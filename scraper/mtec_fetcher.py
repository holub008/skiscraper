from abc import ABCMeta, abstractmethod
import HTMLParser
import urllib2

from RaceResults import RaceInfo, StructuredRaceResults, UnstructuredRaceResults

MTEC_BASE_URL = "http://www.mtecresults.com/"
REFERER_HEADER_FORMAT = MTEC_BASE_URL + "race/show/%s'" # expects the race id
REQUESTED_WITH_HEADER = "XMLHttpRequest"


class SubdivisionParser(HTMLParser):
    """
    find the all the races for the event (race_info is a bit of a misnomer I guess)
    """

    def __init__(self, race_info):
        HTMLParser.__init__(self)

        self.event_race_info = race_info

        # since unstructured content include a race on the event landing page, we need to include the landing page :O
        self.race_infos = [race_info]
        self.results_are_structured = True

        self.in_other_race_select = False
        self.in_race_option = False
        self.current_name = ""
        self.current_url = ""

    def _generate_race_info(self):
        return RaceInfo(self.event_race_info.season, self.event_race_info.date, self.current_url, "%s, %s" % (self.event_race_info.name, self.current_name))

    def handle_starttag(self, tag, attrs):
        if tag == "div" and SubdivisionParser.extract_attr(attrs, "class") == "racetextresults":
            self.results_are_structured = False
        elif tag == "select" and SubdivisionParser.extract_attr(attrs, "id") == "otherracesselect":
            self.in_other_race_select = True
        elif tag == "option" and self.in_other_race_select:

            # todo if we have structured results, we need to handle this differently. these links just take you to another top level page
            # we need to parse out ids or do some post-processing in get_race_infos
            # in any event, the url should look like: http://www.mtecresults.com/race/quickResults?raceid=2866&version=1&overall=yes&offset=0&perPage=10000
            self.in_race_option = True
            self.current_url = MTEC_BASE_URL + self.extract_attr(attrs, "href")

    def handle_data(self, data):
        if self.in_race_option:
            self.current_name = data

    def handle_endtag(self, tag):
        if tag == "select":
            self.in_other_race_select = False
        elif tag == "option" and self.in_race_option:
            self.race_infos.append(self._generate_race_info())
            self.in_race_option = False

    def get_result_infos(self):
        if self.results_are_structured:
            # unstructured results always include a result page on the parent event :O
            return self.race_infos[1:]
        else:
            return self.race_infos

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None


class StructuredResultParser(HTMLParser):
    """
    Parser for the case where we have a good race result summary
    """

    def __init__(self, ri):
        HTMLParser.__init__(self)
        self.race_info = ri

    def handle_starttag(self, tag, attrs):
        pass

    def handle_data(self, data):
        pass

    def handle_endtag(self, tag):
        pass


class UnstructuredResultParser(HTMLParser):
    """
    unfortunately, some results are in plain text, and I don't believe I can depend on consistent
    headers across all mtex races (todo study this)
    """

    def __init__(self, ri):
        HTMLParser.__init__(self)
        self.race_info = ri

    def handle_starttag(self, tag, attrs):
        pass

    def handle_data(self, data):
        pass

    def handle_endtag(self, tag):
        pass

def process_race(race_info):
    """
    process results on the mtec site. this method may spawn the creation of new race_info types.
    :param race_info: race metadata (RaceInfo)
    :return: void
    """

    response = urllib2.urlopen(race_info.url)
    if not response.status.code == 200:
        print("Unexpected response code from url (%s): %d. Unable to fetch mtec results." % (race_info.url, response.status_code))
        return

    event_parser = SubdivisionParser()
    event_parser.feed(response.text)

    event_id = race_info.url[race_info.url.last.find("/"):]
    for sub_race_info in event_parser.get_race_infos():

        # todo I don't like "scoping" response and parser like this,
        if event_parser.results_are_structured:
            request_headers = {"Referrer" : REFERER_HEADER_FORMAT % (event_id, ),
                               "X-Requested-With" : REQUESTED_WITH_HEADER}
            response = urllib2.urlopen(race_info.url, headers = request_headers)
            race_parser = StructuredResultParser(sub_race_info)
        else:
            response = urllib2.urlopen(race_info.url)
            race_parser = UnstructuredResultParser(sub_race_info)

        if not response.status_code == 200:
            print "Failed to fetch unstructured results at url %s" % (race_info.url, )
            continue

        race_parser.feed(response.text)
        for race_result in race_parser.race_results:
            race_result.serialize()