"""
for results hosted on gopherstateevents.com
some citizen races are hosted here, but primarily high school races from 2015 on
we can get structured results here :)
"""

from HTMLParser import HTMLParser
import re
import urllib2

from configs import Configs
from RaceResults import RaceInfo, RaceResult, StructuredRaceResults
import RaceResultStore

config = Configs()
DEFAULT_CITIZEN_POST_DATA = {"gender":"b", "submit_race":"submit_race", "get_race":"view"}
DEFAULT_HS_POST_DATA = {"submit_meet":"submit_meet", "get_meet":"View+This+Meet"}

HS_RACE_INFO_PAGE = "http://www.gopherstateevents.com/results/cc_rslts/cc_rslts.asp?sport=nordic"


class GopherStateEventInfoParser(HTMLParser):
    """
    parse the event landing page to get race infos
    """
    def __init__(self):
        HTMLParser.__init__(self)

        self.race_name_ids = []


    def get_race_names_ids(self):
        """
        :return: race id / race name tuples associated with this event
        """
        return self.race_name_ids


class GopherStateHSRaceInfoParser(HTMLParser):
    """
    high school results are only obtained through post requests, so skinnyski doesn't link to them
    we are forced to scrape direct from site to get structured results :(
    skinnyski only links to unstructured txt results
    """
    def __init__(self):
        HTMLParser.__init__(self)

        # capture groups 1. name 2. date
        self.content_re = re.compile("(.+).*(\([0-9/]+/\))")
        self.division = config.get_as_string("HS_DIVISION")
        self.date_format = "%m/%d/%Y"

        self.in_meet_list = False
        self.in_meet_option = False

        self.race_infos = []
        self.post_ids = []


    def handle_starttag(self, tag, attrs):
        if tag == "select" and self.extract_attr(attrs, "id") == "meets":
            self.in_meet_list = True
        elif self.in_meet_list and tag == "option":
            self.in_meet_option = True
            self.post_ids.append(self.extract_attr(attrs, "id"))

    def handle_endtag(self, tag):
        if tag == "select":
            self.in_meet_list = False

    def handle_data(self, data):
        if self.in_meet_option:
            match = self.content_re.search(data)
            if match:
                race_name = match.group(1)
                race_date = match.group(2)

                race_info = RaceInfo(None, self.division, race_date, HS_RACE_INFO_PAGE, race_name)
                race_info.set_season_from_date(self.date_format)

    def get_race_infos(self):
        """
        :return: high school race infos that we found (List<RaceInfo>)
        """
        return self.race_infos

    def get_post_ids(self):
        """
        todo loose coupling
        :return: ids associated with the parsed race_infos (List<Integer>)
        """
        return self.post_ids

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr in attrs:
            if len(attr) == 2:
                if attr[0] == attr_name:
                    return attr[1]
        return None


class GopherStateHSResultParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

        self.race_infos = []

    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass

    def get_race_infos(self):
        return self.race_infos

class GopherStateRaceResultParser(HTMLParser):
    """
    citizen and hs races have different columns/formats
    todo this class should be wise to that, or split into separate class
    """
    def __init__(self):
        HTMLParser.__init__(self)

        self.race_results = []

    def get_race_results(self):
        """
        :return: structured race results that were parsed out (List<RaceResult>)
        """
        return self.race_results

def get_gopher_state_content(url, post_data={}):
    try:
        # have to check, since if data= is specified, post request will be used
        if not post_data:
            response = urllib2.urlopen(url)
        else:
            response = urllib2.urlopen(url, data=post_data)
    except:
        # todo logging
        print "Error: failed to open resource at %s" % (url, )
        return None

    if response.getcode() == 200:
        return response.read()
    else:
        return None


def process_race(event_info, race_store):
    """
    this is for citizen races!
    :param event_info: the event to fetch - should have subraces (RaceInfo)
    :param race_store: all current races (RaceResultStore)
    :return: void
    """

    event_parser = GopherStateEventInfoParser(event_info)
    event_content = get_gopher_state_content(event_info.url)

    if not event_content:
        print("Warning: skipping fetch for gopher state event: %s" % (event_info))
        return

    event_parser.feed(event_content)
    for race_names_ids in event_parser.get_race_post_ids():
        if event_info in race_store:
            print("Skipping race gopher state race already stored: %s" % (event_info,))
        else:
            race_name = race_names_ids[0]
            post_id = race_names_ids[1]
            race_info = RaceInfo(event_info.season, event_info.division, event_info.date, event_info.url, race_name)

            post_data = DEFAULT_CITIZEN_POST_DATA.copy()
            post_data["races"] = post_id
            race_content = get_gopher_state_content(race_info.url, post_data=post_data)
            if not race_content:
                print("Warning: skipped gopher state race due to post problems: %s" % (race_info,))
            else:
                parser = GopherStateRaceResultParser()
                parser.feed(race_content)

                StructuredRaceResults(race_info, parser.get_race_results()).serialize()

def process_hs_event(event_info, meet_id, race_store):
    """
    this is for hs races! yeah for dupicated logic!
    :param event_info:
    :param race_store:
    :return:
    """

    # todo probably need a new one of these guys too :(
    event_parser = GopherStateEventInfoParser(event_info)
    post_data = DEFAULT_HS_POST_DATA.copy()
    post_data["meets"] = meet_id
    event_content = get_gopher_state_content(event_info.url, post_data=post_data)

    if not event_content:
        print("Warning: skipping fetch for gopher state hs event: %s" % (event_info))
        return
    for race_info in event_parser.get_race_names_ids():
        race_parser = GopherStateHSResultParser()


def fetch_hs_races(race_store):
    """
    :param race_store: a store of races we currently have
    :return: void
    """
    parser = GopherStateHSRaceInfoParser()

    content = get_gopher_state_content(HS_RACE_INFO_PAGE)
    if not content:
        print("Warning: skipping fetch for all gopher state highschool events!")
        return

    parser.feed(content)
    for ix, event_info in enumerate(parser.get_race_infos()):
        process_hs_event(event_info, parser.get_post_ids()[ix])


    
if __name__ == "__main__":
    race_store = RaceResultStore.RaceResultStore()
    event_info = RaceInfo("2016", "103", "2016-01-30", "http://www.gopherstateevents.com/results/fitness_events/results.asp?event_type=46&event_id=530", "Big Island and back test")
    process_race(event_info, race_store)

    # for hs
    # event_info = RaceInfo("2016", "103", "2016-01-30", "http://www.gopherstateevents.com/results/fitness_events/results.asp?event_type=46&event_id=530", "Big Island and back test")
    # process_race(event_info, race_store)