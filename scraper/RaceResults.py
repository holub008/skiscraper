"""
classes representing all the data we hold about races & results
"""
from abc import ABCMeta, abstractmethod
from datetime import datetime


class RaceInfo:
    """
    metadata about a race that can be used to uniquely identify the race
    """
    def __init__(self, s):
        """
        :param s: the season of the race, as a year (str)
        """
        self.season= s
        self.date = None
        self.url = None
        self.name = None

    def set_date_from_skinnyski(self, day):
        """
        mutates both self.date and self.season
        :param day: the month,day combination formatted mon.xx (str)
        """
        # since we don't know year, we might get a ValueError on leap years when considering day- must strip it out.
        date_with_month = datetime.strptime(day.split(".")[0],"%b")
        # case: season is the prior year
        if date_with_month.month in (1, 2, 3, 4, 5):
            try:
                self.season = str(int(self.season) + 1)
            except:
                print("Error: could not parse season as an integer")
        # case: we aren't in the late months of the year, something unexpected has happened
        elif date_with_month.month not in (11, 12):
            print "Error: unexpected season (%s) / month (%s) combination encountered" % (self.season, date_with_month.month)

        self.date = datetime.strptime("%s.%s" % (self.season, day), '%Y.%b.%d')

    def get_cleansed_name(self):
        return self.name.replace("/", "").replace(";", "").replace(",", "").replace("'","")

    def __str__(self):
        return "<date:%s, URL:%s, name:%s>" % (self.season, self.url, self.name,)

    def __repr__(self):
        return "%s||%s||%s" % (self.season, self.url, self.name,)


class RaceResult:
    """
    an individual's result from a race
    """
    def __init__(self, n, t, p):
        """
        todo name should eventually be an id
        :param n: the name of the racer (str)
        :param t: the time of the racer (str)
        :param p: the placement of the racer- could be an int or fractional (str)
        """
        self.name = n
        self.time = t
        self.place = p

    def __str__(self):
        return "<name:%s, time:%s, place:%s>" % (self.name, self.time, self.place)

    def __repr__(self):
        return "%s||%s||%s" % (self.name, self.time, self.place)

    def serialize(self, race_id):


class RaceResults:
    """
    This "interface" defines a contract of what functionality inheriting RaceResults should
    provide.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def serialize(self):
        """
        persist the race result somewhere
        """
        pass

    @staticmethod
    @abstractmethod
    def deserialize(race_id):
        """
        :param race_id: uniquely identifying value for the race (str)
        :return: the deserialized RaceResult, if the race_id corresponds to a valid race
        """
        pass

    @abstractmethod
    def matches_query(self, query):
        """
        :param query: the value to be searched for (str) todo expand to a Query type (regex, name, etc.)
        :return: whether not the results match the given query (bool)
        """
        pass


class StructuredRaceResults(RaceResults):
    """
    a race result for when we have structured data- the results have been parsed
    these results are stored in a db
    """
    def __init__(self, info, res):
        """
        :param info: Race metadata to uniquely identify the race (RaceInfo)
        :param res: A list of pre-parsed race results (List<RaceResult>)
        """
        self.info = info
        self.results = res

    def serialize(self):
        pass

    @staticmethod
    def deserialize(race_id):
        pass

    def matches_query(self, query):
        """
        a simple implementation that checks if the query matches racer name by strict comparison
        """
        for result in self.results:
            if result.name == query:
                return True
        return False


class UnstructuredRaceResults(RaceResults):
    """
    a race result for when we only have a text blob
    these results are written to the fs as a text file
    """

    def __init__(self, info, res):
        """
        :param info: Race metadata to uniquely identify the race (RaceInfo)
        :param res: a text blob of results (str)
        """
        self.info = info
        self.results = res

    def serialize(self):
        pass

    @staticmethod
    def deserialize(race_id):
        pass

    def matches_query(self, query):
        """
        a simple implementation that splits the query into tokens on whitespace, then searches for those tokens
        individually across the text blob. everything lowercase
        """
        case_insensitive_results = self.results.lower()
        for token in query.split("\t"):
            if not token.lower() in case_insensitive_results:
                return False
        return True
