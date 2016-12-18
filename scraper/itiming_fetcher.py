from HTMLParser import HTMLParser
import urllib2

from RaceResults import RaceInfo


class ITimingHTMLParser(HTMLParser):
    """
    parse the itiming landing page to find the relevant link to the results table
    """

    def __init__(self):
        HTMLParser.__init__(self)

        self.in_anchor = False
        self.results_url = None
        self.current_href = None

    def handle_starttag(self, tag, attrs):
        # yeesh. why not capitalize your html elements?!
        if tag.lower() == "a":
            self.in_anchor = True
            self.current_href = ITimingHTMLParser.extract_attr(attrs, "href")

    def handle_data(self, data):
        # not sure how consistent this magic string is- may need to do "rough" comparison
        if self.in_anchor and data == "Searchable Results with Leaderboard":
            self.results_url = self.current_href

    def handle_endtag(self, tag):
        if tag.lower() == "a":
            self.in_anchor = False

    def get_result_url(self):
        return self.results_url

    @staticmethod
    def extract_attr(attrs, attr_name):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == attr_name:
                    return attr_pair[1]
        return None


def process_race_from_landing(race_info):
    """
    process results on the itiming site, starting potentially from the landing page in race_info.url
    :param race_info: race metadata (RaceInfo)
    :return: void
    """

    response = urllib2.urlopen(race_info.url)
    if not response.getcode() == 200:
        # todo logging
        print("Did not receive the expected response from itiming url: " + race_info.url)
        return

    parser = ITimingHTMLParser()
    parser.feed(response.read())

    race_url  = parser.get_result_url()
    if race_url:
        race_info.url = race_url
        process_race(race_info)
    else:
        # todo logging
        print("Failed to find results page for itiming url: " + race_info.url)


def process_race(race_info):
    """
    process results on the itiming site. this method may spawn the creation of new race_info types.
    :param race_info: race metadata (RaceInfo)
    :return: void
    """
    pass

# investigation:
# starting from http://www.itiming.com/html/raceresults.php?year=2016&EventId=1322&eventype=0
# follow searchable results
# curl 'https://results.chronotrack.com/embed/results/results-grid?callback=results_grid7423793&sEcho=3&iColumns=11&sColumns=&iDisplayStart=0&iDisplayLength=100&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8&mDataProp_9=9&mDataProp_10=10&raceID=41116&bracketID=435632&intervalID=82716&entryID=&eventID=17250&eventTag=event-17250&oemID=www.chronotrack.com&genID=7423793&x=1482043311101&_=1482043311102' -H 'Cookie: CT=d8bsh08cmc40hqief2g18qbje2; _gat_UA-34134613-4=1; _ga=GA1.3.2074290227.1482043077' -H 'X-NewRelic-ID: Vg8EVlRbGwIFVFhRBwcB' -H 'Accept-Encoding: gzip, deflate, sdch, br' -H 'Accept-Language: en-US,en;q=0.8' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36' -H 'Accept: text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01' -H 'Referer: https://results.chronotrack.com/event/results/event/event-17250' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --compressed
# results in js with an embedded json string of results

if __name__ == "__main__":
    r = RaceInfo("2015","2016-01-01", "http://www.itiming.com/html/raceresults.php?year=2016&EventId=1322&eventype=0", "Pre-birkie")
    process_race_from_landing(r)