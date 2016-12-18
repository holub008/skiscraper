"""
classes representing all the data we hold about races & results
"""
from abc import ABCMeta, abstractmethod
from configs import Configs
from datetime import datetime
import mysql.connector

from pdf_serializer import write_pdf_and_text

config = Configs()
DB_USER = config.get_as_string("DB_USER")
DB_PASSWORD = config.get_as_string("DB_PASSWORD")
RACE_DB = config.get_as_string("RACE_DB")
STRUCTURED_RESULTS_DB = config.get_as_string("STRUCTURED_RESULTS_DB")
UNSTRUCTURED_RESULTS_DB = config.get_as_string("UNSTRUCTURED_RESULTS_DB")


class RaceInfo:
    """
    metadata about a race that can be used to uniquely identify the race
    """
    def __init__(self, s, d, u, n):
        """
        :param s: season (str)
        :param d: date, arbitrary format (str)
        :param u: url (str)
        :param n: race name (str)
        """
        self.season = s
        self.date = d
        self.url = u
        self.name = n

    @staticmethod
    def create_empty(s):
        """
        :param s: the season of the race, as a year (str)
        """
        return RaceInfo(s, None, None, None)

    def set_date_from_skinnyski(self, day):
        """
        mutates both self.date and self.season
        :param day: the month,day combination formatted mon.xx (str)
        """
        # since we don't know year, we might get a ValueError on leap years when considering day- must strip it out.
        date_with_month = datetime.strptime(day.split(".")[0], "%b")
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
        return self.name.replace("/", "").replace(";", "").replace(",", "").replace("'", "")

    def serialize(self, cursor, result_type):
        """
        write the info to db- it is the caller's responsibility to commit the insertions
        :param cursor: db connection object (mysql.connector)
        :return: id of the created race (int)
        """
        raw_sql = "INSERT INTO %s" % (RACE_DB, ) \
                  + " (rname, rdate, ryear, rurl, result_type) VALUES (%s, %s, %s, %s, %s)"

        cursor.execute(raw_sql, (self.name, self.date, self.season, self.url, result_type))

        # this will return the last id generated by the connection- may become a problem if parallelized
        last_id_sql = "SELECT LAST_INSERT_ID()"
        cursor.execute(last_id_sql)

        for result in cursor:
            try:
                return int(result[0])
            except:
                # todo logging
                print "Failed to parse the created race id: too few fields or not an integer:" + str(result)
                return -1

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

    def serialize(self, cursor, race_id):
        """
        the executed command must be committed by the caller
        :param cursor: a db cusor object (mysql.connector.cursor)
        :param race_id: the id of the race in the races db (int)
        :return: void
        """
        raw_sql = "INSERT INTO %s" % (STRUCTURED_RESULTS_DB,) \
                  + " (race_id, name, placement, race_time) VALUES (%s,  %s, %s, %s)"
        cursor.execute(raw_sql, (race_id, self.name, self.place, self.time))


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
        """
        write the race results to db. todo take connection object
        :return: void
        """
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
        cursor = cnx.cursor()
        # first, write the race metadata to the race db
        race_id = self.info.serialize(cursor, "structured")
        cnx.commit()

        # then insert the structured race results into the results db
        for race_result in self.results:
            race_result.serialize(cursor, race_id)
        cnx.commit()
        cnx.close()


class UnstructuredPDFRaceResults(RaceResults):
    """
    a race result for when we only have a text blob, in PDF format
    these results are written to the fs as a text file
    """

    def __init__(self, info, res):
        """
        :param info: Race metadata to uniquely identify the race (RaceInfo)
        :param res: a pdf blob of results (str)
        """
        self.info = info
        self.pdf_content = res

    def serialize(self):
        """
        1. write the race metadata 2. write the string
        :return:
        """

        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
        cursor = cnx.cursor()
        # first, write the race metadata to the race db
        race_id = self.info.serialize(cursor, "unstructured")

        # because I'm not sure mysql is the right tool for storing enormous strings, might still need to use the file
        text_blob = write_pdf_and_text(self.pdf_content, race_id)
        if not text_blob:
            # todo consider making this a TextRaceResult
            text_blob = ""

        raw_sql = "INSERT INTO " + UNSTRUCTURED_RESULTS_DB + " (race_id, text_blob) VALUES (%s, %s)"
        cursor.execute(raw_sql, (race_id, text_blob))
        cnx.commit()


class UnstructuredTextRaceResults(RaceResults):
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
        self.text_content = res

    def serialize(self):
        """
        1. write the race metadata 2. write the string
        :return:
        """

        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host="localhost")
        cursor = cnx.cursor()
        # first, write the race metadata to the race db
        race_id = self.info.serialize(cursor, "unstructured")

        raw_sql = "INSERT INTO " + UNSTRUCTURED_RESULTS_DB + " (race_id, text_blob) VALUES (%s, %s)"
        cursor.execute(raw_sql, (race_id, self.text_content))
        cnx.commit()
