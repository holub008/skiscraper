import requests
from HTMLParser import HTMLParser
import mysql.connector
import urllib2

from configs import Configs
import pdf_serializer
from RaceResults import RaceResult, StructuredRaceResults, RaceInfo, UnstructuredRaceResults

config = Configs()
DB_USER = config.get_as_string("DB_USER")
DB_PASSWORD = config.get_as_string("DB_PASSWORD")

# division ids for forming the url correspond to list index
RACES = ["51K Skate","55K Classic","24K Skate","24K Classic"]
# bunch of boilerplate, only variable params are page # (100 per page), year, and divId
BASE_URL_FORMAT_2014ON = "http://birkie.pttiming.com/results/%d/index.php?page=1150&r_page=division&pageNum_rsOverall=%d&divID=%d"
URL_PREFETCH_2007ON = "http://results.birkie.com"
# yikes! this will spit raw sql errors if you supply malformed queries
BASE_URL_FORMAT_2007ON = "http://results.birkie.com/index.php?event_id=%s&page_number=%s"
URL_PREFETCH_PRE2007 = "http://www.birkie.com/ski/events/birkie/results/"

# todo this is dynamic
BIRKIE_RACE_NAME = "American Birkebeiner"

class Birkie2014Parser(HTMLParser):
    """
    a custom parser for results on birkie.pttiming.com
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_data_row = False
        self.current_race_result = RaceResult("","","")
        self.current_td_data = []
        self.td_count = 0
        self.race_results = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr" and self.extract_class(attrs) == "dataRow":
            self.td_count = 0
            self.in_data_row = True
            self.current_race_result = RaceResult("","","")
        elif tag == "td" and self.in_data_row:
            self.td_count += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_data_row:
            self.race_results.append(self.current_race_result)
            self.in_data_row = False
        elif tag == "td" and self.in_data_row:
            # todo, ascii re-encoding is lossy and a hack for easy writing to mysql
            # todo sql sanitization does not belong here
            clean_data = " ".join([x.strip().replace("'", "") for x in self.current_td_data]).encode("ascii", "ignore")
            if self.td_count == 1:
                self.current_race_result.place = clean_data
            elif self.td_count == 5:
                self.current_race_result.name = clean_data
            elif self.td_count == 7:
                self.current_race_result.time = clean_data
            self.current_td_data = []

    # html parser is disgusting and gives the data not as an entire string
    def handle_data(self, data):
        if self.in_data_row:
            self.current_td_data.append(data)

    @staticmethod
    def extract_class(attrs):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == "class":
                    return attr_pair[1]
        return None

class Birkie2007OnParser(HTMLParser):
    """
    a custom parser for results on results.birkie.com
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_data_row = False
        self.current_race_result = RaceResult("","","")
        self.current_td_data = []
        self.td_count = 0
        self.race_results = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr" and self.extract_class(attrs) == "dataRow":
            self.td_count = 0
            self.in_data_row = True
            self.current_race_result = RaceResult("","","")
        elif tag == "td" and self.in_data_row:
            self.td_count += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_data_row:
            self.race_results.append(self.current_race_result)
            self.in_data_row = False
        elif tag == "td" and self.in_data_row:
            # todo, ascii re-encoding is lossy and a hack for easy writing to mysql
            # todo sql sanitization does not belong here
            clean_data = " ".join([x.strip().replace("'", "") for x in self.current_td_data]).encode("ascii", "ignore")
            if self.td_count == 1:
                self.current_race_result.place = clean_data
            elif self.td_count == 5:
                self.current_race_result.name = clean_data
            elif self.td_count == 7:
                self.current_race_result.time = clean_data
            self.current_td_data = []

    # html parser is disgusting and gives the data not as an entire string
    def handle_data(self, data):
        if self.in_data_row:
            self.current_td_data.append(data)

    @staticmethod
    def extract_class(attrs):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == "class":
                    return attr_pair[1]
        return None


