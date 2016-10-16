import skinnyski_fetcher ## tool for getting result URLS & properties
import datetime
import os ##moving files around
import urllib2 ##pulling files from the web
import subprocess ##pdf to text utility
import mysql.connector ## race db
from configs import Configs
from skinnyski_fetcher import get_race_infos

config = Configs()

history_years = config.get_as_int("HISTORY_LENGTH")
SEASONS = [str(datetime.date.today().year - year_delta) for year_delta in range(1, history_years)]
SKINNYSKI_URL = config.get_as_string("RESULTS_URL")
DB_USER = config.get_as_string("DB_USER")
DB_PASSWORD = config.get_as_string("DB_PASSWORD")
RACE_DB = config.get_as_string("RACE_DB")


def is_pdf(url):
    """
    :param url: the url to be inspected (str)
    :return: if the indicated url is a pdf (bool)
    """
    return url.endsWith(".pdf")


def handle_pdf(race_info, season):

    # cleanse the race name
    race_info.name = race_info.name.replace(" ","").replace("/","")

    response = urllib2.urlopen(race_info.url)
    if not response.getcode() == 200:
        # todo logging
        print "Error: failed to open resource at %s" % race_info.url
        return
    content = response.read()

    # write the data into directories in scraper/ todo yuck
    pwd = os.path.dirname(os.path.realpath(__file__))

    fpath = "%s/pdf/%s/"%(pwd, season)
    path_fname = "%s%s"%(fpath, race_info.name)
    path_fname_ext = "%s.pdf" % (path_fname, )

    txt_path = "%s/text/%s"%(pwd, season)
    txt_dest = "%s/text/%s/%s.txt"%(pwd, season, race_info.name)

    # build the data dest dirs, if not there
    if not os.path.exists(fpath):
        os.makedirs(fpath)
    if not os.path.exists(txt_path):
        os.makedirs(txt_path)

    # write the data to a pdf
    pdf_file = open(path_fname_ext,'wb')
    pdf_file.write(content)
    pdf_file.close()

    # todo check return value of pdftotext
    handle = subprocess.Popen(['/usr/local/bin/pdftotext',path_fname_ext], stdout = subprocess.PIPE)
    handle.wait() # block until file is written
    os.rename("%s.txt"%path_fname, txt_dest)

    # todo create only one connection object
    cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
    cursor = cnx.cursor()

    # ensure that the parser found all the race properties
    # if we don't make this entry in the db, the race will simply never be searched
    if race_info.name and race_info.url and race_info.date:
        cursor.execute("INSERT INTO %s (rpath, rname, rdate, ryear, rurl) VALUES('%s','%s','%s','%s','%s')" % (RACE_DB,
        txt_dest, race_info.name, race_info.date , season, race_info.url))
        cnx.commit()
    else:
        print("Missing necessary race info fields- this entry will not be searched")
        # todo logging


def handle_nonpdf(race_obj, year):
    """
        attempt to find result sets on sites where the link is not direct to a doc
    """
    print "TODO nonpdf"


def store_file_from_url(race_info, season):
    if race_info.url:
        # handle relative paths
        if race_info.url.startswith("/"):
            race_info.url = "%s%s"%(SKINNYSKI_URL,race_info.url)

        if is_pdf(race_info.url):
            handle_pdf(race_info.url, season)
        else:
            handle_nonpdf(race_info, season)

    else:
        # todo logging
        print "Error: URL is not present"

######################
# start control flow
######################

for season in SEASONS:
    race_infos = get_race_infos(season)

    for race in race_infos:
        store_file_from_url(race, season)

