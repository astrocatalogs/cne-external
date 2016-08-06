from bs4 import BeautifulSoup
import urllib.request
import re
import os.path
import os

directory = "WalterData"

def parseUrl(url, times, directory):		
	try:
		contents = urllib.request.urlopen(url)
	except (urllib.error.HTTPError, ValueError):
		print("Could not open " + url)
		return 1

	soup = BeautifulSoup(contents, "html.parser")

	baseUrl = ""
	for i in range(len(url)-1,-1,-1):
		if url[i] == "/":
			baseUrl = url[:i+1] 
			break
	
	if baseUrl == "": return 2
	
	for link in soup.find_all('a'):	
		linkUrl = link.get('href')
		if linkUrl == None: continue
		
		if re.match(r"(https?://)|(\.\./)|(www\.)", linkUrl):
			True == True
		elif re.match(r"(iicsa\.)|(tad\.)|(txt\.)", linkUrl[::-1].strip()):			
			#download file
			folder = "Spectra" if re.search(r"spec", url, re.IGNORECASE) else "Photometry"
			filename = ""			
			for i in range(len(linkUrl)-1,-1,-1):
				if linkUrl[i] == "/":
					filename = linkUrl[i+1:]
					break
			filename = linkUrl if filename == "" else filename
			
			
			try:
				urllib.request.urlretrieve(baseUrl + linkUrl, directory + "/%s/%s" %(folder,filename))
			except (urllib.error.HTTPError, ValueError):
				print("Problem downloading " + baseUrl + linkUrl)
				continue

		elif re.match(r"(gpe?j\.)|(fig\.)|(gnp\.)", linkUrl[::-1].strip()):	
			#dowload image
			filename = ""			
			for i in range(len(linkUrl)-1,-1,-1):
				if linkUrl[i] == "/":
					filename = linkUrl[i+1:]
					break
			filename = linkUrl if filename == "" else filename
			try:
				urllib.request.urlretrieve(baseUrl + linkUrl, directory + "/%s/%s" %("Images",filename))
			except (urllib.error.HTTPError, ValueError):
				print("Problem downloading " + baseUrl + linkUrl)
				continue
			
		elif "/" in linkUrl and times != 0:
			parseUrl(baseUrl + linkUrl, times - 1, directory)

	return 0

if not os.path.exists(directory): os.mkdir(directory)
if not os.path.exists(directory + "/Images"): os.mkdir(directory + "/Images")
if not os.path.exists(directory + "/Spectra"): os.mkdir(directory + "/Spectra")
if not os.path.exists(directory + "/Photometry"): os.mkdir(directory + "/Photometry")

i = parseUrl("http://www.astro.sunysb.edu/fwalter/SMARTS/NovaAtlas/atlas.html", 4, directory)
