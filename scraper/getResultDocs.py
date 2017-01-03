import datetime

import birkie_fetcher
from configs import Configs
from RaceResultStore import RaceResultStore
import skinnyski_fetcher

config = Configs()

history_years = config.get_as_int("HISTORY_LENGTH")
# SEASONS = [str(datetime.date.today().year - year_delta) for year_delta in range(1, history_years)]
SEASONS = ['2015']
race_store = RaceResultStore()
######################
# start control flow
######################

for season in SEASONS:
    # get low hanging fruit from skinnyski
    race_infos = skinnyski_fetcher.get_race_infos(season)

    for race_info in race_infos:
        # this doesn't solve race_infos that spawn more race_infos
        # so, downstream race_infos will also need to be checked in the store as well (todo)
        if race_info in race_store:
            print("Skipping race already present %s" % (race_info, ))
        else:
            skinnyski_fetcher.process_race(race_info, race_store)

    # get birkie results from the birkie website
    birkie_fetcher.fetch_season(season, race_store)