class Birkie2007To2014Prefetcher(HTMLParser):
    def __init__(self, season):
        """
        :param season: the season the birkie took place, one less than the year of the race you probably want (str)
        """
        HTMLParser.__init__(self)

        self.year = str(int(season) + 1)
        # todo parity between ids and names
        self.event_ids = []
        self.event_names = []
        self.current_id = -1
        self.in_option = False
        self.in_race_select = False

    def handle_starttag(self, tag, attrs):
        if self.in_race_select and tag == "option":
            self.in_option = True
            self.current_id = self.extract_attr(attrs, "value")
        elif tag == "select" and self.extract_attr(attrs, "id") == "divid":
            self.in_race_select = True

    def handle_data(self, data):
        # quick hack, check if the season is a substring of the race name
        if self.in_option and self.year in data:
            self.event_ids.append(self.current_id)
            self.event_names.append(data)

    def handle_endtag(self, tag):
        if self.in_race_select and tag == "select":
            self.in_race_select = False
        if tag == "option":
            self.in_option = False
            self.current_id = -1

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None

class BirkiePre2007Prefetcher(HTMLParser):
    def __init__(self, season):
        """
        :param season: the season the birkie took place, one less than the year of the race your probably want (str)
        """
        HTMLParser.__init__(self)

        self.year = str(int(season) + 1)
        self.race_urls = []
        self.race_names = []

        self.current_header = ""

        self.in_results_div = False
        self.in_results_header = False
        self.in_result_list_element = False
        self.in_anchor = False
        self.current_result_kept = False
        self.current_race_name_parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "div" and self.extract_attr(attrs, "class") == "col-xs-12 col-md-6":
            self.in_results_div = True
        elif self.in_results_div and tag == "h3":
            self.in_results_header = True
        elif self.in_results_div and tag == "li" and self.year in self.current_header:
            self.in_result_list_element = True
        elif self.in_result_list_element and tag == "a":
            self.in_anchor = True
            url = self.extract_attr(attrs, "href")

            if self.is_pdf_link(url) and self.is_non_duped_result(url):
                self.race_urls.append(url)
                self.current_result_kept = True
            else:
                self.current_result_kept = False

    def handle_data(self, data):
        if self.in_results_header:
            self.current_header = data
        elif self.in_anchor and self.current_result_kept:
            self.current_race_name_parts += data.split()

    def handle_endtag(self, tag):
        if self.in_results_div and tag == "div":
            self.in_results_div = False
        elif self.in_results_header and tag == "h3":
            self.in_results_header = False
        elif self.in_result_list_element and tag == "li":
            self.in_result_list_element = False
        elif self.in_anchor and tag == "a":
            self.in_anchor = False

            if self.current_result_kept:
                self.race_names.append(self.current_header + " " + " ".join(self.current_race_name_parts))
                self.current_race_name_parts = []

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None

    @staticmethod
    def is_pdf_link(href):
        # todo it's too late for doing this right...
        return href.endswith(".pdf")

    @staticmethod
    def is_non_duped_result(href):
        # sometimes two pdfs contain more or less the same results
        # simple heuristic: these are always age group awards :)
        # todo this requires more tuning!
        return "age" not in href.lower()

def handle2014On(season):
    """

    :param season: the season of the race we want. note Birkies are in Feb, so they are a year ahead (str)
    :return: void
    """
    year = int(season) + 1

    for div_ix, div in enumerate(RACES):
        total_results = []
        page = 0
        # page size defaults to 100, if smaller, we've reached the end
        current_page_size = 100
        while current_page_size == 100:
            # todo a bit inefficient
            parser = Birkie2014Parser()

            # indexed from 1
            div_id = div_ix + 1
            url = BASE_URL_FORMAT_2014ON % (year, page, div_id)
            try:
                response = requests.get(url)
            except Exception as e:
                print("failed to fetch Birkie results at url (%s) with error: %s" % (url, str(e)))
                continue

            table = ""
            if response.status_code == 200:
                table = response.text[response.text.index("Overall Event Results"):]
                parser.feed(table)
                current_page_size = len(parser.race_results)
                total_results += parser.race_results
            else:
                print("Bad response code (%d) at url %s" % (response.status_code, url))
                current_page_size = 0
            page += 1

        # todo get date of race
        url_for_db = BASE_URL_FORMAT_2014ON % (year, 0, div_id)
        race_info = RaceInfo(season, str(year), url_for_db, "%s %s" % (BIRKIE_RACE_NAME, div))
        race = StructuredRaceResults(race_info, total_results)
        race.serialize()


