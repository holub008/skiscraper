import re
import requests
import urllib2

from configs import Configs
from HTMLParser import HTMLParser
import gopher_state_fetcher
import itiming_fetcher
import mtec_fetcher
from RaceResults import RaceInfo, UnstructuredPDFRaceResults, UnstructuredTextRaceResults

config = Configs()
SKINNYSKI_URL = config.get_as_string("RESULTS_URL")
DB_USER = config.get_as_string("DB_USER")
DB_PASSWORD = config.get_as_string("DB_PASSWORD")
RACE_DB = config.get_as_string("RACE_DB")

######################################
# todo fetcher abstract class
# fetchers may delegate to other fetchers, eg. skinnyski->mtec hosted
#
# todo create a prefetcher to generate RaceInfos, as in birkie_fetcher
######################################


class SkinnySkiRaceInfoParser(HTMLParser):
    """
        a subclass of HTMLParser to override tag/data handlers
    """
    def __init__(self, season, division):
        # since we're overriding the init member function of HTMLParser, need to run superclass's init
        HTMLParser.__init__(self)
        self.elements = []
        self.current_element = RaceInfo.create_empty(season, division)
        self.current_name_starter = ""
        self.season = season
        self.division = division

        # so that we can grab the first data element, the date
        self.first = False
        # url and race name reside in the first anchor.
        self.first_anchor = True

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            # first element in every list is the date
            self.first = True
            self.current_name_starter = ""
        elif tag == 'a' and self.first_anchor:
            self.current_element.url = SkinnySkiRaceInfoParser.extract_href(attrs)
            # leave first_anchor true so that we may extract the race name (contained in the data)

    def handle_endtag(self, tag):
        if tag == 'li':
            self.elements.append(self.current_element)
            self.first_anchor = True
            self.current_element = RaceInfo.create_empty(self.season, self.division)
        elif tag == 'a':
            self.first_anchor = False

    def handle_data(self, data):
        if self.first:
            # handle the date- sometimes the race name isn't entirely contained in the anchor
            # and we must append it later. date is always present, optionally a space follows
            date_str = data.split(" ")[0]
            self.current_element.set_date_from_skinnyski(date_str)
            name_starter_ix = data.find(" ")
            # empty string if no name_starter
            self.current_name_starter = data[name_starter_ix:]

            self.first = False
        elif self.first_anchor:
            # there may have been a component of the name outside the anchor element to reappend
            self.current_element.name = self.current_name_starter + data
            self.first_anchor = False

    @staticmethod
    def extract_href(attrs):
        for attr in attrs:
            if len(attr) == 2:
                if attr[0] == 'href':
                    # handle relative addresses
                    if attr[1].startswith("/"):
                        return "%s%s" % (SKINNYSKI_URL, attr[1])
                    else:
                        return attr[1]
        return "nohrefattr"


class SkinnySkiUnstructuredRaceResultParser(HTMLParser):
    """
    scrape unstructured text results hosted on skinnyski
    ugh, want to use BeautifulSoup but don't want to add the dependency
    """

    def __init__(self):
        HTMLParser.__init__(self)

        self.table_depth = 0
        self.table_count = 0 # count at depth = 0
        self.results = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.table_depth == 0:
                self.table_count += 1
            self.table_depth += 1

    def handle_endtag(self, tag):
        if tag == "table":
            self.table_depth -= 1

    def handle_data(self, data):
        if self.table_count == 2 and self.table_depth == 3:
            self.results.append(data)

    def getTextResults(self):
        return "\n".join(self.results).strip()


def is_pdf(race_info):
    """
    :param race_info: the race metadata to be inspected (RaceInfo)
    :return: if the indicated url is a pdf (bool)
    """
    return race_info.url.rstrip("/").endswith(".pdf")


def is_skinnyski_hosted(race_info):
    """
    :param race_info: the race metadata to be inspected (RaceInfo)
    :return: if the given race is hosted plain text
    """
    ss_re = re.compile(".*skinnyski\.com/racing/display\.asp.*")
    match = ss_re.search(race_info.url)

    return match is not None


def is_mtec_hosted(race_info):
    """
    :param race_info: the race metadata to be inspected (RaceInfo)
    :return: if the given race is hosted plain text
    """
    mt_re = re.compile(".*mtec\.com.*")
    match = mt_re.search(race_info.url)

    return match is not None


