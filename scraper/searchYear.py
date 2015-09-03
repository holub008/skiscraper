import mysql.connector
import os

## TODO yuck
RESULT_PARENT = "%s/text"%os.path.dirname(os.path.realpath(__file__))

## race db credentials
DB_USER="scraper"
DB_PASSWORD="Compellent04"
RACE_DB="skiscraper.races"

def getPathHits(key,year):
	"""
		a temporary solution until an inverted index is implemented / integrated
		simply search through all the files for a given string
	"""
	
	RESULT_SOURCE = "%s/%s/"%(RESULT_PARENT,str(year))
	
	race_files = [RESULT_SOURCE + race for race in os.listdir(RESULT_SOURCE)]
	
	path_hits = []
	for race_path in race_files:
		handle = open(race_path,'r')
		contents = handle.read()
		handle.close()
		
		## search the document for a hit
		if key.lower() in contents.lower():
			path_hits.append(race_path)
	
	return path_hits

def search(key,years):
	
	## the list of search results, formatted to be inserted straight into the client datatable
	search_result = []
	
	for year in years:
	
		## get the results hit for the year
		paths = getPathHits(key,year)
		
		cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
		cursor = cnx.cursor()
		## join the result paths with the database entries		
		## note checking for list membership in mysql requires making a list of strings (joining on ',')
		cursor.execute("SELECT * FROM skiscraper.races WHERE rpath IN ('%s')"%("','".join(paths)))
		for row in cursor:
			search_result.append(row)
	
	return search_result
		

		