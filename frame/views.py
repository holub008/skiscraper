import sys
#todo bleck
sys.path.insert(0, '/Users/kholub/skiscraper/scraper/')

import searchYear

from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")
	
@app.route('/search/')
def search():
	return render_template("search.html")
	
@app.route('/search/_submit/')
def submitsearch():
	
	search_key = request.args.get('key',None,type=str)
	
	#TODO
	years = ["2014","2015"]
	
	rows = searchYear.search(search_key,years)
	
	return jsonify(results=rows)

# entry point
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8080,debug=True)
