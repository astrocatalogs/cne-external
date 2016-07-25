from astroquery.vizier import Vizier
import re
import os
import os.path

_o = "Optical"
_ir = "Infrared"
_s = "Spectra"
_p = "Photometry"

#put catalogs in here
#dictionary with catalog names as keys tuples with (novaName ,author, regime, datatype); novaName is MULT if multiple nova
catalogs={"J/AJ/140/34/table2": ("MULT", "Strope", _o, _p), "J/ApJS/187/275/mags": ("MULT", "Schaefer", _o, _p), "J/other/NewA/27.25": ("KT_Eri", "Munari", _o, _p), "J/MNRAS/435/771": ("V959_Mon", "Munari", _o, _p), "J/MNRAS/387/344": ("V2615_Oph", "Munari", _o, _p), "J/A+A/492/145": ("V2362_Cyg", "Munari", _o, _p), "J/A+A/452/567": ("V477_Sct", "Munari", _o, _s), "J/A+A/434/1107/photom": ("V838_Mon", "Munari", _o, _p)}

directory = "DataToImport/"

#program does this for you
keys = []

Vizier.ROW_LIMIT = -1

if not os.path.exists(directory):
	os.mkdir(directory)

for page in catalogs:
	keys.append(page)

dataTables = Vizier.get_catalogs(keys)
keys = dataTables.keys()

keyRepeatDict = {}

for key in keys:
	if key not in keyRepeatDict:
		keyRepeatDict[key] = 0
	else:
		keyRepeatDict[key] += 1

	names = ()
	for catalogKey in catalogs:
		if re.search(catalogKey.replace("+", "\+").replace(".", "\."), key):
			names = catalogs[catalogKey]
		
	if names == ():
		print("Error with catalog " + catalogKey)
		continue
	
	name = "%s_%s_%s_%s" %names
	name += ("" if keyRepeatDict[key] == 0 else str(keyRepeatDict[key]))
	name += ".dat"

	data = dataTables[key]
	data.write(directory + name, format = "ascii")
	print("Completed writing "  + name)


fileSplitList = []
otherFileList = []
for fileName in os.listdir(directory):
	if re.match("MULT", fileName, re.IGNORECASE):
		fileSplitList.append(fileName)
	else:
		otherFileList.append(fileName)


for f in fileSplitList:
	novaNameCol = -1
	fileName = directory + f
	contents = open(fileName)
	text = contents.read()
	text = text.replace("\r", "\n")
	textArray = text.split("\n")
	if textArray[-1] == '':
		textArray = textArray[:-1]

	textArray = [re.split(''' (?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', textArray[i]) for i in range(len(textArray))]	 	
	titles = textArray[0]
	
	for i in range(len(titles)):
		if titles[i].lower() in ["nova", "name"]:
			novaNameCol = i

	if novaNameCol == -1:
		print("Error with file " + f)
		continue

	novaeNameList = ["",]
	for i in range(1, len(textArray)):		
		novaName = textArray[i][novaNameCol]
		novaName = novaName.replace('"', '')
		novaName = novaName.replace("'", "")
		novaName = novaName.replace(" ", "_")
		novaeNameList.append(novaName)
	
	newNameDict = {}
	for i in range(1, len(textArray)):
		if novaeNameList[i] not in newNameDict:
			newNameDict[novaeNameList[i]] = [i,]
		else:
			newNameDict[novaeNameList[i]].append(i)

	
	textArray = [",".join(textArray[i]) for i in range(len(textArray))]
	for key in newNameDict:
		fileName = directory + key + f[4:-4] + ".csv"
		writeFile = open(fileName, "w")
		text = "\n".join([textArray[i] for i in newNameDict[key]])
		writeFile.write(text)
		writeFile.close()
		print("Completed writing file " + fileName)
		os.system("rm " + directory + f)
			
for f in otherFileList:
	fileName = directory + f
	contents = open(fileName)
	text = contents.read()
	text = text.replace("\r", "\n")
	textArray = text.split("\n")
	if textArray[-1] == '':
		textArray = textArray[:-1]

	textArray = [re.split(''' (?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', textArray[i]) for i in range(len(textArray))]
	textArray = [",".join(textArray[i]) for i in range(len(textArray))]
	text = "\n".join(textArray)

	fileName = directory + f[:-4] + ".csv"
	writeFile = open(fileName, "w")
	writeFile.write(text)
	writeFile.close()
	print("Completed writing file " + fileName)
	os.system("rm " + directory + f)
	
for fileName in os.listdir(directory):
	underscores = [m.start() for m in re.finditer(r"_", fileName)]
	novaName, author, regime, datatype = "", "", "", ""

	try:
		novaName = fileName[:underscores[1]]
		author = fileName[underscores[1]+1:underscores[2]]
		regime = fileName[underscores[2]+1:underscores[3]]
		datatype = fileName[underscores[3]+1:re.search(r"\.", fileName).start()]
	except (IndexError, AttributeError):
		print(fileName + " is not a valid file")
		continue
	
	try:
		index = re.search(r"\d+", datatype).start()
		x = int(datatype[index:])
	except AttributeError:
		datatype = datatype
	
	#if not os.path.exists("../Individual_Novae/" + novaName):
	#	os.system("python3 MakeNewNovaDirectory.py " + novaName)
	
	os.rename("DataToImport/" + fileName, "DataHolder/" + fileName)#directory + fileName, "../Individual_Novae/" + novaName + "/Data/" + fileName)


