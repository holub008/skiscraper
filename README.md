# skiscraper
A tool to provide aggregate cross country ski result search capabilities to results hosted on skinnyski.com. Exists only as a proof of concept in current state. Improvements coming Decemeber of 2015. Comes with a simple python flask framework to provide a search / results interface.

Current release (9/23/15) only includes functionality to search direct linked pdf files from http://www.skinnyski.com/racing/results/. Next iteration plans are to

1. Include high school and college results.
2. Expand to handling plaintext pages, links to plaintext, links to pages hosting results pdfs.
3. Provide links to images from the race, as hosted on skinnyski.com.

Long term goals include:

1. Scrape racer name, city, club affiliation, and time from result documents. Due to unstructured nature of data, this will require some form of AI & user verification.
2. Create user profiles using the data mined from result documents.
3. Create visualizations for racers using their results

## Required Software and Configurations
1. Python 2.7 (not tested on 3, but should work run if all print statements are revised)
2. MySQL Database with a table, user and password as specified in config/config.txt.
3. The Unix utility 'pdftotext' (yum install pdftotext, brew install poppler, etc.).
4. Python Flask (pip install flask).

## Quick Start
Clone the repository. Run:
```python
python skiscraper/scraper/getResultDocs.py
python skiscraper/frame/views.py
```


