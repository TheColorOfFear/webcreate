import sys
import os

#how this work??
#take a data file, laid out as follows, where 
#tags are composed of "~tagName(attribute:value,...){ tagContent }" :
# 
# ~webcreate{
#   ~head{
#     ~title{sample page}
#   }
#   ~body{
#     ~navbar{}
#     ~main{
#       ~title{welcome to my sample page!}
#       ~date{}
#       ~h3{Sample Links (World's Finest!) :}
#       ~blacklink(href:http://example.com){example.com}
#       ~blacklink(href:http://example.com){also example.com ~hot{}}
#     }
#   }
# }
#
#
#and a rule file, where tags are composed of
#"@tagName(attribute:defaultValue,...){ subRules [content] }":
#
# @outputformat(filename:input){[$filename$.html]}
# @webcreate{[<!DOCTYPE html>\n<html lang="en">$content$</html>]}
# @head{
#   @title{[<title>$content$</title>]}
#   [<head><link href="style.css" rel="stylesheet" type="text/css" media="all">$content$</head>]
# }
# @body{
#   @navbar{[<div class='navbar' id='navbar'>whoops, y'gotta turn on javascript!</navbar>\n<script src='/js/navbar.js'></script>]}
#   @main{[<div class='content'>$content$</div>]}
#   @title{[<div class='header'>$content$</div>]}
#   @blacklink(href:){[<a href='$href$' class='back'>$content$</a>]}
#   (other rules omitted for brevity)
#   [<body>$content$</body>]
# }

debuginfo = False

def parsetree(textin, tagchar, bracket=False):
	text = textin
	escaped = False
	mode = "genparse"
	attribmode = "readattrib"
	QDRL = []
	treestack = [[]]
	content = ""
	while (len(text) != 0):
		eatenchar = text[0]
		if (eatenchar == "\\" and not(escaped)):
			escaped = True
		else:
			if (mode == "genparse"):
				if (eatenchar == tagchar and not(escaped)):
					mode = "tagparse"
					workingtag = "@"
					if (not(bracket)):
						treestack[-1].append(content)
						content = ""
				elif (eatenchar == "[" and bracket and not(escaped)):
					mode = "contentparse"
					content = ""
				elif (eatenchar == "}" and not(escaped)):
					if (not(bracket)):
						treestack[-1].append(content)
						content = ""
					thistag = treestack.pop()
					try:
						treestack[-1].append(thistag)
					except:
						if (debuginfo):
							print(treestack, thistag)
				elif (not(bracket)):
					content = content + eatenchar
			elif (mode == "tagparse"):
				if (eatenchar == "{" and not(escaped)):
					mode = "genparse"
					#print(workingtag)
					treestack.append([workingtag])
					treestack[-1].append({})
					#print(treestack)
				elif (eatenchar == "(" and not(escaped)):
					mode = "attribparse"
					#print(workingtag)
					attribs = {}
					attribmode = "readattrib"
					attrib = ""
					treestack.append([workingtag])
				else:
					workingtag = workingtag + eatenchar
			elif (mode == "attribparse"):
				if (eatenchar == ")" and not(escaped)):
					mode = "wait-obrace"
					attribs[attrib.lstrip()] = attribvalue.lstrip()
					treestack[-1].append(attribs)
				elif (attribmode == "readattrib"):
					if (eatenchar == ":" and not(escaped)):
						attribmode = "readvalue"
						attribvalue = ""
					else:
						attrib = attrib + eatenchar
				elif (attribmode == "readvalue"):
					if (eatenchar == "," and not(escaped)):
						attribs[attrib.lstrip()] = attribvalue.lstrip()
						attrib = ""
						attribvalue = ""
						attribmode = "readattrib"
					else:
						attribvalue = attribvalue + eatenchar
			elif (mode == "contentparse"):
				if (eatenchar == "]" and not(escaped)):
					mode = "genparse"
					treestack[-1].append(content)
				else:
					content = content + eatenchar
			elif (mode == "wait-obrace"):
				if (eatenchar == "{" and not(escaped)):
					mode = "genparse"
			escaped = False
		#print(eatenchar, end='')
		text = text[1:]
	QDRL = treestack[-1]
	return(QDRL)

def printtree(tree, nest=0):
	for branch in tree:
		if (type(branch) is list):
			for i in range(nest):
				print("  ", end='')
			print("[")
			printtree(branch, nest + 1)
			for i in range(nest):
				print("  ", end='')
			print("]")
		else:
			for i in range(nest):
				print("  ", end='')
			print(branch)

def readruledict(textin):
	tree = parsetree(textin, "@", True)
	if (debuginfo):
		printtree(tree)
	rules = {}
	def makedict(treein, initial=False):
		thisdict = {}
		for item in treein:
			if (type(item) is dict):
				attriblist = []
				for key in item:
					attriblist.append(key)
					thisdict["$" + key + "$"] = item[key]
					#print("$" + key + "$", item[key])
				thisdict["attributes"] = attriblist
			elif (type(item) is list):
				thisdict.update(makedict(item))
			elif (type(item) is str):
				thisdict["content"] = item
		if (initial):
			return thisdict
		else:
			return {treein[0] : thisdict}
	outdict = makedict(tree, True)
	return outdict
	#print("yup those sure are rules!")

