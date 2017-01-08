from HTMLParser import HTMLParser
import json
import re
import urllib2

from RaceResults import RaceInfo, RaceResult, StructuredRaceResults

CHRONOTRACK_BASE_RESULTS_URL = "https://results.chronotrack.com/embed/results"
CHRONOTRACK_AJAX_EVENT_URL = CHRONOTRACK_BASE_RESULTS_URL + "/load-model?modelID=event&eventID=%s" # expects eventID
CHRONOTRACK_AJAX_RESULTS_URL = CHRONOTRACK_BASE_RESULTS_URL + "/results-grid?\
iDisplayStart=0&iDisplayLength=10000&raceID=%s&eventID=%s" # expects raceID & eventID

REQUESTED_WITH_HEADER = "XMLHttpRequest"

# expected column indices for chronotrack individual results
CHRONOTRACK_PLACE_INDEX = 1
CHRONOTRACK_NAME_INDEX = 2
CHRONOTRACK_TIME_INDEX = 4

class ITimingHTMLParser(HTMLParser):
    """
    parse the itiming landing page to find the relevant link to the results table
    """

    def __init__(self):
        HTMLParser.__init__(self)

        self.in_anchor = False
        self.event_url = None
        self.current_href = None

    def handle_starttag(self, tag, attrs):
        # yeesh. why not capitalize your html elements?!
        if tag.lower() == "a":
            self.in_anchor = True
            self.current_href = ITimingHTMLParser.extract_attr(attrs, "href")

    def handle_data(self, data):
        # not sure how consistent this magic string is- may need to do "rough" comparison
        if self.in_anchor and "searchable" in data.lower():
            self.event_url = self.current_href
        # todo printable -> unstructured results
        # ex http://www.itiming.com/html/raceresults.php?year=2016&EventId=1324&eventype=0

    def handle_endtag(self, tag):
        if tag.lower() == "a":
            self.in_anchor = False

    def get_event_url(self):
        return self.event_url

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None


def prepare_chronotrack_result_json(text):
    """
    :param text: string from /load-model that contains embedded json - assumed the callback function is an empty string
    :return: the embedded json (str)
    """
    return text.lstrip("(").rstrip(");")


def get_event_id_from_url(event_url):
    """
    :param event_url: chronotrack url (str)
    :return: event id contained in url, None if not present (int)
    """
    event_regex = re.compile("event-([0-9]+)")
    match = event_regex.search(event_url)
    if match:
        return match.group(1)
    else:
        return None


def get_races_for_event(event_url):
    """
    :param race_info: a race info object representing an event (RaceInfo)
    :param event_url: a chronotrack url for the event (str)
    :return: the race ids under this event with corresponding race names (Generator<Tuple<int, str>>)
    todo wrap the return in some more reasonable object
    """
    request = urllib2.Request(event_url, headers={"X-Requested-With" : REQUESTED_WITH_HEADER})
    response = urllib2.urlopen(request)

    if response.getcode() == 200:
        json_blob = prepare_chronotrack_result_json(response.read())
        try:
            data_map = json.loads(json_blob)
            race_list = data_map["model"]["races"]

            race_id_regex = re.compile("[0-9]+")
            for element in race_list.keys():
                match = race_id_regex.search(element)
                if match:
                    yield (match.group(0), race_list[element]["name"])
        except Exception as e:
            # todo logging
            print("Chronotrack json parse problems / unexpected structure: " + str(e))
    else:
        # todo logging
        print("Unexpected response code from Chronotrack event url: " + event_url)


def process_chronotrack_race(race_info):
    """
    after generating a list of chronotrack races from the event page, ingest the race
    :param race_info:
    :return:
    """
    request = urllib2.Request(race_info.url, headers={"X-Requested-With" : REQUESTED_WITH_HEADER})
    response = urllib2.urlopen(request)

    if response.getcode() == 200:
        try:
            data_map = json.loads(prepare_chronotrack_result_json(response.read()))

            race_results = []
            for row in data_map["aaData"]:
                race_results.append(RaceResult(row[CHRONOTRACK_NAME_INDEX], row[CHRONOTRACK_TIME_INDEX], row[CHRONOTRACK_PLACE_INDEX]))

            StructuredRaceResults(race_info, race_results).serialize()
        except Exception as e:
            # todo logging
            print("Chronotrack individual result json parse problems / unexpected structure: " + str(e))
    else:
        # todo logging
        print("Unexpected response (%d) in getting individual results from chronotrack url: %s" % (response.getcode(), race_info.url))


def process_events(event_race_info, event_url, race_store):
    """
    process results on the itiming site. this method may spawn the creation of new race_info types.
    :param event_race_info: race metadata (RaceInfo)
    :param event_url: url for the chronotrack event
    :param race_store: store of all currently processed races (RaceResultStore)
    :return: void
    """
    event_id = get_event_id_from_url(event_url)
    if event_id:
        chronotrack_event_url = CHRONOTRACK_AJAX_EVENT_URL % (event_id, )

        race_count = 0
        for race_pair in get_races_for_event(chronotrack_event_url):
            race_count += 1
            chronotrack_race_url = CHRONOTRACK_AJAX_RESULTS_URL % (race_pair[0], event_id)
            race_name = "%s - %s" % (event_race_info.name, race_pair[1], )
            race_info = RaceInfo(event_race_info.season, event_race_info.division, event_race_info.date, chronotrack_race_url, race_name)

            if race_info in race_store:
                # todo logging
                print "Skipping the processing of itiming race (%s) because it was already processed." %(race_info)
            else:
                process_chronotrack_race(race_info)

        if race_count < 1:
            # todo logging
            print("Warning: failed to find any races for itiming/chronotrack url: " + event_url)
    else:
        # todo logging
        print("Failed to get id from itiming url: " + event_url)
        return


def process_race_from_landing(race_info, race_store):
    """
    process results on the itiming site, starting potentially from the landing page in race_info.url
    :param race_info: race metadata (RaceInfo)
    :param race_store: store of all currently processed races (RaceResultStore)
    :return: void
    """

    response = urllib2.urlopen(race_info.url)
    if not response.getcode() == 200:
        # todo logging
        print("Did not receive the expected response from itiming url: " + race_info.url)
        return

    parser = ITimingHTMLParser()
    parser.feed(response.read())

    event_url = parser.get_event_url()
    if event_url:
        process_events(race_info, event_url, race_store)
    else:
        # todo logging
        print("Failed to find results page for itiming url: " + race_info.url)

if __name__ == "__main__":
    r = RaceInfo("2015", "101", "2016-01-01", "http://www.itiming.com/html/raceresults.php?year=2016&EventId=1322&eventype=0", "Pre-birkie")
    process_race_from_landing(r)