"""
a config accessor
"""
import os

SCRAPER_TOP = "SCRAPERTOP env var not set"
if "SCRAPERTOP" in os.environ:
    SCRAPER_TOP = os.environ["SCRAPERTOP"]

COMMENT_CHAR = "#"
DELIM_CHAR = "\t"
CONFIG_PATH =  os.path.join(SCRAPER_TOP,"data/config.txt")

def parse_configs():
    """
    create a map representation of app configs
    :return: a string kv store of the configs
    """
    print("Debug: Fetching configs")

    config_map = {}
    with open(CONFIG_PATH, "r") as config_file:
        for line in config_file:
            if not line.startswith(COMMENT_CHAR):
                fields = line.split(DELIM_CHAR)
                if len(fields) < 2:
                    # todo logging
                    print("Warning: invalid config line: %s" % line)
                else:
                    config_map[fields[0]] = fields[1].rstrip("\n")
    return config_map


class Configs:
    config_map = parse_configs()

    def __init__(self):
        print("Debug: creating Config object")

    def get_as_int(self, key):
        """
        :param key: the config to look up
        :return: the value corresponding to key (int). none if config key is not present or cannot be parsed to int
        """
        if key in self.config_map:
            try:
                return int(self.config_map[key])
            except:
                print("Error: could not parse value '%s' for key '%s' as an int"%(val, key))
        return None

    def get_as_string(self, key):
        """
        :param key: the config to look up
        :return: the value corresponding to key (str). none if the config key is not present
        """
        if key in self.config_map:
            return self.config_map[key]
        return None