#ticketCreator.py
#creates tickets for the ONC
#Max Morehead
#6/21/16



#generate correct ticket
validtype = True
while validtype:
	datatype = input("DATATYPE: ")	
	if datatype[0] in ["P","p"]:
		datatype = "Photometry"
		dataFields = ["OBJECT NAME: ", "TIME UNITS: ", "FLUX UNITS: ",  "FLUX ERROR UNITS: ", "FILTER SYSTEM: ", "MAGNITUDE SYSTEM: ", "WAVELENGTH REGIME: ", "TIME SYSTEM: ", "ASSUMED DATE OF OUTBURST: ", "TELESCOPE: ", "OBSERVER: ", "REFERENCE: ", "BIBCODE: ", "DATA FILENAME: ", "TIME COLUMN NUMBER: ", "FLUX COLUMN NUMBER: ", "FLUX ERROR COLUMN NUMBER: ", "FILTER/FREQUENCY/ENERGY RANGE COLUMN NUMBER: ", "UPPER LIMIT FLAG COLUMN NUMBER: ", "TELESCOPE COLUMN NUMBER: ", "OBSERVER COLUMN NUMBER: ", "FILTER SYSTEM COLUMN NUMBER: ", "TICKET STATUS: "]
	elif datatype[0] in ["S","s"]:
		dattype = "Spectra"
		dataFields = ["OBJECT NAME: ", "FLUX UNITS: ", "FLUX ERROR UNITS: ", "WAVELENGTH REGIME: ", "TIME SYSTEM: ", "ASSUMED DATE OF OUTBURST: ", "REFERENCE: ", "BIBCODE: ", "DEREDDENED FLAG: ", "METADATA FILENAME: ", "FILENAME COLUMN: ", "WAVELENGTH COLUMN: ", "FLUX COLUMN: ", "FLUX ERROR COLUMN: ", "FLUX UNITS COLUMN: ", "DATE COLUMN: ", "TELESCOPE COLUMN: ", "INSTRUMENT COLUMN: ", "OBSERVER COLUMN: ", "SNR COLUMN: ", "DISPERSION COLUMN: ", "RESOLUTION COLUMN: ", "WAVELENGTH RANGE COLUMN: ", "TICKET STATUS: "]
 
	else:
		continue
	validtype = False


	
ticketText = ""
userInput = []
length = []
for i in range(len(dataFields)):
	userInput.append(0)
	length.append(0)

i = 0
directory =""
while i < len(dataFields):
	userInput[i] = input(dataFields[i])
	if userInput[i] in ["goback", "Goback", "go_back", "Go_back"]:
		if i == 0:	
			print("You can't go back now. This is the first field.")
		else:
			ticketText = ticketText[0:-length[i-1]]
			i -= 1
	else:
		if i == len(dataFields) - 1:
			if userInput[i][0] in ["C", "c"]:
				directory = "CompletedTickets"
			elif userInput[i][0] in ["P", "p"]:
				directory = "PendingTickets"
			else:
				continue
		length[i] = len(dataFields[i]) + len(userInput[i])
		ticketText = ticketText + dataFields[i] + userInput[i] + "\n"			
		i += 1
	
ticketText = ticketText[:-1]

if datatype == "Photometry":
	author = userInput[11].strip().split()[0].replace(",", "")
	novaName = userInput[0].strip().replace(" ", "_")
	regime = userInput[6].replace(" ", "")
if datatype == "Spectra":
	author = userInput[6].strip().split()[0]
	regime = userInput[3].replace(" ", "")
	novaName = userInput[0].replace(" ", "")
print(author)
	
myFile = open("../Individual_Novae/" + novaName + "/Tickets/" + directory + "/" + novaName + "_" + author + "_" + regime + "_" + datatype + ".txt", "w")
myFile.write(ticketText)
myFile.close()

