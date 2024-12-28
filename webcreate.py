import sys

#how this work??
#take a data file, laid out as follows, where 
#tags are composed of "~tagName(attribute:'value',...){ tagContent }" :
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
#       ~blacklink(href:'http://example.com'){example.com}
#       ~blacklink(href:'http://example.com'){also example.com ~hot{}}
#     }
#   }
# }
#
#
#and a rule file, where tags are composed of
#"@tagName(attribute:'defaultValue',...){ subRules [content] }":
#
# @outputformat(filename:'input',extension:'wcr'){[$filename$.html]}
# @webcreate{[<!DOCTYPE html>\n<html lang="en">$content$</html>]}
# @head{
#   @title{[<title>$content$</title>]}
#   [<head><link href="style.css" rel="stylesheet" type="text/css" media="all">$content$</head>]
# }
# @body{
#   @navbar{[<div class='navbar' id='navbar'>whoops, y'gotta turn on javascript!</navbar>\n<script src='/js/navbar.js'></script>]}
#   @main{[<div class='content'>$content$</div>]}
#   @title{[<div class='header'>$content$</div>]}
#   @blacklink(href:''){[<a href='$href$' class='back'>$content$</a>]}
#   (other rules omitted for brevity)
#   [<body>$content$</body>]
# }

def readruledict(textin):
	rules = {}
	text = textin
	escaped = False
	mode = "genparse"
	while (len(text) != 0):
		eatenchar = text[0]
		if (eatenchar == "\\" and not(escaped)):
			escaped = True
		else:
			if (mode == "genparse"):
				if (eatenchar == "@" and not(escaped)):
					mode = "tagparse"
					workingtag = "@"
			elif (mode == "tagparse"):
				if (eatenchar == "{" and not(escaped)):
					mode = "genparse"
					print(workingtag)
				elif (eatenchar == "(" and not(escaped)):
					mode = "attribparse"
					print(workingtag)
				else:
					workingtag = workingtag + eatenchar
			elif (mode == "attribparse"):
				if (eatenchar == ")" and not(escaped)):
					mode = "genparse"
			escaped = False
		#print(eatenchar, end='')
		text = text[1:]
	print("yup those sure are rules!")

if __name__ == "__main__":
	if ((len(sys.argv) == 1) or (sys.argv[1] in ["-h","-?","--help"])):
		print("Usage: webcreate <--listing listing_file | data_file> [output_template ...]")
	else:
		if (sys.argv[1] == "--listing"):
			print("#TODO")
		else:
			data_in_name     = sys.argv[1]
			template_in_name = sys.argv[2]
			print(data_in_name, template_in_name)
			with open(template_in_name) as rulef:
				rules = rulef.read()
			ruledict = readruledict(rules)























