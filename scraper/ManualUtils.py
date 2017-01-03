"""
utilities for one-off mantainence tasks
"""
import sys
import mysql.connector


USAGE = """
-d <comma separated race ids to be cleared from db>
"""


def remove_race_by_id(race_id):
    cnx = mysql.connector.connect(user=self.config.get_as_string("DB_USER"),
                                  password=self.config.get_as_string("DB_PASSWORD"), host="localhost")
    cursor = cnx.cursor()

    remove_unstructured_results_sql = "DELETE * FROM skiscraper.unstructured_race_results where race_id = %s"
    remove_structured_results_sql = "DELETE * FROM skiscraper.unstructured_race_results where race_id = %s"
    remove_race_sql = "DELETE * FROM skiscraper.races where id = %s"

    cursor.execute(remove_unstructured_results_sql, params=(race_id))
    cursor.execute(remove_structured_results_sql, params=(race_id))
    cursor.execute(remove_race_sql, params=(race_id))

    cnx.close()


#########################
# start control flow
#########################

arg_ix = 0
while arg_ix < len(sys.argv):
    if sys.argv[arg_ix] == "-d":
        if arg_ix + 1 >= len(sys.argv):
            print("Error: missing race ids for race delete command")
            print USAGE
            sys.exit(-1)
        else:
            arg_ix += 1
            race_ids = sys.argv[arg_ix]
            for race_id in race_ids.split(","):
                if race_id.isdigit():
                    remove_race_by_id(race_id)
                else:
                    print "Skipping malformed race id '%s' - must be numeric" % (race_id, )
                    continue