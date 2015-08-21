import requests
from HTMLParser import HTMLParser
import sys

class Race():
	def __init__(self):
		self.date = None
		self.URL = None
		self.name = None
	
	def __str__(self):
		return "<date:%s, URL:%s, name:%s>"%(self.date,self.URL,self.name,)
	def __repr__(self):
		return "%s||%s||%s"%(self.date,self.URL,self.name,)

## create a subclass of HTMLParser to override tag/data handlers
class CustomHTMLParser(HTMLParser):
	def __init__(self):
		##since we're overriding the init member function of HTMLParser, need to run superclass's init
		HTMLParser.__init__(self)
		self.elements =[]
		self.current_element = Race()
		
		## stateful member variables- keep track of progress into the list item
		self.first = False ## so that we can grab the first data element, the date
		self.first_anchor = True ## url and race name reside in the first anchor.
		
	def handle_starttag(self,tag,attrs):
		if tag == "li":
			self.first = True ## first element in every list is the date
		elif tag == 'a' and self.first_anchor:
			self.current_element.URL = self.extractHref(attrs)
			##leave first_anchor true so that we may extract the race name (contained in the data)
	
	def handle_endtag(self,tag):
		if tag =='li':
			self.elements.append(self.current_element)
			self.first_anchor = True
			self.current_element = Race()
		elif tag == 'a':
			self.first_anchor = False
	
	def handle_data(self,data):
		if self.first:
			self.current_element.date = data.rstrip()
			self.first = False
		elif self.first_anchor:
			self.current_element.name = data
			self.first_anchor=False
	
	def extractHref(self,attrs):
		for attr in attrs:
			if len(attr) == 2:
				if attr[0] == 'href':
					return attr[1]
		return "nohrefattr"		
		
def getRaceObjs(year):
	"""
		get the list of URLs to results for the year
	"""
	url = "http://www.skinnyski.com/racing/results/default.asp"

	## submit a post request
	r = requests.post(url,data={"season":str(year)})
	
	## check for http OK
	
	##TODO use a html parser 
	##hacky and at the mercy of skinnyski page design changes... nm we're okay :)
	if r.status_code == 200:
		## simplify the parser's work by cutting down the html to a a bunch of lists
		link_list = r.text[r.text.index("<ul>")+4:r.text.index("</ul>")]
		
		p = CustomHTMLParser()
		try:
			p.feed(link_list)
		except:
			#TODO logging
			print "Failed to parse HTML- may be invalid"
			return []
		return p.elements
	else:
		##TODO logging
		print r.reason
		return []	
	

