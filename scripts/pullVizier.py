from astroquery.vizier import Vizier
from tqdm import tqdm
import re
import os
import os.path
#from .utils import convert_line_bands, convert_jd, get_dec_digits

_o = "Optical"
_ir = "Infrared"
_s = "Spectra"
_p = "Photometry"

#put catalogs in here
#dictionary with catalog names as keys list with [novaName ,author, regime, datatype, telescope, observer, reference, bibcode]
#novaName is MULT if multiple nova

catalogs={"J/AJ/140/34/table2": ["MULT", "Strope", _o, _p, "NA", "AAVSO", "Strope et. al (2010)", "2010AJ....140...34S"], "J/ApJS/187/275/mags": ["MULT", "Schaefer", _o, _p, "NA", "NA", "Schaefer (2010)", "2010ApJS..187..275S"], "J/other/NewA/27.25": ["KT_Eri", "Munari", _o, _p, 'INAF Observatories', "Munari", "Munari & Dallaporta (2014)", "2014NewA...27...25M"], "J/MNRAS/435/771": ["V959_Mon", "Munari", _o, _p, 'INAF Observatories', "Munari", "Munari et. al (2013)", "2013MNRAS.435..771M"], "J/MNRAS/387/344": ["V2615_Oph", "Munari", _o, _p, 'INAF Observatories', "Munari", "Munari et. al (2008)", "2008MNRAS.387..344M"]} 


#"J/A+A/452/567": ["V477_Sct", "Munari", _o, _s], "J/A+A/492/145": ["V2362_Cyg", "Munari", _o, _p], "J/A+A/434/1107/photom": ["V838_Mon", "Munari", _o, _p]}
directory = "DataToImport"


def write_ticket(filename, ticket_fields):
	ticket_data_fields = ["OBJECT NAME: ", "TIME UNITS: ", "FLUX UNITS: ",  "FLUX ERROR UNITS: ", "FILTER SYSTEM: ", "MAGNITUDE SYSTEM: ", "WAVELENGTH REGIME: ", "TIME SYSTEM: ", "ASSUMED DATE OF OUTBURST: ", "TELESCOPE: ", "OBSERVER: ", "REFERENCE: ", "BIBCODE: ", "DATA FILENAME: ", "TIME COLUMN NUMBER: ", "FLUX COLUMN NUMBER: ", "FLUX ERROR COLUMN NUMBER: ", "FILTER/FREQUENCY/ENERGY RANGE COLUMN NUMBER: ", "UPPER LIMIT FLAG COLUMN NUMBER: ", "TELESCOPE COLUMN NUMBER: ", "OBSERVER COLUMN NUMBER: ", "FILTER SYSTEM COLUMN NUMBER: ", "TICKET STATUS: "]
	if len(ticket_data_fields) != len(ticket_fields):
		raise ValueError("Ticket fields list is wrong length.")
		return
	string = ''
	for i in range(len(ticket_data_fields)):
		string += ticket_data_fields[i] + ticket_fields[i] + "\n"
	string = string[:-1]		
	
	with open(filename, "w") as ticket_file:
		ticket_file.write(string)
		ticket_file.close()

	return 0

