# skiscraper
A tool to provide aggregate cross country ski result search capabilities to results hosted on skinnyski.com. Exists only as a proof of concept in current state. Improvements coming Decemeber of 2015.

Current release (9/23/15) only includes functionality to search direct linked pdf files from http://www.skinnyski.com/racing/results/.

Comes with a simple python flask framework to provide a search / results interface.

## Required Software and Configurations
1. Python 2.7 (not tested on 3, but should work run if all print statements are revised)
2. MySQL Database with a table, user and password as specified in scraper/getResultDocs.py. Same configs required in scraper/searchYear.py.
3. The Unix utility 'pdftotext'.
4. Python Flask (if you wish to run the simple search interface).

## Quick Start
Clone the repository. Run:
```python
python skiscraper/scraper/getResultsDocs.py
python skiscraper/frame/views.py
```