def is_itiming_hosted(race_info):
    """
    :param race_info:  the race metadata to be inspected (RaceInfo)
    :return: if the given race is hosted on itiming.com
    """
    it_re = re.compile(".*itiming\.com.*")
    match = it_re.search(race_info.url)

    return match is not None


def is_gopher_state_hosted(race_info):
    """
    :param race_info: the race metadata (RaceInfo)
    :return: if the
    """
    gs_re = re.compile(".*gopherstateevents\.com.*")
    match = gs_re.search(race_info.url)

    # barf, gopher state only makes hs results viewable via post requests, so skinnyski can't link to structured results
    # instead, it links to an unstructured txt doc, which isn't as fun
    # as such, we scrape race infos directly from gopher state and ignore the txt docs linked from skinnyski
    return match is not None and not race_info.url.rstrip("/").endsWith("txt")


def handle_skinnyski_pdf(race_info):
    """
    :param race_info: race metadata (RaceInfo)
    :return: void
    """
    pdf_content = get_skinnyski_content(race_info)
    if pdf_content:
        results = UnstructuredPDFRaceResults(race_info, pdf_content)
        results.serialize()
    else:
        print("Warning: skipping a pdf which was unable to be accessed")


def handle_skinnyski_text(race_info):
    """
    :param race_info: race metadata (RaceInfo)
    :return: void
    """
    raw_html = get_skinnyski_content(race_info)
    if raw_html:
        parser = SkinnySkiUnstructuredRaceResultParser()
        parser.feed(raw_html)

        UnstructuredTextRaceResults(race_info, parser.getTextResults()).serialize()
    else:
        print("Warning: skipping a skinnyski text race which was unable to be accessed")


def get_skinnyski_content(race_info):
    """
    :param race_info: metadata about the race (RaceInfo)
    :return: race results fetched from online. returns None if a problem occurred
    """
    try:
        response = urllib2.urlopen(race_info.url)
    except:
        # todo logging
        print "Error: failed to open resource at %s" % (race_info.url, )
        return None
    if response.getcode() == 200:
        return response.read()
    else:
        return None


def handle_unrecognized(race_info):
    """
        attempt to find result sets on sites where the link is not direct to a doc
    """
    print("TODO nonpdf: %s" % (race_info.url,))
    pass


def process_race(race_info, race_store):
    """
    factory to determine how to handle this race and process accordingly
    :param race_info: race metadata (RaceInfo)
    :param race_store: existing races in the race db (RaceResultStore)
    :return: void
    """
    if race_info.url:
        if is_pdf(race_info):
            handle_skinnyski_pdf(race_info)
        elif is_skinnyski_hosted(race_info):
            handle_skinnyski_text(race_info)
        elif is_mtec_hosted(race_info):
            mtec_fetcher.process_race(race_info, race_store)
        elif is_itiming_hosted(race_info):
            itiming_fetcher.process_race_from_landing(race_info, race_store)
        elif is_gopher_state_hosted(race_info):
            gopher_state_fetcher.process_race(race_info, race_store)
        else:
            handle_unrecognized(race_info)

    else:
        # todo logging
        print "Error: URL is not present"


def get_race_infos(season, division):
    """
        get the list of URLs to results for the year
    """
    url = "%s/racing/results/default.asp" % (SKINNYSKI_URL, )
    r = requests.post(url, data={"season": season, "cat": division})

    # hacky and at the mercy of skinnyski page design changes... nm we're okay :)
    if r.status_code == 200:
        # simplify the parser's work by cutting down the html to a a bunch of lists
        link_list = r.text[r.text.index("<ul>") + 4:r.text.index("</ul>")]

        parser = SkinnySkiRaceInfoParser(season, division)
        try:
            parser.feed(link_list)
        except Exception as e:
            # TODO logging
            print("Failed to parse HTML- may be invalid: ")
            print(e)
            return []

        return parser.elements
    else:
        # TODO logging
        print("Error: failed to connect to skinnyski: %s" % r.reason)
        return []

if __name__ == "__main__":
    info = RaceInfo("2016", "103", "2016-01-07", "http://www.skinnyski.com/racing/display.asp?Id=35835", "Elm Creek Series Test")
    handle_skinnyski_text(info)
