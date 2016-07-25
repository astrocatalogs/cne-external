import os

# for file_name in os.listdir("Data"):
file_name = input("AAVSO Data Filename: ")
data = open(file_name, "r")

filters = ["U", "B", "V", "R", "I", "J", "H", "K", "TG", "TB", "TR", "CV", "CR", "SZ", 
"SU", "SG", "SR", "SI", "STU", "STV", "STB", "STY", "STHBW", "STHBN", "MA", "MB", "MI",
"HA", "HAC", "Vis."]
string = []
while True:
	
	lim_flag = 0
	filter_flag = 0
	line = data.readline()
	if not line:
		break
	cols = line.split(",")
	
	try:
		for char in cols[1]:
			if char == "<":
				cols[1] = cols[1][1:]
				lim_flag += 1
	except IndexError:
		continue

	if cols[4] not in filters:
		filter_flag += 1
		
	if lim_flag == 1:
		cols[1] += ",1"
	else:
		cols[1] += ",0"
	
	line = ",".join(cols)
	
	if filter_flag == 0:
		string.append(line)

data.close()

string = "".join(string)

data = open(file_name, "w")
data.write(string)
data.close()
