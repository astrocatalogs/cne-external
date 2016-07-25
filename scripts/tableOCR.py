#extractPdfData.py
#finds tables in Pdf, converts to csv

from PIL import Image
import os
import os.path
import re
import subprocess
from threading import Thread
from asyncio import Queue
import argparse


defaultPdfList = []
#enter pdfs here or use one of below methods (input prompt or command line argument)
defaultPdfList = ["V723Cas_test.pdf[15]"]

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--auto", help="Finds table automatically.", action="store_true")
parser.add_argument("filenames", help="Names of files to be processed.", type=str, nargs="*")
parser.add_argument("-z", "--zero", help ="If used, page numbers will index from 0 instead of 1.", action="store_true")
args = parser.parse_args()
pdfList = args.filenames
auto = True if args.auto else False
zero = 0 if args.zero else 1


if pdfList == []:
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
			if l.length + 1000 > self.length and self.length - 1000 < l.length:
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
	global zero
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
						pageSet.add(i - zero)
				
				else:
					raise AttributeError("Incorrectly formatted page range.")
			elif re.match(r"\d+$", value):
				pageSet.add(int(value) - zero)
			else:
				raise AttributeError("Incorrectly formatted page range.")
	return pageSet

	
def convertPdf(pdf, density=900):
	global auto
	try:
		sufIndex = re.search(r".pdf((\[[\d,\-]+\]$)|$)",pdf).start()
		suffix = pdf[sufIndex+4:]
		suffix = suffix if suffix == "" else "-" + suffix[1:-1]
		pdfPrefix = pdf[:sufIndex]
	except AttributeError:
		print(pdf + " is not a valid pdf name")
		return 1
		pdfPrefix = pdf[:-4]
		suffix = ""
	if auto:
		destName = "__working/%s%s.pbm" %(pdfPrefix, suffix)
		subprocess.run("convert -density %s -depth 1 %s %s" %(str(density), pdf, destName), shell=True)
		return 0;

	else:
		destName = "__working/%s%s.png" %(pdfPrefix, suffix)
		Completed = subprocess.run("convert -density %s -depth 1 %s %s" %(str(density), pdf, destName), shell=True, stderr = subprocess.PIPE)
		if Completed.stderr.decode() != '': 
			print("Could not find " + pdf)
			return 1;

		while True:
			subprocess.run("gthumb " + destName, shell=True)
			x = ""			
			while True:
				x = input("Did you crop %s correctly? [Y/N]: " %(pdf,)) 
				if x.strip() in ["Y", "y", "N", "n"]: break
			if x.strip() in ["Y", "y"]: break	
		
		
		subprocess.run("convert -density %s -depth 1 %s %s" %(str(density), destName, destName[:-4] +".pbm"), shell=True)
		os.remove(destName)
		return 0;
	
def convertPdfs(pdfList, threads=4):
	global auto
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
		if auto:
			threads = [Thread(target=convertPdf, args=(pdfTuple[i],)) for i in range(0,len(pdfTuple))]
			for thread in threads:
				thread.start()
			for thread in threads:
				thread.join()
		else:
			for pdfName in pdfTuple:
				convertPdf(pdfName)

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
				if y + black_thickness < h and black != 0 and pix[x, y + black_thickness] == pixMatch:				
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

def OCR(tabIm, hlines, vlines, imageFile, t=""):
	t = "" if t == "" else "-" + t
	
	contents = []	
	for i in range(len(hlines) - 1):
		contents.append([])
		for j in range(len(vlines) - 1):	
			contents[i].append("")

	devnull = open(os.devnull, "w")
	for i in range(len(hlines) - 1):
		print("OCR for row " + str(i))
		for j in range(len(vlines) - 1):
			fileName = "%s%s-%s-%s.pbm" %(imageFile[:-4],t,j,i)
			
			tabIm.crop((vlines[j].avgx, hlines[i].avgy, vlines[j+1].avgx-1, hlines[i+1].avgy-1)).save(fileName)		
					
			subprocess.run("tesseract %s %s" %(fileName, fileName[:-4]), shell=True, stdout=devnull, stderr=devnull) 
				
			txtFile = open(fileName[:-4] + ".txt", "r")
			contents[i][j] = re.sub(r"_+$", "", txtFile.read().strip().replace(",","_").replace('"', ''))
			txtFile.close()
			if contents[i][j] == "":
				subprocess.run("gocr -o %s.txt %s" %(fileName[:-4], fileName), shell=True, stdout=devnull, stderr=devnull)
				txtFile = open(fileName[:-4] + ".txt", "r")
				contents[i][j] = re.sub(r"_+$", "", txtFile.read().strip().replace(",","_"))
				txtFile.close()
			elif re.search("\d+\D*\d+", contents[i][j]):
				contents[i][j] = contents[i][j].replace("?", "7").replace("'", "")
				#if not re.match(r"-?\d+\.?\d+"):
				#	subprocess.run("gocr -o %s.txt %s" %(fileName[:-4], fileName), shell=True)
				#	txtFile = open(fileName[:-4] + ".txt", "r")
				#	temp = re.sub(r"_+$", "", txtFile.read().strip().replace(",","_"))
				#	txtFile.close()
	devnull.close()
			
	rows = [(",".join(row)).replace("\n", "") for row in contents]
	i = 0
	while i < len(rows):
		if re.match(r"^,+$", rows[i]):
			rows = rows[:i] + rows[i+1:]
		else:
			i += 1
	if re.match(r"^,+$", rows[-1]): rows = rows[:-1]

	csvText = "\n".join(rows)
	csvFile = open(imageFile[10:-4] + t + ".csv", "w")
	csvFile.write(csvText)
	csvFile.close()