def convert_jd(contentsList, increase=2450000, **kwargs):
	"""Inputs a list of list of file contents, adds increase to JD column """
	manual = False if increase >= 2400000 and increase <= 2500000 else True
	
	zeros = len(str(increase)) - re.search(r"0*$", str(increase)).start()
		
	def digits(x):
		i = 0
		while True:
			if int(x) // (10 ** i) == 0:
				return i
			else:
				i += 1
	
	index = -1
	if "jdCol" in kwargs:
		index = kwargs[jdCol]
	else:
		for line in contentsList:
			for i in range(len(line)):
				if re.search(r"(jd)|(julian)",line[i], re.IGNORECASE):
					index = i
					break
			if index != -1:
				break
	if index == -1:
		raise ValueError("Could not find JD column.")
		return contentsList
	
	longJd = increase
	for i in range(len(contentsList)):
		if contentsList[i][0].strip().startswith("#"):
			continue
		try:
			dec_digits = str(get_dec_digits(contentsList[i][index]))
			mjd = float(contentsList[i][index].strip())
		except IndexError:
			continue

		if digits(mjd) >= 4:
			if digits(mjd) == 4: mjd += increase
			elif digits(mjd) == 5 and not manual: mjd += 2400000
			elif digits(mjd) == 5 and manual: mjd += increase
			elif digits(mjd) == 6: mjd += 2000000
			longJd = mjd
		else:
			mjdDigits = digits(mjd)
			if zeros > mjdDigits:	
				power = 10 ** mjdDigits
				mjd += (longJd // power) * power
			else:
				mjd += increase

		
		contentsList[i][index] = ("{:.%sf}" %(dec_digits)).format(mjd)
			
	return contentsList

def get_dec_digits(string):
	
	for i in range(len(string)):
		if string[i] == '.':
			return len(string) - i - 1

	return 0


def convert_line_bands(line, titles):
	bands = r'UBVRI'
	mag_dict = {}
	error_dict, error = {}, False
	
	col_set = set([])
	for i, title in enumerate(titles):
		title = title.upper().replace('_', '').replace(' ', '')
		for band in bands:
			if re.match(r'%sC?MAG' %(band), title):
				x = re.search(r'MAG', title).start()
				mag_dict[title[:x]] = line[i].strip()
				col_set.add(i)
				for (j,t) in enumerate(titles):
					t = t.upper()
					if re.match(r'E_?%sC?MAG' %(band), t):
						error = True
						x = re.search(r'MAG', t.replace("_", '')).start()
						error_dict[t.replace("_", '')[1:x]] = line[j].strip()
						col_set.add(j)


	for i, title in enumerate(titles):
		title = title.upper().replace(" ", "")
		
		if re.match(r'[%s]C?[\-_][%s]C?$' %(bands, bands), title):
			x = re.search(r'[\-_][%s]' %(bands), title).start()
			band1 = title[:x]
			band2 = title[x+1:]
			try:
				subtrahend = mag_dict[title[x + 1:]]
				band = title[:x]
				not_band = title[x+1:]
			except KeyError:
				subtrahend = mag_dict[title[:x]]
				band = title[x+1:]
				not_band = title[:x]
				
			minuend = line[i].strip()
			
			decs1 = get_dec_digits(minuend)
			decs2 = get_dec_digits(subtrahend)
			decs = decs1 if decs1 > decs2 else decs2
			if not title[0:x] in mag_dict:
				try: mag_dict[title[0:x]] = ('{:.%df}' %(decs)).format(float(subtrahend) + float(minuend))
				except ValueError: mag_dict[title[0:x]] = minuend
			elif not title[x+1] in mag_dict:
				try: mag_dict[title[x+1:]] = ('{:.%df}' %(decs)).format(float(subtrahend) - float(minuend))
				except ValueError: mag_dict[title[x+1:]] = minuend
		
			col_set.add(i)
			
			for (j,t) in enumerate(titles):
				t = t.upper()
				if re.match(r'E_?[%s]C?[\-_][%s]C?$' %(band1, band2), t):
					error = True
					try:
						if not_band in error_dict and float(error_dict[not_band]) > float(line[j].strip()):
							error_dict[band] = error_dict[not_band]
						else:
							error_dict[band] = line[j].strip()
					except (ValueError, KeyError):
						error_dict[band] = line[j].strip()
					col_set.add(j)
	
	if len(col_set) > 0:
		line_list = []
		for band in mag_dict:
			new_line = []
			for i in range(len(line)):
				if not i in col_set:
					new_line.append(line[i])

			new_line.append(mag_dict[band])
			if error:
				try:
					new_line.append(error_dict[band])
				except KeyError:
					new_line.append('--')
			new_line.append(band)

			line_list.append(new_line)
	else:
		line_list = [line]
	
	new_titles = []
	for i in range(len(titles)):
		if not i in col_set: new_titles.append(titles[i])
	if len(col_set) > 0:
		new_titles.append('Mag')
		if error:
			new_titles.append('e_Mag')
		new_titles.append('Band')
		

	return (line_list, new_titles)

		
		
#for catalog in catalogs:
#	
#	catalogs[catalog].append(input("Reference: "))
##	catalogs[catalog].append(input("Bibcode: "))
#	catalogs[catalog].append(input("Time Col: "))
#	catalogs
	
#v = Vizier(columns = ['Vmag','B-V','U-B','V-Rc','Rc-Ic','e_Vmag','e_B-V','e_U-B','e_V-Rc','e_Rc-Ic']


keys = []

Vizier.ROW_LIMIT = -1

if not os.path.exists(directory):
	os.mkdir(directory)

for page in catalogs:
	keys.append(page)

#v = Vizier(columns=['Name','Nova','JD', 'Band', 'mag', 'e_mag', 'Source'])

dataTables = Vizier.get_catalogs(keys)
keys = dataTables.keys()

keyRepeatDict = {}

filename_dict = {}
for key in keys:
	if key not in keyRepeatDict:
		keyRepeatDict[key] = 0
	else:
		keyRepeatDict[key] += 1

	names = ()
	for catalogKey in catalogs:
		if re.search(catalogKey.replace("+", "\+").replace(".", "\."), key):
			names = catalogs[catalogKey]
		
	if names == []:
		print("Error with catalog " + catalogKey)
		continue
	
	name = "%s_%s_%s_%s" %tuple(names[:4])
	name += ("" if keyRepeatDict[key] == 0 else str(keyRepeatDict[key]))
	name += ".dat"
	filename_dict[name] = str(key)

	data = dataTables[key]
	data.write(os.path.join(directory, name), format = "ascii")
	print("Completed writing "  + name)


fileSplitList = []
otherFileList = []

for fileName in os.listdir(directory):
	if re.match("MULT", fileName, re.IGNORECASE):
		fileSplitList.append(fileName)
	else:
		if fileName.endswith('.dat'):
			otherFileList.append(fileName)


for f in fileSplitList:
	novaNameCol = -1
	fileName = os.path.join(directory, f)
	contents = open(fileName)
	text = contents.read()
	text = text.replace("\r", "\n")
	textArray = text.split("\n")
	if textArray[-1] == '':
		textArray = textArray[:-1]

	textArray = [re.split(''' (?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', textArray[i]) for i in range(len(textArray))]
	textArray = [[word.strip().replace('"', '') for word in line] for line in textArray]
	if not textArray[0][0].startswith('#'):
		textArray[0][0] = '#' + textArray[0][0]	
	titles = textArray[0]	

	textArray = convert_jd(textArray)

	t = convert_line_bands(textArray[1], titles)
	separate_band_arr = [t[1]] + t[0]
	
	for i in tqdm(range(2, len(textArray)), desc=f):
		separate_band_arr += convert_line_bands(textArray[i], titles)[0]
		
	titles = t[1]
	textArray = separate_band_arr
	

	if not titles[0].startswith("#"):
		titles[0] = "#" + titles[0]

	for i in range(len(titles)):
		if re.search(r"(nova)|(name)", titles[i].lower()):
			novaNameCol = i
			break

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
	key = filename_dict[f]
	try:
		names = catalogs[key]
	except KeyError:
		for i in range(len(key)):
			if key[-i] == '/':
				names = catalogs[key[:-i]]
				break



	flux_col, flux_err_col, band_col, time_col, observ_col = 'NA','NA','NA','NA','NA'
	for i, title in enumerate(titles):
		title = title.lower()
		if i == 0: title = title[1:]
		if title.startswith('mag'): flux_col = str(i)
		if re.match(r'e_?mag', title): flux_err_col = str(i)
		if re.match(r'band', title): band_col = str(i)
		if re.search(r'jd', title): time_col = str(i)
		if re.match(r'(source)|(observer)', title): observ_col = str(i)
	

	for key in newNameDict:
		if not os.path.exists("../Individual_Novae/" + key):
			os.system("python3 MakeNewNovaDirectory.py " + key)

		fileName = os.path.join('..', 'Individual_Novae', key, 'Data', key + f[4:-4] + ".csv")
		writeFile = open(fileName, "w")
		text = "\n".join([",".join(titles)] + [textArray[i] for i in newNameDict[key]])
		writeFile.write(text)
		writeFile.close()

		
		
		ticket_fields = [key, "JD", "Mags", "Mags", "Johnson-Cousins", "Vega", "Optical", "JD", "NA", names[4], names[5], names[6], names[7], os.path.split(fileName)[-1], time_col, flux_col, flux_err_col, band_col, "NA", "NA", observ_col, "NA", "Completed"]
		write_ticket(os.path.join('..', 'Individual_Novae', key, "Tickets", 'CompletedTickets', key + f[4:-4] + '.txt'), ticket_fields)
		print("Completed writing file " + fileName)

	

	

	os.remove(os.path.join(directory, f))
			
for f in otherFileList:
	fileName = os.path.join(directory, f)
	contents = open(fileName)
	text = contents.read()
	text = text.replace("\r", "\n")
	textArray = text.split("\n")
	if textArray[-1] == '':
		textArray = textArray[:-1]
	if not textArray[0].startswith("#"):
		textArray[0] = "#" + textArray[0]

	textArray = [re.split(''' (?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', textArray[i]) for i in range(len(textArray))]
	textArray = [[word.strip() for word in line] for line in textArray]
	titles = textArray[0]
	
	textArray = convert_jd(textArray)

	t = convert_line_bands(textArray[1], titles)
	separate_band_arr = [t[1]] + t[0]
	
	
	for i in tqdm(range(2, len(textArray)), desc=f):
		separate_band_arr += convert_line_bands(textArray[i], titles)[0]

	textArray = separate_band_arr
	titles = t[1]

	if not titles[0].startswith('#'):
		titles[0] = '#' + titles[0]
	
	textArray = [",".join(textArray[i]) for i in range(len(textArray))]
	text = "\n".join(textArray)

	key = filename_dict[f]
	try:
		names = catalogs[key]
	except KeyError:
		for i in range(len(key)):
			if key[-i] == '/':
				names = catalogs[key[:-i]]
				break

	flux_col, flux_err_col, band_col, time_col, observ_col = 'NA','NA','NA','NA','NA'
	for i, title in enumerate(titles):
		title = title.lower()
		if i == 0: title = title[1:]
		if title.startswith('mag'): flux_col = str(i)
		if re.match(r'e_?mag', title): flux_err_col = str(i)
		if re.match(r'band', title): band_col = str(i)
		if re.search(r'jd', title): time_col = str(i)
		if re.match(r'(source)|(observer)', title): observ_col = str(i)

	novaName = names[0]

	if not os.path.exists("../Individual_Novae/" + novaName):
		os.system("python3 MakeNewNovaDirectory.py " + novaName)

	fileName = os.path.join('..', 'Individual_Novae', novaName, 'Data', f[:-4] + ".csv")
	writeFile = open(fileName, "w")
	writeFile.write(text)
	writeFile.close()

	
		
	ticket_fields = [novaName, "JD", "Mags", "Mags", "Johnson-Cousins", "Vega", "Optical", "JD", "NA", names[4], names[5], names[6], names[7], os.path.split(fileName)[-1], time_col, flux_col, flux_err_col, band_col, "NA", "NA", observ_col, "NA", "Completed"]
	write_ticket(os.path.join('..', 'Individual_Novae', novaName, "Tickets", 'CompletedTickets', f[:-4] + '.txt'), ticket_fields)

	print("Completed writing file " + fileName)
	os.remove(os.path.join(directory, f))





	
	#os.rename("DataToImport/" + fileName, "DataHolder/" + fileName)#os.path.join(directory + fileName), "../Individual_Novae/" + novaName + "/Data/" + fileName)


