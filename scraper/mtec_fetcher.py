from abc import ABCMeta, abstractmethod
from HTMLParser import HTMLParser
import re
import urllib2

from RaceResults import RaceInfo, RaceResult, StructuredRaceResults, UnstructuredTextRaceResults

TEXT_RESULT_DIV_CLASS = "racetextresults"

MTEC_BASE_URL = "http://www.mtecresults.com"
MTEC_AJAX_URL =  MTEC_BASE_URL + "/race/quickResults?raceid=%s&version=63&overall=yes&offset=0&perPage=10000" # expects the race id
REFERER_HEADER_FORMAT = MTEC_BASE_URL + "/race/show/%s'" # expects the race id
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
        self.current_name = u""
        self.current_url = ""

    def _generate_race_info(self):
        return RaceInfo(self.event_race_info.season, self.event_race_info.division, self.event_race_info.date, self.current_url, u"{}, {}".format(self.event_race_info.name, self.current_name))

    def handle_starttag(self, tag, attrs):
        if tag == "div" and SubdivisionParser.extract_attr(attrs, "class") == TEXT_RESULT_DIV_CLASS:
            self.results_are_structured = False
        elif tag == "select" and SubdivisionParser.extract_attr(attrs, "id") == "otherracesselect":
            self.in_other_race_select = True
        elif tag == "option" and self.in_other_race_select:
            # todo if we have structured results, we need to handle this differently. these links just take you to another top level page
            # we need to parse out ids or do some post-processing in get_race_infos
            # in any event, the url should look like: http://www.mtecresults.com/race/quickResults?raceid=2866&version=1&overall=yes&offset=0&perPage=10000
            self.in_race_option = True

            relative_path = self.extract_attr(attrs, "value")
            if relative_path:
                self.current_url = MTEC_BASE_URL + relative_path
            else:
                # todo logging & this will yield a shiesty raceinfo
                print "Skipping mtec subdivision race due to no supplied url"

    def handle_data(self, data):
        if self.in_race_option:
            self.current_name = data.decode('utf-8')

    def handle_endtag(self, tag):
        if tag == "select":
            self.in_other_race_select = False
        elif tag == "option" and self.in_race_option:
            self.race_infos.append(self._generate_race_info())
            self.in_race_option = False

    # todo filter out garbage / repeated races
    def get_race_infos(self):
        return self.race_infos

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None


class ResultParser:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_race_results(self):
        """
        :return: get the parsed race results (RaceResults)
        """


class StructuredResultParser(HTMLParser, ResultParser):
    """
    Parser for the case where we have a good race result summary
    except it's not good because mtec does not see fit to close all it's <tr> tags...
    """

    def __init__(self, ri):
        HTMLParser.__init__(self)
        self.race_info = ri

        self.race_results = []
        self.current_data = [] # for handling multiline data...
        self.current_race_result = RaceResult("", "", "")

        self.in_thead = False
        self.first_tr = True
        self.td_count = 0


    def handle_starttag(self, tag, attrs):
        if tag == "thead":
            self.in_thead = True
        elif tag == "tr" and not self.in_thead:
            self.in_tr = True
            # since we have no closing tr tags, we must assume that a newly opened one indicates a prior closure
            if self.first_tr:
                self.first_tr = False
            else:
                self.race_results.append(self.current_race_result)
                self.current_race_result = RaceResult("", "", "")

                self.td_count = 0
        elif tag == "td":
            self.td_count += 1

    def handle_data(self, data):
        self.current_data.append(data.strip())

    def handle_endtag(self, tag):
        """
        note that there are no useful closing tr tags in this data
        """
        if tag == "thead":
            self.in_thead = False
        elif tag == "td":
            if self.td_count == 2:
                self.current_race_result.name = self._get_current_data()
            elif self.td_count == 7:
                self.current_race_result.place = self._get_current_data()
            elif self.td_count == 10:
                self.current_race_result.time = self._get_current_data()
            self.current_data = []

    def _get_current_data(self):
        return "".join(self.current_data)

    def get_race_results(self):
        return StructuredRaceResults(self.race_info, self.race_results)


class UnstructuredResultParser(HTMLParser, ResultParser):
    """
    unfortunately, some results are in plain text, and I don't believe I can depend on consistent
    headers across all mtex races (todo study this)
    """

    def __init__(self, ri):
        HTMLParser.__init__(self)
        self.race_info = ri

        # list for handling multiple
        self.results = []

        self.in_result_div = False

    def handle_starttag(self, tag, attrs):
        if tag == "div" and UnstructuredResultParser.extract_attr(attrs, "class") == TEXT_RESULT_DIV_CLASS:
            self.in_result_div = True

    def handle_data(self, data):
        if self.in_result_div:
            self.results.append(data)

    def handle_endtag(self, tag):
        if tag == "div":
            self.in_result_div = False

    def get_race_results(self):
        return UnstructuredTextRaceResults(self.race_info, "\n".join(self.results))

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None

def _get_id_from_url(url):
    """
    :param url: the race url to be parsed
    :return: mtec id of the requested race (str, none if not present)
    """
    KEY = "race/show/"
    key_regex = re.compile(KEY + "[0-9]+")
    match = key_regex.search(url)
    if match:
        return match.group(0).lstrip(KEY)
    return None


def process_race(race_info, race_store):
    """
    process results on the mtec site. this method may spawn the creation of new race_info types.
    :param race_info: race metadata (RaceInfo)
    :param race_store: collection of races existing in the race db
    :return: void
    """

    response = urllib2.urlopen(race_info.url)
    if not response.getcode() == 200:
        print("Unexpected response code from url (%s): %d. Unable to fetch mtec results." % (race_info.url, response.status_code))
        return

    event_parser = SubdivisionParser(race_info)
    event_parser.feed(response.read())

    for sub_race_info in event_parser.get_race_infos():
        if sub_race_info in race_store:
            # todo logging
            print "Skipping the processing of mtec race (%s) because it already exists in the race store" % (sub_race_info,)
            continue

        event_id = _get_id_from_url(sub_race_info.url)
        if event_id:
            # todo I don't like "scoping" response and parser like this,
            if event_parser.results_are_structured:
                request_headers = {"Referrer" : REFERER_HEADER_FORMAT % (event_id, ),
                                   "X-Requested-With" : REQUESTED_WITH_HEADER}
                response = urllib2.urlopen(urllib2.Request(MTEC_AJAX_URL % (event_id, ), headers=request_headers))
                race_parser = StructuredResultParser(sub_race_info)
            else:
                response = urllib2.urlopen(sub_race_info.url)
                race_parser = UnstructuredResultParser(sub_race_info)

            if not response.getcode() == 200:
                print "Failed to fetch results at url %s" % (race_info.url, )
                continue

            race_parser.feed(response.read())
            race_parser.get_race_results().serialize()

        else:
            # todo logging
            print "Skipping mtec url due to no id: " + sub_race_info.url

if __name__ == "__main__":
    r = RaceInfo("2015", "101", "2015-01-01","http://www.mtecresults.com/race/show/3824/2016_City_of_Lakes_Loppet_Festival-Columbia_Sportswear_Skate","COLL")
    process_race(r)
    r = RaceInfo("2011", "101","2011-01-01", "http://www.mtecresults.com/race/show/250/2011_Mora_Vasaloppet-58K_Freestyle", "Mora Vasaloppet")
    process_race(r)