#ONC/scripts/softlinkTickets.py
#soft links tickets in individual novae directories
#6/28/16

import os

for directoryName in os.listdir("../Individual_Novae"):
	if "." not in directoryName:
		for ticketType in ["CompletedTickets", "PendingTickets"]:
			for fileName in os.listdir("../Individual_Novae/" + directoryName + "/Tickets/" + ticketType):
				dest = "../Tickets/" + ticketType + "/" + fileName
				if not (os.path.exists(dest) or fileName.lower() == "blankreadme.txt"):
					if os.path.lexists(dest):
						os.remove(dest)

					try:
						os.symlink("../../Individual_Novae/" + directoryName + "/Tickets/" + ticketType + "/" + fileName, dest)
					except FileExistsError:
						print("There was a problem soft-linking " + fileName)

			for fileName in os.listdir("../Tickets/" + ticketType):
				if not os.path.exists("../Tickets/%s/%s" %(ticketType, fileName)):
					os.remove("../Tickets/%s/%s" %(ticketType, fileName))

os.system("git add ..")

