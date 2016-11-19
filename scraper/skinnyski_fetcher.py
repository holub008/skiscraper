import mysql.connector
import requests
import urllib2

from configs import Configs
from HTMLParser import HTMLParser
import itiming_fetcher
import mtec_fetcher
from pdf_serializer import write_pdf_and_text
from RaceResults import RaceInfo

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
    def __init__(self, season):
        # since we're overriding the init member function of HTMLParser, need to run superclass's init
        HTMLParser.__init__(self)
        self.elements = []
        self.current_element = RaceInfo.create_empty(season)
        self.current_name_starter = ""
        self.season = season

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
            self.current_element.url = self.extractHref(attrs)
            # leave first_anchor true so that we may extract the race name (contained in the data)

    def handle_endtag(self, tag):
        if tag == 'li':
            self.elements.append(self.current_element)
            self.first_anchor = True
            self.current_element = RaceInfo.create_empty(self.season)
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

    def extractHref(self, attrs):
        for attr in attrs:
            if len(attr) == 2:
                if attr[0] == 'href':
                    # handle relative addresses
                    if attr[1].startswith("/"):
                        return "%s%s" % (SKINNYSKI_URL, attr[1])
        return "nohrefattr"


def is_pdf(race_info):
    """
    :param race_info: the race metadata to be inspected (RaceInfo)
    :return: if the indicated url is a pdf (bool)
    """
    return race_info.url.endswith(".pdf")


def is_mtec_hosted(race_info):
    """
    :param race_info: the race metadata to be inspected (RaceInfo)
    :return: if the given race is hosted on mtec.com (bool)
    """
    # todo regex
    return "mtec" in race_info.url


def is_itiming_hosted(race_info):
    """
    :param race_info:  the race metadata to be inspected (RaceInfo)
    :return: if the given race is hosted on itiming.com
    """
    # todo regex
    return "itiming" in race_info.url

def handle_pdf(race_info):
    """
    :param race_info: race metadata (RaceInfo)
    :return: void
    """
    pdf_content = get_skinnyski_pdf(race_info)
    if pdf_content:
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
        race_id = race_info.serialize(cnx.cursor(), "unstructured")
        cnx.close()
        # yikes I've coded myself into a corner here :) todo!
        # the solution should be to write all races in the same directory (maybe a pdf/ and text/) with the race_id as the filename
        # no need for a filepath then
        text_path = write_pdf_and_text(pdf_content, race_id)
    else:
        print("Warning: skipping a pdf which was unable to be accessed")

def get_skinnyski_pdf(race_info):
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


def handle_nonpdf(race_info):
    """
        attempt to find result sets on sites where the link is not direct to a doc
    """
    print("TODO nonpdf")
    pass


def process_race(race_info):
    """
    determine how to handle this race and process accordingly
    :param race_info: race metadata (RaceInfo)
    :return: void
    """
    if race_info.url:
        if is_pdf(race_info):
            handle_pdf(race_info)
        elif is_mtec_hosted(race_info):
            mtec_fetcher.process_race(race_info)
        elif is_itiming_hosted(race_info):
            itiming_fetcher.process_race(race_info)
        else:
            handle_nonpdf(race_info)

    else:
        # todo logging
        print "Error: URL is not present"


def get_race_infos(season):
    """
        get the list of URLs to results for the year
    """
    url = "%s/racing/results/default.asp" % (SKINNYSKI_URL, )
    r = requests.post(url, data={"season": str(season)})

    # hacky and at the mercy of skinnyski page design changes... nm we're okay :)
    if r.status_code == 200:
        # simplify the parser's work by cutting down the html to a a bunch of lists
        link_list = r.text[r.text.index("<ul>") + 4:r.text.index("</ul>")]

        parser = SkinnySkiRaceInfoParser(season)
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


def race_already_processed(race_info):
    # todo move to utility class for recycling!- use for birkie fetcher
    # ensure that the parser found all the race properties
    # if we don't make this entry in the db, the race will simply never be searched
    if race_info.name and race_info.url and race_info.date:
        # todo only one connection
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
        cursor = cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM %s WHERE rname='%s' and ryear='%s' and rurl='%s'"
                       % (RACE_DB, race_info.get_cleansed_name(), race_info.season, race_info.url))
        count = int(next(cursor)[0])
        cnx.close()
        return count > 0
    else:
        print "Found a race with a null name/url/date. Always will reprocess by default."
        return False

if __name__ == "__main__":
    race_infos = get_race_infos("2014")
    for i in range(0,10):
        process_race(race_infos[i])
