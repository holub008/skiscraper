# skiscraper
A tool to provide aggregate cross country ski result search capabilities to results hosted on skinnyski.com & a few other sites. Comes with a simple python flask framework to provide a search / results interface. This is primarily a project for getting some oop experience with Python, as well as python web development. I plan to host this once I have reasonably searchable results for the big races (birkie, coll, vasa, etc.) and a usable interface.

Current release searches mostly unstructured text blobs generated from pdf files. Concrete plans:

1. Include high school and college results.
2. Add support for structured results from some of the bigger hosting sites.
3. Add support for plain-text/html results linked directly from skinnyski.
4. Provide links to images from the race, as hosted on skinnyski.com.

Long term goals include:

1. Scrape structured results from pdfs. Due to unstructured nature of data, this will require some form of AI & user verification.
2. Build a more intelligent skinnyski scraper that doesn't dead-end when not linked directly to results page.
3. Create user profiles using the data mined from result documents. Racers have the ability to "claim" unstructured results and make them structured.
4. Create visualizations for racers using their results
5. Move the web stuff to java.

## Required Software and Configurations
1. Python 2.7 (not tested on 3, should work if you change some string encodings and maybe the odd print statement
2. MySQL Database with a table, user and password as specified in config/config.txt. Will probably have to move to psql for hosting.
3. The unix utility 'pdftotext' (will have to a bit of google searching depending on your system: yum install pdftotext, brew install poppler, etc.)
4. Python Flask (pip install flask).

## Quick Start
Clone the repository. Run:
```python
python skiscraper/scraper/getResultDocs.py
python skiscraper/frame/views.py
```
Sorry if something breaks, I don't have a dev branch yet!


