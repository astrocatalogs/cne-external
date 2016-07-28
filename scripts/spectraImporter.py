import os
import os.path
import re
from astropy.io import fits
from astropy.time import Time
from tqdm import tqdm

directory = "Spectra"

author = "Williams"
dataType = "Spectra"
regime = "Optical"

def get_dec_digits(float_num):
	eps = 10.0 ** -10
	i = 0
	while True:
		ans = float_num / (10.0 ** i)
		ans = int(ans + 0.5) - ans 
		print(ans)
		if ans < eps and ans > -eps:
			return -i
		i -= 1

def getNovaName(filePrefix):
	return filePrefix[:-1]

#works only for 1931-2030
def convertDateUTC(date):
	if re.match(r"\d(\d)?[/:\-]\d[/:\-]", date):
		i = re.match(r"\d(\d)?[/:\-]", date).end()
		date = date[:i] + "0" + date[i:]
	if re.match(r"\d[/:\-]\d(\d)?[/:\-]", date):
		date = "0" + date

	year, month, day = "","",""	
	if re.match(r"\d\d[/:\-]\d\d[/:\-]\d\d(\d\d)?$", date):
		year = date[6:] if re.match(r"\d\d[/:\-]\d\d[/:\-]\d\d\d\d$", date) else ("19" + date[6:] if int(date[6:]) > 30 else "20" + date[6:])
		if int(date[3:5]) > 12:
			day = date[3:5]
			month = date[0:2]
		else:
			day = date[0:2]
			month = date[3:5]
	elif re.match(r"\d\d\d\d[/:\-]\d\d[/:\-]\d\d$", date):
		return date
	else:
		raise ValueError("Not a valid date.")		
		return ""
	return ("%s-%s-%s" %(year, month, day))

realNovaNameDict = {}
novaDict = {}

metadataFields = ['FILENAME', 'WAVELENGTH COL NUM', 'FLUX COL NUM', 'FLUX ERR COL NUM', 'FLUX UNITS', 'DATE', 'OBSERVER', 'TELESCOPE', 'INSTRUMENT', 'DISPERSION', 'WAVELENGTH RANGE 1', 'WAVELENGTH RANGE 2']

ticketDataFields = ["OBJECT NAME: ", "FLUX UNITS: ", "FLUX ERROR UNITS: ", "WAVELENGTH REGIME: ", "TIME SYSTEM: ", "ASSUMED DATE OF OUTBURST: ", "REFERENCE: ", "BIBCODE: ", "DEREDDENED FLAG: ", "METADATA FILENAME: ", "FILENAME COLUMN: ", "WAVELENGTH COLUMN: ", "FLUX COLUMN: ", "FLUX ERROR COLUMN: ", "FLUX UNITS COLUMN: ", "DATE COLUMN: ", "TELESCOPE COLUMN: ", "INSTRUMENT COLUMN: ", "OBSERVER COLUMN: ", "SNR COLUMN: ", "DISPERSION COLUMN: ", "RESOLUTION COLUMN: ", "WAVELENGTH RANGE COLUMN: ", "TICKET STATUS: "]

for filename in tqdm(os.listdir(directory), desc='Processing Spectra'):
	if re.search(".fits?$", filename, re.IGNORECASE):
		if filename.lower().startswith("lmc"):
			continue

		filePrefix = filename[:re.search(".fits?$", filename, re.IGNORECASE).start()]	
		novaName = getNovaName(filePrefix)
		fitsFile = fits.open(directory + "/" + filename)
	
		spectra = fitsFile[0]
		header = spectra.header

		_date = header["DATE-OBS"]
		if filename == "V2214OPF.FIT":
			_date = "09-06-88"
		if filename == "V2214OPM.FIT":
			_date = "25-07-88"
		_time = header["UT"].strip()
	
		_time = "0" + _time if re.match("r\d:", _time) else _time
		try:		
			_date = _date.replace(" ", "")
			_date = convertDateUTC(_date)
		except ValueError:
			print(_date, _time)
		dateTime = _date + "T" + _time
		try:
			t = Time(dateTime, "isot")
			date = t.jd
		except ValueError:
			print(filename)
			print(_date, _time, dateTime)
			continue
		#match = re.match(r"[\d\-/]+[Tt]", dateTime)
		#date = dateTime[:match.end()] if match else ""	
		
		string = ""
		data = spectra.data
			
		for i in range(header["NAXIS1"]):			
			wavelength = header["CRVAL1"] + (header["CRPIX1"] - 1 + i) * header["CDELT1"]
			string += "%s,%s\n" %("{:.5f}".format(wavelength),"{:.5}".format(data[i])) 
		
		outputFile = "%s_%s_%s_%s.csv" %(filePrefix, author, regime, dataType)

		wl0, wln = wavelength = '{:.5f}'.format(header["CRVAL1"] + (header["CRPIX1"] - 1) * header["CDELT1"]), '{:.5f}'.format(header["CRVAL1"] + (header["CRPIX1"] - 2 + header["NAXIS1"]) * header["CDELT1"])
		disp = header["CDELT1"]
		
		realNovaName = ""
		if novaName not in realNovaNameDict:
			sure = False
			while not sure:	
				realNovaName = input(novaName + "'s real name: ", )
				sure = True if input("Are you sure? [Y/N]: ") in ["Y", "y"] else False
				realNovaNameDict[novaName] = realNovaName
		else:
			realNovaName = realNovaNameDict[novaName]

		if not os.path.exists("../Individual_Novae/" + realNovaName):
			os.system("python3 MakeNewNovaDirectory.py " + realNovaName)

		if realNovaName not in novaDict:
			novaDict[realNovaName] = [(outputFile, '{:.6}'.format(date), disp, wl0, wln)]
		else:
			novaDict[realNovaName].append((outputFile, '{:.6}'.format(date), disp, wl0, wln))	

		string = string[:-1]
		csvFile = open("../Individual_Novae/" + realNovaName + "/Data/" + outputFile, "w")
		csvFile.write(string)
		csvFile.close()
				
			
for realNovaName in novaDict:
	string = "#" + ",".join(metadataFields) + "\n"
	
	sure = False
	
	for fileName in novaDict[realNovaName]:
		string += ",".join([fileName[0],'0','1','NA','ergs/cm^2/sec',str(fileName[1]),'Williams','CTIO 1 m','2D-Frutti',str(fileName[2]), str(fileName[3]), str(fileName[4])]) + "\n"
	string = string[:-1]
	
	metadataFilename = "%s_%s_%s_%s_MetaData.csv" %(realNovaName, author, regime, "Spectra")
	metadataFile = open("../Individual_Novae/" + realNovaName + "/Data/" + metadataFilename, "w")
	metadataFile.write(string)
	metadataFile.close()

	ticketFields = [realNovaName, "NA", "NA", regime, "JD", "NA", "Williams et al. (1992)", "1992AJ....104..725W", "False", metadataFilename, "0", "1", "2", "3", "4", "5", "7", "8", "6", "NA", "9", "NA", "10,11", "Completed"]
	
	ticketText = ""
	for i in range(len(ticketDataFields)):
		ticketText += ticketDataFields[i] + ticketFields[i] + "\n"
	ticketText = ticketText[:-1]

	author = ticketFields[6].lstrip().split()[0].replace(",", "")
	regime = ticketFields[3].replace(" ", "")
	ticketFilename = "%s_%s_%s_%s.txt" %(realNovaName, author, regime, "Spectra")
		
	ticketFile = open("../Individual_Novae/" + realNovaName + "/Tickets/CompletedTickets/" + ticketFilename, "w")
	ticketFile.write(ticketText)
	ticketFile.close()
	

