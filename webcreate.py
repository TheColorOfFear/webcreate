import sys

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

if __name__ == "__main__":
	if ((len(sys.argv) == 1) or (sys.argv[1] in ["-h","-?","--help"])):
		print("Usage: webcreate <--listing listing_file | data_file> [output_template ...]")
	else:
		if (sys.argv[1] == "--listing"):
			print("#TODO")
		else:
			data_in_name     = sys.argv[1]
			template_in_names = sys.argv[2:]
			
			with open(data_in_name) as dataf:
				textin = dataf.read()
			
			for template_in_name in template_in_names:
				print(data_in_name, template_in_name, end=' --> ')
				with open(template_in_name) as rulef:
					rules = rulef.read()
				ruledict = readruledict(rules)
				
				textout = applyruledict(textin, ruledict)
				name = data_in_name.rpartition('.')
				nameform = "~outputformat(filename:"+name[0]+",extension:"+name[2]+"){}"
				data_out_name = applyruledict(nameform, ruledict)
				print(data_out_name)
				with open(data_out_name, 'wt') as dataf:
					dataf.write(textout)




















