import re

def convertJd(contentsList, increase=2400000, **kwargs):
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
	print(index)
	longJd = increase
	for i in range(len(contentsList)):
		if contentsList[i][0].strip().startswith("#"):
			continue
		try:
			mjd = float(contentsList[i][index].strip())
		except IndexError:
			print(contentsList[i])
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

		contentsList[i][index] = "{:.6f}".format(mjd)
			
	return contentsList

myFile = open("document-3.csv", "r")
contents = myFile.read()

contents = contents.split("\n")
contents = [line.split(",") for line in contents]
myFile.close()
while contents[-1] == ['']:
	contents = contents[:-1]

print(convertJd(contents, increase=2440000))



