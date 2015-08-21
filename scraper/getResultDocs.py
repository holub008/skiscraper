import getURLS
import datetime
import os
import urllib2
import subprocess


history_years = 10
YEARS = [str(datetime.date.today().year - year_delta) for year_delta in range(1,history_years)]
SKINNYSKI_URL="https://skinnyski.com"

def isPDF(url):
	"""
		determine if the url dest is a pdf file
	"""
	## TODO check file extension, not just contains
	return ".pdf" in url

def handlePDF(url,rname,year):
	response = urllib2.urlopen(url)
	content = response.read()
	
	## write the data into directories in scraper/
	pwd = os.path.dirname(os.path.realpath(__file__))
	
	fpath = "%s/pdf/%s/"%(pwd,year)
	path_fname = "%s%s"%(fpath,rname)
	path_fname_ext = "%s.pdf"%(path_fname)
	
	txt_path = "%s/text/%s"%(pwd,year)
	txt_dest = "%s/text/%s/%s.txt"%(pwd,year,rname)
	
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
	handle = subprocess.Popen(['/usr/bin/pdftotext',path_fname_ext], stdout = subprocess.PIPE)
	handle.wait() ##block until file is written
	os.rename("%s.txt"%path_fname, txt_dest)

def handleNonPDF(url,rname,year):	
	"""
		attempt to find result sets on sites where the link is not direct to a doc
	"""
	print "TODO nonpdf"
	
def storeFileFromURL(race_obj,year):
	url = race_obj.URL
	rname = race_obj.name.replace(" ","")
	
	if len(url) > 0:
		##handle relative paths
		if url[0] =="/":
			absolute_address = "%s%s"%(SKINNYSKI_URL,url)
		else:
			absolute_address = url

		if isPDF(url):
			handlePDF(absolute_address,rname,year)
		else:
			handleNonPDF(absolute_address,rname,year)				
				
	else:
		##TODO logging
		print "Error: getResultDocs.py: URL is an empty string"
	
######################
## start control flow
######################
for year in YEARS:
	race_objs = getURLS.getRaceObjs(year)
	storeFileFromURL(race_objs[0],year)
	