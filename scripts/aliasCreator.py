import os
from astroquery.simbad import Simbad

for directory in os.listdir("../Individual_Novae"):
	if not "." in directory:
		string = ""		
		try:
			aliases = Simbad.query_objectids("V* " + directory.replace("_"," "))
		except:
			print("Could not find " + directory.replace("_", " "))
			continue
		for i in range(len(aliases)):
			string += aliases[i][0].decode() + "\n"
		string = string[:-1]
		
		
		aliasFile = open("../Individual_Novae/" + directory + "/aliases.txt", "w")
		aliasFile.write(string)
		aliasFile.close()
