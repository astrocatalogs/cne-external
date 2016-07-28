import re

__all__ = ['convert_line_bands']

def get_dec_digits(string):
	
	for i in range(len(string)):
		if string[i] == '.':
			return len(string) - i - 1

	return 0

def convert_line_bands(line, titles):
	
	bands = r'UBVRI'
	mag_dict = {}
	
	col_set = set([])
	for i, title in enumerate(titles):
		title = title.upper().replace('_', '').replace(' ', '')
		for band in bands:
			if title == band + 'MAG':
				mag_dict[band] = line[i].strip()
		col_set.add(i)	


	for i, title in enumerate(titles):
		title = title.upper().replace(" ", "")
		
		if re.match(r'[%s][\-_][%s]' %(bands, bands), title):
			subtrahend = mag_dict[title[2]]
			minuend = line[i].strip()

			decs1 = get_dec_digits(minuend)
			decs2 = get_dec_digits(subtrahend)
			decs = decs1 if decs1 > decs2 else decs
			if not titles[0] in mag_dict:
				mag_dict[titles[0]] = ('{:.%df}' %(decs)).format(float(subtrahend) + float(minuend))
			col_set.add(i)

	line_list = []
	for band in mag_dict:
		new_line = []
		for i in range(len(line)):
			if not i in col_set: new_line.append(line[i])
		new_line.append(mag_dict[band])
		new_line.append(line)
		
		line_list.append(new_line)

	titles.append('Mag', 'Band')

	return (line_list, titles)

		
		
