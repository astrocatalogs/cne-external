#extractPdfData.py
#finds tables in Pdf, converts to csv

from PIL import Image
import os
import os.path
import re
import subprocess
from threading import Thread
from asyncio import Queue
import sys

defaultPdfList = []
#enter pdfs here or use one of below methods (input prompt or command line argument)
defaultPdfList = ["V723Cas_test.pdf[15]", "V723Cas_test.pdf[16]"]

pdfList = []
if len(sys.argv) > 1:
	for i in range(1, len(sys.argv)):
		pdfList.append(sys.argv[i])

else:
	firstString = "skip"
	while True:
		pdfList.append(input("Enter a pdf name (or press enter to %s): " %(firstString,)))
		firstString = "continue"
		if pdfList[-1] == "":
			pdfList = pdfList[:-1]
			break

if pdfList == []:
	pdfList = defaultPdfList


class Line:
	def __init__(self, x1, y1, x2, y2, color):
		self.x1 = x1
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2
		self.vert, self.horiz, self.length, self.thickness = (True, False, y2-y1+1, x2-x1+1) if y2-y1 > x2-x1 else (False, True, x2-x1+1, y2-y1+1)
		self.color = color.lower()
		self.avgx = (x2 + x1) // 2
		self.avgy = (y2 + y1) // 2
		
	def __add__(self, l):
		yspan = range(self.y1-1, self.y2+2)
		xspan = range(self.x1-1, self.x2+2)
		if (l.y1 in yspan or l.y2 in yspan or l.avgy in yspan) and (l.x1 in xspan or l.x2 in xspan or l.avgx in xspan) and l.vert == self.vert and self.color == l.color:
			if l.length + 20 > self.length and self.length - 20 < l.length:
				return Line(min(self.x1,l.x1), min(self.y1,l.y1), max(self.x2,l.x2), max(self.y2,l.y2), self.color)
			else:
				return (self if self.length >= l.length else l)
		else:
			raise ValueError("These lines cannot be added.")

	def __str__(self):
		return str((self.x1, self.y1, self.x2, self.y2))

	def __repr__(self):
		return str((self.x1, self.y1, self.x2, self.y2))

	def cmpKey(self):
		return (self.avgx if self.vert else self.avgy)

def findPages(string):
	rangeList = [i.replace(" ", "") for i in string.split(",")]
	pageSet = set([])
	for value in rangeList:
		if value != "":
			match = re.match(r"\d+-\d+$", value)
			if match:
				dash = re.search(r"-", value).start()
				lower, upper = int(value[:dash]), int(value[dash+1:])
				if lower <= upper:
					for i in range(lower, upper + 1):
						pageSet.add(i)
				
				else:
					raise AttributeError("Incorrectly formatted page range.")
			elif re.match(r"\d+$", value):
				pageSet.add(int(value))
			else:
				raise AttributeError("Incorrectly formatted page range.")
	return pageSet

	
def convertPdf(pdf, density=500):
	try:
		sufIndex = re.search(r".pdf((\[[\d,\-]+\]$)|$)",pdf).start()
		suffix = pdf[sufIndex+4:]
		suffix = suffix if suffix == "" else "-" + suffix[1:-1]
		pdfPrefix = pdf[:sufIndex]
	except AttributeError:
		print(pdf + " is not a valid pdf name")
		return 1
	destName = "__working/%s%s.pbm" %(pdfPrefix, suffix)
	subprocess.run("convert -density %s -depth 1 %s %s" %(str(density), pdf, destName), shell=True)
	
def convertPdfs(pdfList, threads=4):
	newPdfList = []
	pdfPageList = []
	for pdf in pdfList:
		try:
			close = re.search("\]", pdf)
			if close:
				start = re.search(r".pdf((\[[\d,\-]+\]$)|$)", pdf).start() + 5
				end = close.start()
				pageSet = findPages(pdf[start:end])
				for i in pageSet:
					pdfPageList.append(pdf[:start] + str(i) + "]")
			else:
				pdfPageList.append(pdf)
		except AttributeError:
			print(pdf + " is not a valid pdf name")
	
	for i in range(0,len(pdfPageList),threads):
		try:		
			newPdfList.append(tuple(pdfPageList[i:i+threads]))
		except IndexError:
			newPdfList.append(tuple(pdfPageList[i:]))
	for pdfTuple in newPdfList:
		threads = [Thread(target=convertPdf, args=(pdfTuple[i],)) for i in range(0,len(pdfTuple))]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()

