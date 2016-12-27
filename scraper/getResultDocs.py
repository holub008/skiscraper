import datetime

from configs import Configs
import skinnyski_fetcher
import birkie_fetcher

config = Configs()

history_years = config.get_as_int("HISTORY_LENGTH")
# todo
SEASONS = [str(datetime.date.today().year - year_delta) for year_delta in range(1, history_years)]
SEASONS = ['2015']
######################
# start control flow
######################

for season in SEASONS:
    # get low hanging fruit from skinnyski
    race_infos = skinnyski_fetcher.get_race_infos(season)


    for race_info in race_infos:
        # todo this doesn't solve race_infos that spawn more race_infos
        # instead, this logic should be handled as soon as possible- once we know that we already have the race
        # and before we submit request(s)
        if skinnyski_fetcher.race_already_processed(race_info):
            print("Skipping race already present %s" % (race_info, ))
        else:
            skinnyski_fetcher.process_race(race_info)

    # get birkie results from the birkie website
    birkie_fetcher.fetch_season(season)

