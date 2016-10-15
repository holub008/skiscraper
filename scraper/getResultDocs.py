import getURLS ## tool for getting result URLS & properties
import datetime
import os ##moving files around
import urllib2 ##pulling files from the web
import subprocess ##pdf to text utility
import mysql.connector ## race db


history_years = 10
YEARS = [str(datetime.date.today().year - year_delta) for year_delta in range(1,history_years)]
SKINNYSKI_URL="https://skinnyski.com"
DB_USER="scraper"
DB_PASSWORD="Compellent04"
RACE_DB="skiscraper.races"


def isPDF(url):
	"""
		determine if the url dest is a pdf file
	"""
	## TODO check file extension, not just contains
	return ".pdf" in url

def handlePDF(race_obj,year):
	
	name_cleansed = race_obj.name.replace(" ","").replace("/","")

	##get the pdf sitting at the URL
	##TODO handle 404
	response = urllib2.urlopen(race_obj.URL)
	content = response.read()
	
	## write the data into directories in scraper/ TODO yuck
	pwd = os.path.dirname(os.path.realpath(__file__))
	
	fpath = "%s/pdf/%s/"%(pwd,year)
	path_fname = "%s%s"%(fpath,name_cleansed)
	path_fname_ext = "%s.pdf"%(path_fname)
	
	txt_path = "%s/text/%s"%(pwd,year)
	txt_dest = "%s/text/%s/%s.txt"%(pwd,year,name_cleansed)
	
	##build the data dest dir, if not there
	if not os.path.exists(fpath):
		os.makedirs(fpath)
	if not os.path.exists(txt_path):
		os.makedirs(txt_path)
	
	##write the data to a pdf
	file = open(path_fname_ext,'wb')
	file.write(content)
	file.close()
	
	##system call to make a text file of a pdf
	##TODO ensure the pdftotext utility is installed
	##TODO return value
	handle = subprocess.Popen(['/usr/local/bin/pdftotext',path_fname_ext], stdout = subprocess.PIPE)
	handle.wait() ##block until file is written
	os.rename("%s.txt"%path_fname, txt_dest)
	
	##finally, plug entry in skiscraper db
	##TODO create only one connection object
	cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
	cursor = cnx.cursor()
	
	## insure that the parser found all the race properties
	if race_obj.name and race_obj.URL and race_obj.date:
		cursor.execute("INSERT INTO %s (rpath, rname, rdate, ryear, rurl) VALUES('%s','%s','%s','%s','%s')"%(RACE_DB, txt_dest, race_obj.name, race_obj.date ,year, race_obj.URL))
		cnx.commit()
	else:
		print "Missing necessary race info fields"
		##TODO logging
def handleNonPDF(race_obj,year):	
	"""
		attempt to find result sets on sites where the link is not direct to a doc
	"""
	print "TODO nonpdf"
	
def storeFileFromURL(race_obj,year):
	## get and cleanse the race name and URL to results
	url = race_obj.URL
	
	if url:
		##handle relative paths
		if url[0] =="/":
			race_obj.URL = "%s%s"%(SKINNYSKI_URL,url)

		if isPDF(url):
			handlePDF(race_obj,year)
		else:
			handleNonPDF(race_obj,year)				
				
	else:
		##TODO logging
		print "Error: getResultDocs.py: URL is an empty string"
	
######################
## start control flow
######################

for year in YEARS:
	race_objs = getURLS.getRaceObjs(year)
	
	for race in race_objs:
		storeFileFromURL(race,year)
	