def get_hlines(pix, w, h, color="black", H_THRESH = 1000, black_thickness = 0):
	"""Finds horizontal lines, returns list of Line objects"""
	pixMatch = 0
	color = color.lower()
	if color == "white":
		pixMatch = 255
	hlines = []
	y = 0
	while y < h:
		_y = y		
		black, adjust, x, _x = (0,0,0,0)
		not_moved = True
		while x < w:
			if pix[x,y] == pixMatch:				
				if black == 0:
					x1 = x
				black += 1
				if x == w - 1:
					if black > H_THRESH:
						hlines.append(Line(x1, _y, x, y, color))
					black = 0
					y += adjust
					#x = x if not_moved else _x + 2
					adjust = 0
					not_moved = True

			elif black != 0 and color != "white":   			
				if [x,y+1] == pixMatch:
					black += 1
					y += 1
					adjust -= 1
				elif [x,y-1] == pixMatch:
					black += 1
					y -= 1
					adjust += 1
				else:
					if black > H_THRESH:
						hlines.append(Line(x1, _y, x, y, color))
					black = 0
					y += adjust
					#x = x if not_moved else _x + 2
					adjust = 0
					not_moved = True
				if not_moved:
					_x = x
					not_moved = False
			elif color == "white":
				if x + black_thickness < w and black != 0 and pix[x + black_thickness, y] == pixMatch:
					x += black_thickness + 2
					black += black_thickness + 2
				elif black > H_THRESH:
					hlines.append(Line(x1, _y, x, y, color))
					black = 0
				else:
					black = 0
				
			x += 1
		y += 1
	if len(hlines) != 0:
		lineList = [hlines[0]]
		for i in range(1, len(hlines)):
			try:
				templ = lineList[-1] + hlines[i]
				lineList[-1] = templ
			except ValueError:
				lineList.append(hlines[i])
	else:
		lineList = []
	
	return lineList

def get_vlines(pix, w, h, color="black", V_THRESH = 1000, black_thickness = 0):
	"""Finds vertical lines, returns list of Line objects"""	
	pixMatch = 0
	color = color.lower()
	if color == "white":
		pixMatch = 255
	vlines = []
	x = 0
	while x < w:
		_x = x		
		black, adjust, y, _y = (0,0,0,0)
		not_moved = True
		while y < h:
			if pix[x,y] == pixMatch:				
				if black == 0:
					y1 = y
				black += 1
				if y == h - 1:
					if black > V_THRESH:
						vlines.append(Line(_x, y1, x, y, color))
					black = 0
					x += adjust
					#y = y if not_moved else _y
					adjust = 0
					not_moved = True	

			elif black != 0 and color != "white":
				if [x+1,y] == pixMatch:
					black += 1
					x += 1
					adjust -= 1
				elif [x-1,y] == pixMatch:
					black += 1
					x -= 1
					adjust += 1
				else:
					if black > V_THRESH:
						vlines.append(Line(_x, y1, x, y, color))
					black = 0
					x += adjust
					#y = y if not_moved else _y
					adjust = 0
					not_moved = True
				if not_moved:			
					_y = y
					not_moved = False

			elif color == "white":
				if y + black_thickness < h and black != 0 and pix[x, y + black_thickness + 1] == pixMatch:				
					y += black_thickness + 1
					black += black_thickness + 1		
				elif black > V_THRESH:
					vlines.append(Line(_x, y1, x, y, color))
					black = 0
				else:
					black = 0
		
			y += 1
		x += 1
	if len(vlines) != 0:
		lineList = [vlines[0]]
		for i in range(1, len(vlines)):
			try:
				templ = lineList[-1] + vlines[i]
				lineList[-1] = templ
			except ValueError:
				lineList.append(vlines[i])
	else:
		lineList = []

	return lineList


