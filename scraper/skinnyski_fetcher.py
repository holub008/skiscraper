import mysql.connector
import os
import requests
import subprocess
import urllib2

from configs import Configs
from HTMLParser import HTMLParser
import itiming_fetcher
import mtec_fetcher
from RaceResults import RaceInfo

config = Configs()
SKINNYSKI_URL = config.get_as_string("RESULTS_URL")
DB_USER = config.get_as_string("DB_USER")
DB_PASSWORD = config.get_as_string("DB_PASSWORD")
RACE_DB = config.get_as_string("RACE_DB")
PDF_TO_TEXT = config.get_as_string("PDF_TO_TEXT")
DATA_DIR = os.path.join(config.SCRAPERTOP, "data/")


class SkinnySkiRaceInfoParser(HTMLParser):
    """
        a subclass of HTMLParser to override tag/data handlers
    """
    def __init__(self, season):
        # since we're overriding the init member function of HTMLParser, need to run superclass's init
        HTMLParser.__init__(self)
        self.elements = []
        self.current_element = RaceInfo(season)
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
            self.current_element = RaceInfo(self.season)
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


def write_pdf_and_text(race_info, pdf_content):
    """
    the workhorse- writes the pdf to disk, converts it to a txt, writes txt to disk

    :param race_info: race metdata (RaceInfo)
    :param pdf_content: a blob representing (hopefully) a pdf (str)
    :return: void
    """

    fpath = os.path.join(DATA_DIR,"pdf/", race_info.season)
    path_fname = os.path.join(fpath, race_info.get_cleansed_name())
    path_fname_ext = "%s.pdf" % (path_fname, )

    txt_path = os.path.join(DATA_DIR, "text/", race_info.season)
    txt_dest = os.path.join(txt_path, race_info.get_cleansed_name())
    txt_dest_ext = "%s.txt" % (txt_dest, )

    # build the data dest dirs, if not there
    if not os.path.exists(fpath):
        os.makedirs(fpath)
    if not os.path.exists(txt_path):
        os.makedirs(txt_path)

    # write the data to a pdf
    pdf_file = open(path_fname_ext,'wb')
    pdf_file.write(pdf_content)
    pdf_file.close()

    # todo check return value of pdftotext
    handle = subprocess.Popen([PDF_TO_TEXT, path_fname_ext, txt_dest_ext], stdout = subprocess.PIPE)
    handle.wait() # block until file is written

    return txt_dest_ext


def write_race_metadata(race_info, text_path):
    # todo create only one connection object (sloooow)
    cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
    cursor = cnx.cursor()

    # ensure that the parser found all the race properties
    # if we don't make this entry in the db, the race will simply never be searched
    if race_info.name and race_info.url and race_info.date:
        cursor.execute("INSERT INTO %s (rpath, rname, rdate, ryear, rurl) VALUES('%s','%s','%s','%s','%s')" % (RACE_DB,
        text_path, race_info.get_cleansed_name(), race_info.date, race_info.season, race_info.url))
        cnx.commit()
    else:
        print("Missing necessary race info fields- this entry will not be searched")
        # todo logging
    cnx.close()


def handle_pdf(race_info):
    """
    :param race_info: race metadata (RaceInfo)
    :return: void
    """
    pdf_content = get_skinnyski_pdf(race_info)
    if pdf_content:
        text_path = write_pdf_and_text(race_info, pdf_content)
        write_race_metadata(race_info, text_path)
    else:
        print("Warning: skipping a pdf which was unable to be accessed")


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

