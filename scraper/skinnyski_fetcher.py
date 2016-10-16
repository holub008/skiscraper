import requests
from HTMLParser import HTMLParser
from RaceResults import RaceInfo


class CustomHTMLParser(HTMLParser):
    """
        a subclass of HTMLParser to override tag/data handlers
    """
    def __init__(self, season):
        # since we're overriding the init member function of HTMLParser, need to run superclass's init
        HTMLParser.__init__(self)
        self.elements = []
        self.current_element = RaceInfo()
        self.season = season

        # so that we can grab the first data element, the date
        self.first = False
        # url and race name reside in the first anchor.
        self.first_anchor = True

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            # first element in every list is the date
            self.first = True
        elif tag == 'a' and self.first_anchor:
            self.current_element.URL = self.extractHref(attrs)
            # leave first_anchor true so that we may extract the race name (contained in the data)

    def handle_endtag(self, tag):
        if tag == 'li':
            self.elements.append(self.current_element)
            self.first_anchor = True
            self.current_element = RaceInfo()
        elif tag == 'a':
            self.first_anchor = False

    def handle_data(self, data):
        if self.first:
            self.current_element.set_date_from_skinnyski(self.season, data.rstrip())
            self.first = False
        elif self.first_anchor:
            self.current_element.name = data
            self.first_anchor = False

    def extractHref(self, attrs):
        for attr in attrs:
            if len(attr) == 2:
                if attr[0] == 'href':
                    return attr[1]
        return "nohrefattr"


def get_race_infos(season):
    """
        get the list of URLs to results for the year
    """
    # todo config
    url = "http://www.skinnyski.com/racing/results/default.asp"
    r = requests.post(url, data={"season": str(season)})

    # todo use a html parser
    # hacky and at the mercy of skinnyski page design changes... nm we're okay :)
    if r.status_code == 200:
        # simplify the parser's work by cutting down the html to a a bunch of lists
        link_list = r.text[r.text.index("<ul>") + 4:r.text.index("</ul>")]

        p = CustomHTMLParser(season)
        try:
            p.feed(link_list)
        except:
            # TODO logging
            print("Failed to parse HTML- may be invalid")
            return []
        return p.elements
    else:
        # TODO logging
        print("Error: failed to connect to skinnyski: %s" % r.reason)
        return []