def findTables(hlines, width, ROW_THRESH = 250):
	""" Finds the tables from a list of horizontal line, with rows smaller than ROW_THRESH
		Returns a list of tuples, with each tuple representing the table dimensions	and the lines which the table includes	"""
	tableList = []
	nextTable = []
	start = 0
	for i in range(len(hlines)):
		line = hlines[i]
		if nextTable == []:
			nextTable = [line.x1 - 100, line.y1, line.x2 + 100, line.y1]
			row = 0
		else:
			if nextTable[1] + ROW_THRESH > line.y1:
				row += 1
				nextTable[3] = line.y2
			elif row < 3:
				nextTable[3] = line.y2
				row = 3
			else:
				tableList.append(tuple(nextTable) + (start, i))
				nextTable = [line.x1 - 100, line.y1, line.x2 + 100, line.y1]
				row = 0
	if nextTable != [] and nextTable[1] != nextTable[3]:
		tableList.append(tuple(nextTable) + (start, len(hlines)-1))
	return tableList


def processImage(imageFile):
	im = Image.open(imageFile)
	im = im.convert("1")
	pix = im.load()
	width, height = im.size
	table_lines = get_hlines(pix, width, height)
	tables = findTables(table_lines, width)
	
	max_thickness = 0
	for hline in table_lines:
		if hline.thickness > max_thickness:
			max_thickness = hline.thickness 

	for t in range(len(tables)):
		table = tables[t]
		tabIm = im.crop(table[:4])
		w, h = tabIm.size
		tabPix = tabIm.load()
		vlines_black = get_vlines(tabPix, w, h, V_THRESH = h - max_thickness * len(table_lines) - h // 20)
		vlines_white = get_vlines(tabPix, w, h, color = "white", V_THRESH = h - max_thickness * len(table_lines) - h // 20, black_thickness = max_thickness)
		hlines_white = get_hlines(tabPix, w, h, color = "white", H_THRESH = w - 250)
		hlines_black = get_hlines(tabPix, w, h, H_THRESH = w - 250)

		i = 0
		while i < len(vlines_white):
			if vlines_white[i].thickness < w / 50 :
				vlines_white.remove(vlines_white[i])
			else:
				i += 1
	
		hlines = sorted(hlines_black + hlines_white, key = lambda x: x.cmpKey())
		vlines = sorted(vlines_black + vlines_white, key = lambda x: x.cmpKey())
		
		contents = []
		for i in range(len(hlines) - 1):
			contents.append([])
			for j in range(len(vlines) - 1):
				fileName = "%s-%s-%s-%s.pbm" %(imageFile[:-4],t,j,i)
				tabIm.crop((vlines[j].avgx, hlines[i].avgy, vlines[j+1].avgx, hlines[i+1].avgy)).save(fileName)					
				subprocess.run("tesseract %s %s" %(fileName, fileName[:-4]), shell=True) #stdout=subprocess.PIPE)
				#process.wait()				
				#output, err = process.communicate()
				#if re.search(r"Empty page!!"):
				#	subprocess.run("convert -density 500 -density	
				txtFile = open(fileName[:-4] + ".txt", "r")
				contents[i].append(re.sub(r"_+$", "", txtFile.read().strip().replace(",","_")))
				txtFile.close()
				if contents[i][j] == "":
					subprocess.run("gocr -o %s.txt %s" %(fileName[:-4], fileName), shell=True)
					txtFile = open(fileName[:-4] + ".txt", "r")
					contents[i][j] = re.sub(r"_+$", "", txtFile.read().strip().replace(",","_"))
					txtFile.close()
				

		rows = [(",".join(row)).replace("\n", "") for row in contents]
		for i in range(len(rows)-1,-1,-1):
			if re.match(r"^,+$", rows[i]):
				del rows[i]
		csvText = "\n".join(rows)
		csvFile = open(imageFile[10:-4] + ".csv", "w")
		csvFile.write(csvText)
		csvFile.close()

			#title row unknown
	#	else if table[5] - table[4] == 2:
			#title in first row
		
	#	else if table[5] - table[4] == 3:
	#		#title in first two rows

	#	else:
			#title in first row, rows known
			

def workerTask(q):
	while not q.empty():
		processImage(q.get_nowait()[0])
		q.task_done()
		
if not os.path.exists("__working"):
	os.mkdir("__working")
convertPdfs(pdfList)
q = Queue(maxsize=0)
num_threads = 4

#put files in queue
for fileName in os.listdir("__working"):
	if fileName.endswith(".pbm"):
		q.put_nowait(("__working/" + fileName,))

threads = []
for i in range(num_threads):
	worker = Thread(target=workerTask, args=(q,))
	worker.start()
	threads.append(worker)

q.join()
for thread in threads:
	thread.join()

subprocess.run("rm -r __working", shell=True)

