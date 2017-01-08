"""
A persistent store of RaceInfos stored in the race db
Note that no actual race data is stored- just the metadata
"""

from RaceResults import RaceInfo
import configs
import mysql.connector


class RaceResultStore:

    def __init__(self):
        self.config = configs.Configs()
        self.race_infos = self._build_from_db()

    def _build_from_db(self):
        """
        todo exception handling and avoid connection leak
        :return: a collection of race infos we know about (Set<RaceInfo>)
        """
        race_table = self.config.get_as_string("RACE_DB")

        cnx = mysql.connector.connect(user=self.config.get_as_string("DB_USER"), password=self.config.get_as_string("DB_PASSWORD"), host="localhost")
        cursor = cnx.cursor()

        raw_sql = "SELECT ryear, division, rdate, rurl, rname from %s" % (race_table, )
        cursor.execute(raw_sql)

        current_race_infos = set()
        for row in cursor:
            print RaceInfo(*row)
            current_race_infos.add(RaceInfo(*row))

        cnx.close()
        return current_race_infos


    def __contains__(self, item):
        """
        :param item: the race to check (RaceInfo)
        :return: whether the other race has already been processed and is in the store (boolean)
        """
        # todo would be good to short circuit with an instance of check
        return item in self.race_infos


    ## todo implement compare on raceinfo objects- must be considerate of sanitization changes