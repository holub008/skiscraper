from HTMLParser import HTMLParser
import json
import re
import urllib2

from RaceResults import RaceInfo

CHRONOTRACK_BASE_RESULTS_URL = "https://results.chronotrack.com/embed/results"
CHRONOTRACK_AJAX_EVENT_URL = CHRONOTRACK_BASE_RESULTS_URL + "/load-model?modelID=event&eventID=%s" # expects eventID
CHRONOTRACK_AJAX_RESULTS_URL = CHRONOTRACK_BASE_RESULTS_URL + "/results-grid?\
iDisplayStart=0&iDisplayLength=10000&raceID=%s&eventID=%s" # expects raceID & eventID

REQUESTED_WITH_HEADER = "XMLHttpRequest"
EVENT_REFERER_HEADER = CHRONOTRACK_BASE_RESULTS_URL + "/event/event-%s" # expects eventID

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
        if self.in_anchor and data == "Searchable Results with Leaderboard":
            self.event_url = self.current_href

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

def process_race_from_landing(race_info):
    """
    process results on the itiming site, starting potentially from the landing page in race_info.url
    :param race_info: race metadata (RaceInfo)
    :return: void
    """

    response = urllib2.urlopen(race_info.url)
    if not response.getcode() == 200:
        # todo logging
        print("Did not receive the expected response from itiming url: " + race_info.url)
        return

    parser = ITimingHTMLParser()
    parser.feed(response.read())

    event_url  = parser.get_event_url()
    if event_url:
        process_race(race_info, event_url)
    else:
        # todo logging
        print("Failed to find results page for itiming url: " + race_info.url)


def prepare_chronotrack_result_json(text):
    """
    :param text: string from /load-model that contains embedded json - assumed the callback function is an empty string
    :return: the embedded json (str)
    """
    return text.lstrip("(").rstrip(");")


# curl 'https://results.chronotrack.com/embed/results/load-model?modelID=event&eventID=17250' -H 'Referer: https://results.chronotrack.com/event/results/event/event-17250' -H 'X-Requested-With: XMLHttpRequest'
def get_races_for_event(event_url):
    """
    :param race_info: a race info object representing an event (RaceInfo)
    :param event_url: a chronotrack url for the event (str)
    :return: the race ids under this event with corresponding race names (Generator<Tuple<int, str>>)
    todo wrap the return in some more reasonable object
    """
    request = urllib2.Request(event_url, headers={"X-Requested-With" : REQUESTED_WITH_HEADER, "Referer" : EVENT_REFERER_HEADER})
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


def get_event_id_from_url(event_url):
    """
    :param event_url: chronotrack url (str)
    :return: event id contained in url, None if not present (int)
    """
    EVENT_KEY = "event-"
    event_regex = re.compile(EVENT_KEY + "[0-9]+")
    match = event_regex.search(event_url)
    if match:
        return match.group(0).lstrip(EVENT_KEY)
    else:
        return None


def process_race(event_race_info, event_url):
    """
    process results on the itiming site. this method may spawn the creation of new race_info types.
    :param event_race_info: race metadata (RaceInfo)
    :param event_url: url for the chronotrack event
    :return: void
    """
    event_id = get_event_id_from_url(event_url)
    if event_id:
        chronotrack_event_url = CHRONOTRACK_AJAX_EVENT_URL % (event_id, )

        race_infos = []
        for race_pair in get_races_for_event(chronotrack_event_url):
            chronotrack_race_url = CHRONOTRACK_AJAX_RESULTS_URL % (event_id, race_pair[0])
            race_name = "%s - %s" % (event_race_info.name, race_pair[1], )
            race_info = RaceInfo(event_race_info.season, event_race_info.date, chronotrack_event_url, race_name)
            race_infos.append(race_info)

        print race_infos
    else:
        # todo logging
        print("Failed to get id from itiming url: " + event_url)
        return

# investigation:
# starting from http://www.itiming.com/html/raceresults.php?year=2016&EventId=1322&eventype=0
# follow searchable results
# curl 'https://results.chronotrack.com/embed/results/results-grid?iColumns=11&sColumns=&iDisplayStart=0&iDisplayLength=10000&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8&mDataProp_9=9&mDataProp_10=10&raceID=41116&bracketID=435632&intervalID=82716&eventID=17250'  -H 'Referer: https://results.chronotrack.com/event/results/event/event-17250' -H 'X-Requested-With: XMLHttpRequest'
# results in js with an embedded json string of results

if __name__ == "__main__":
    r = RaceInfo("2015","2016-01-01", "http://www.itiming.com/html/raceresults.php?year=2016&EventId=1322&eventype=0", "Pre-birkie")
    process_race_from_landing(r)