def processImage(imageFile, autoFind=True):	
	im = Image.open(imageFile)
	im = im.convert("1")
	pix = im.load()
	width, height = im.size
	
	if autoFind:
		table_lines = get_hlines(pix, width, height)
		tables = findTables(table_lines, width, ROW_THRESH = height // 15)
	
		max_thickness = 0
		for hline in table_lines:
			if hline.thickness > max_thickness:
				max_thickness = hline.thickness 

		for t in range(len(tables)):
			table = tables[t]
			tabIm = im.crop(table[:4])
			tabIm.save("__working/test.pbm")
			w, h = tabIm.size
			tabPix = tabIm.load()
			vlines_black = get_vlines(tabPix, w, h, V_THRESH = h - max_thickness * len(table_lines) - h // 20)
			vlines_white = get_vlines(tabPix, w, h, color = "white", V_THRESH = h - max_thickness * len(table_lines) - h // 20, black_thickness = max_thickness)

			max_vert_thickness = 0
			for vline in table_lines:
				if vline.thickness > max_vert_thickness:
					max_vert_thickness = hline.thickness

			hlines_white = get_hlines(tabPix, w, h, color = "white", H_THRESH = w - 250, black_thickness = max_vert_thickness)
			hlines_black = get_hlines(tabPix, w, h, H_THRESH = w - 250)

			i = 0
			while i < len(vlines_white):
				if vlines_white[i].thickness < w / 50 :
					vlines_white.remove(vlines_white[i])
				else:
					i += 1
	
			hlines = sorted(hlines_black + hlines_white , key = lambda x: x.cmpKey())
			vlines = sorted(vlines_black + vlines_white, key = lambda x: x.cmpKey())
			try:			
				vlines[0] = Line(0,0,0,h-1,"white") + vlines[0]
			except ValueError:
				vlines = [Line(0,0,0,h-1,"white")] + vlines
			try:			
				vlines[-1] = vlines[-1] + Line(w-1,0,w-1,h-1,"white")
			except ValueError:
				vlines.append(Line(w-1,0,w-1,h-1,"white"))	
				
			OCR(tabIm, hlines, vlines, imageFile, t=str(t))
			
	else:
		w,h = width, height

		hlines_black = get_hlines(pix, w, h, H_THRESH = 2*w//3)
		vlines_black = get_vlines(pix, w, h, V_THRESH = 2*h//3)
		max_thickness = 0
		for hline in hlines_black:
			if hline.thickness > max_thickness:
				max_thickness = hline.thickness 
		
		max_vert_thickness = 0
		for vline in vlines_black:
			if vline.thickness > max_vert_thickness:
				max_vert_thickness = hline.thickness


		hlines_white = get_hlines(pix, w, h, color = "white", H_THRESH = w - w//10, black_thickness = max_vert_thickness)
		vlines_white = get_vlines(pix, w, h, color = "white", V_THRESH = h - h//10, black_thickness = max_thickness)
		
		i = 0
		
		while i < len(vlines_white):
			if vlines_white[i].thickness < w / 60 :
				vlines_white.remove(vlines_white[i])
			else:
				i += 1
			
		hlines = sorted(hlines_black + hlines_white, key = lambda x: x.cmpKey())
		vlines = sorted(vlines_black + vlines_white, key = lambda x: x.cmpKey())
		
		try:			
			vlines[0] = Line(0,0,0,h-1,"white") + vlines[0]
		except ValueError:
			vlines = [Line(0,0,0,h-1,"white")] + vlines
		try:			
			vlines[-1] = vlines[-1] + Line(w-1,0,w-1,h-1,"white")
		except ValueError:
			vlines.append(Line(w-1,0,w-1,h-1,"white"))

		OCR(im, hlines, vlines, imageFile)
			

def workerTask(q):
	global auto
	while not q.empty():
		processImage(q.get_nowait()[0], autoFind=auto)
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

for filename in os.listdir("__working"):	
	os.remove("__working/" + filename)
os.rmdir("__working")

