import datetime

from configs import Configs
import skinnyski_fetcher

config = Configs()

history_years = config.get_as_int("HISTORY_LENGTH")
# todo
SEASONS = [str(datetime.date.today().year - year_delta) for year_delta in range(1, history_years)]
######################
# start control flow
######################

for season in SEASONS:
    # get low hanging fruit from skinnyski
    race_infos = skinnyski_fetcher.get_race_infos(season)
    for race_info in race_infos:
        if skinnyski_fetcher.race_already_processed(race_info):
            print("Skipping race already present %s" % (race_info, ))
        else:
            skinnyski_fetcher.process_race(race_info)