def applyruledict(textin, ruledict):
	tree = parsetree(textin, "~")
	#printtree(tree)
	#print(tree)
	def recurse(treein, initial=False, taghistory=[]):
		textback = ""
		#print(treein[0])
		tagname = treein[0]
		begin = 2
		if (initial):
			begin = 0
		for item in treein[begin:]:
			if (type(item) is list):
				taghistorytemp = taghistory.copy()
				taghistorytemp.append(tagname)
				textback = textback + recurse(item, taghistory=taghistorytemp)
			elif (type(item) is str):
				textback = textback + item
		
		#check if our tag is anywhere in the ruledict, starting deepest first
		validruledict = None
		ruledictcheck = []
		ruledictcheck.append(ruledict)
		keepchecking = True
		for tag in taghistory:
			if (keepchecking):
				for testdict in ruledictcheck:
					if (tag in testdict):
						ruledictcheck.append(testdict[tag])
		keepchecking = True
		if (tagname == '@title' and debuginfo):
			print(taghistory)
			for item in ruledictcheck:
				print(item, "\n------\n")
		while (keepchecking and len(ruledictcheck) > 0):
			checkdict = ruledictcheck.pop()
			if (tagname in checkdict):
				validruledict = checkdict
				keepchecking = False
		if (validruledict != None):
			textback = validruledict[tagname]['content'].replace("$content$", textback)
			#print("!", end='')
			#print(validruledict)
			for checkattrib in validruledict[tagname]['attributes']:
				#print(checkattrib, validruledict[tagname]['$' + checkattrib + '$'])
				if (checkattrib in treein[1]):
					#print(checkattrib, treein[1][checkattrib])
					textback = textback.replace('$' + checkattrib + '$', treein[1][checkattrib])
				else:
					#print(validruledict[tagname])
					textback = textback.replace('$' + checkattrib + '$', validruledict[tagname]['$'+checkattrib+'$'])
		##TODO : replace $[SMTH]$ in the textback with attribs and then stuff it in the tag's $[output]$
		#print('>' + treein[0])
		return textback
	return recurse(tree, initial=True)

def openfile(filename, errline=True):
	try:
		with open(filename) as f:
			textin = f.read()
	except UnicodeDecodeError:
		print("UTF-8:", end="")
		if errline:
			print(filename)
		with open(filename, encoding="utf8") as f:
			textin = f.read()
	return textin

def writefile(filename, textout, errline=True):
	try:
		with open(filename, 'wt') as f:
			f.write(textout)
	except UnicodeEncodeError:
		print("UTF-8:", end="")
		if errline:
			print(filename)
		with open(filename, 'wt', encoding="utf8") as f:
			f.write(textout)

def dofile(data_in_name, template_in_names, preservePath=True, endPreserve=False):
	textin = openfile(data_in_name)
	
	for template_in_name in template_in_names:
		#with open(template_in_name) as rulef:
		#	rules = rulef.read()
		rules = openfile(template_in_name)
		print(data_in_name, template_in_name, end=' --> ')
		ruledict = readruledict(rules)
		
		textout = applyruledict(textin, ruledict)
		path = os.path.split(data_in_name)
		name = path[1].rpartition('.')
		if endPreserve and preservePath:
			fname = path[0] + "#" + name[0]
			print(fname)
			name = [fname , name[1], name[2]]
		nameform = "~outputformat(filename:"+name[0]+",extension:"+name[2]+"){}"
		data_out_list = applyruledict(nameform, ruledict).split("#")
		if preservePath and not(endPreserve):
			data_out_name = path[0]
		else:
			data_out_name = ""
		for chunk in data_out_list:
			data_out_name = os.path.join(data_out_name, chunk)
		writefile(data_out_name, textout, errline=False)
		print(data_out_name)

if __name__ == "__main__":
	if ((len(sys.argv) == 1) or (sys.argv[1] in ["-h","-?","--help"])):
		print("Usage: webcreate [--no-preserve-path] <--listing listing_file | data_file> [output_template ...]")
	else:
		args = sys.argv[1:]
		options = {
			"preservePath"	: True,
			"endPreserve"	: True
		}
		while args[0] in ["--no-preserve-path"]:
			if args[0] == "--no-preserve-path":
				options["preservePath"] = False
				args.pop(0)
		if (args[0] == "--listing"):
			listing_in_name = args[1]
			with open(listing_in_name) as listingf:
				listingin = listingf.read()
			
			listing = listingin.splitlines()
			for line in listing:
				if (line == '' or line[0] == '#'):
					pass
				else:
					dofile(line, args[2:], preservePath=options["preservePath"], endPreserve=options["endPreserve"])
		else:
			dofile(args[0], args[1:], preservePath=options["preservePath"], endPreserve=options["endPreserve"])
