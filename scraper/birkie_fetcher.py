import requests
from HTMLParser import HTMLParser
from RaceResults import RaceResult
# division ids for forming the url correspond to list index
RACES = ["51K Skate","55K Classic","24K Skate","24K Classic"]

# bunch of boilerplate, only variable params are page # (100 per page), year, and divId
BASE_URL_FORMAT = "http://birkie.pttiming.com/results/%d/index.php?page=1150&r_page=division&pageNum_rsOverall=%d&divID=%d"


class Birkie2014Parser(HTMLParser):
    """
    a custom parser for results on birkie.pttiming.com
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_data_row = False
        self.current_race_result = RaceResult("","","")
        self.current_td_data = []
        self.td_count = 0
        self.race_results = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr" and self.extract_class(attrs) == "dataRow":
            self.td_count = 0
            self.in_data_row = True
            self.current_race_result = RaceResult("","","")
        elif tag == "td" and self.in_data_row:
            self.td_count += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_data_row:
            self.race_results.append(self.current_race_result)
            self.in_data_row = False
        elif tag == "td" and self.in_data_row:
            clean_data = " ".join([x.strip() for x in self.current_td_data])
            if self.td_count == 1:
                self.current_race_result.place = clean_data
            elif self.td_count == 5:
                self.current_race_result.name = clean_data
            elif self.td_count == 6:
                self.current_race_result.time = clean_data
            self.current_td_data = []

    # html parser is disgusting and gives the data not as an entire string
    def handle_data(self, data):
        if self.in_data_row:
            self.current_td_data.append(data)

    @staticmethod
    def extract_class(attrs):
        for attr_pair in attrs:
            if len(attr_pair) == 2:
                if attr_pair[0] == "class":
                    return attr_pair[1]
        return None


def fetch_and_process(season):
    """

    :param season: the season of the race we want. note Birkies are in Feb, so they are a year ahead (str)
    :return: void
    """
    year = int(season) + 1

    parser = Birkie2014Parser()
    page = 0
    lastt_page_size = 100
    # page size defaults to 100, if smaller, we've reached the end
    while current_page_size == 100:
        for div_ix, div in enumerate(RACES):
            div_id = div_ix + 1
            url = BASE_URL_FORMAT % (year, page, div_id)
            try:
                response = requests.get(url)
            except Exception as e:
                print("failed to fetch Birkie results at url (%s) with error: %s" % (url, str(e)))

            table = ""
            if response.status_code == 200:
                table = response.text[response.text.index("Overall Event Results"):]
            else:
                print("Bad response code (%d) at url %s" % (response.status_code, url))
        partial_race_results = parser.feed(table)

if __name__ == "__main__":
    fetch_and_process("2015")