def handle2007To2015(season):
    """
    structured results are available through a different api 2007-2015
    todo merge like components with the 2014On fetcher- very similar (parser is the exact same...)
    :param season:
    :return:
    """
    year = str(int(season) + 1)

    # first, we have to figure out which races belong to this season
    prefetch_parser = Birkie2007To2014Prefetcher(season)
    try:
        response = requests.get(URL_PREFETCH_2007ON)
    except Exception as e:
        print("failed to prefetch birkie races belonging to season '%s'" % (season, ))
        return

    if response.status_code == 200:
        prefetch_parser.feed(response.text)
    else:
        print("failed to prefetch birkie races belonging to season '%s' due to response %d" % (season, response.status_code))

    # now we can fetch the results for the given ids
    for ix, race_id in enumerate(prefetch_parser.event_ids):
        race_name = prefetch_parser.event_names[ix]
        total_results = []
        # indexed from 1 here for some reason
        page = 1
        current_page_size = 100

        # we expect a full page to be of size 100, anything less means no more results
        while current_page_size >= 100:
            url = BASE_URL_FORMAT_2007ON % (race_id, page)
            # reset state of the parser by creating a new one :/
            parser = Birkie2007OnParser()

            try:
                response = requests.get(url)
            except Exception as e:
                print("Failed to get individual race at url %s" % (url,))

            if response.status_code == 200:
                parser.feed(response.text)
                partial_results = parser.race_results
                current_page_size = len(partial_results)
                total_results += partial_results
            else:
                print("Failed to get individual race at url %s due to response %d" % (url, response.status_code))
                current_page_size = 0
            page +=1

        # todo get actual date of the race
        url_for_db = BASE_URL_FORMAT_2007ON % (race_id, page)
        race_info = RaceInfo(season, str(year), url_for_db, race_name)
        race = StructuredRaceResults(race_info, total_results)
        race.serialize()

def handlePre2007Season(season):
    """
    attempt to find unstructured results on the main results page where some pdfs reside
    :param season: season the race took place, probably a year less than the race you are interested in (str)
    :return: void
    """
    year = str(int(season) + 1)

    try:
        response = requests.get(URL_PREFETCH_PRE2007)
    except Exception as e:
        print("Error: failed to prefetch birkie races at url %s" % (URL_PREFETCH_PRE2007))
        return

    prefetch_parser = BirkiePre2007Prefetcher(season)
    if response.status_code == 200:
        prefetch_parser.feed(response.text)
    else:
        print("Error: failed to prefetch birkie races at url '%s' with return code %s" % (URL_PREFETCH_PRE2007, response.status_code))
        return

    cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")

    for ix, race_name in enumerate(prefetch_parser.race_names):
        url = prefetch_parser.race_urls[ix]
        race_info = RaceInfo(season, year, url, race_name)

        try:
            response = urllib2.urlopen(url)
        except Exception as e:
            print("Failed to fetch pdf at url %s" % (url,))
            continue

        if response.getcode() == 200:
            UnstructuredRaceResults(race_info, response.read()).serialize()

    cnx.commit()
    cnx.close()


def fetch_season(season):
    """
    results are stored differently for different years.
    :param season: the season we are getting results for (str)
    :return: void
    """

    if season >= "2013":
        handle2014On(season)
    elif season >= "2007":
        handle2007To2015(season)
    else:
        # attempt to find unstructured results on the main results pages
        handlePre2007Season(season)


if __name__ == "__main__":
    fetch_season("2014")