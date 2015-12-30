##TODO better alternative to relative pathing?

class ConfigReader():
	def __init__(self):
		self.CONFIG_DELIMITER = "\t"
		self.CONFIG_PATH = "../config/config.txt"
		self.lookup = {}
		
	def readConfigs(self):
		#read the whole file into memory (it should be small)
		with open(self.CONFIG_PATH,"r") as config:
			lines = config.readlines()
			for line in lines:
				if(not line[0] == "#"):
					fields = line.split(self.CONFIG_DELIMITER)
					if(len(fields) >1):
						self.lookup[fields[0]] = fields[1]
					## else, ignore the entry- any exception handling to be done by the caller
					
	def getConfig(self,config_name):
		if(config_name in self.lookup):
			return self.lookup[config_name]
		return None
