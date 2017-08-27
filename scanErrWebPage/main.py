#!/usr/bin/python


from StringIO import StringIO
import sys
import pycurl
import re
import pdb


#WEB_SITE = "http://www.ecust.edu.cn"
WEB_SITE = "http://news.ecust.edu.cn/news?category_id=58"
URL_PREFIX = "www.ecust.edu.cn"
URL_ORG_NAME = "ecust"
#WEB_SITE = "http://news.ecust.edu.cn/call_xxzy_xykx_2013.php"

OUT_FILE = "result.txt"

g_url_prefix = None

g_Url_Rec = dict()
g_Php_Url_Rec = dict()


def getPageHtmlSrc(url):
	buffer = StringIO()
	try:	
		c = pycurl.Curl()
		c.setopt(c.URL, url)
		c.setopt(c.WRITEDATA, buffer)
		c.perform()
		c.close()
		bodyStr = buffer.getvalue()
	except pycurl.error, e:
		#pdb.set_trace()
		print("error for url: {}".format(url))
		print(e)
		bodyStr = ""

	return bodyStr

def outAppendToFile(content, outFile):
	#outFile = 'tmp.txt'
	f = open(outFile, 'a')
	f.write(content)
	f.close()

def outToFile(content):
	#outFile = 'tmp.txt'
	f = open(OUT_FILE, 'a')
	f.write(content+'\n\n')
	f.close()


def getLinesFromSrcCode(bodyStr):
	'''
	return a list of line parsed from the html src
	'''
	lineList = bodyStr.split('\n')
	lineNum = len(lineList)
	return lineList

	#print("line: {}".format(lineNum))
	#print(lineList[lineNum/2])


def getMainPageTabUrlList(mainPageLineList):
	tabPhpUrlList = list()
	pat = re.compile(r'src=\"(.*php)')
	for line in mainPageLineList:
		if re.search(pat, line):
			#print line
			#print(re.search(pat, line).groups()[0])
			phpUrl = re.search(pat, line).groups()[0]
			tabPhpUrlList.append(phpUrl)
	return tabPhpUrlList
	#re.search(r"src=\"(.*php)",str1).groups()[0]


def getUrlListFromTabPage(tabPageUrl):
	bodyStr = getPageHtmlSrc(tabPageUrl)

	#re.S: .can represent \n
	groups = re.findall(r'href="(.*?)"[\n >]*(.*?)[\n ]*</a>', bodyStr, re.S)
	for item in groups:
		urlAddr = item[0]
		urlTopic = item[1].rstrip()
		print('urlAddr:{}!, urlTopic:{}!'.format(urlAddr, urlTopic))



def isLocalUrl(urlAddr):
	'''
	example: www.site1.com, for a outside link like www.site2.com url link in the site1 website, 
			 it's not a local url.
	'''
	if urlAddr is None or urlAddr == '':
		return False

	if urlAddr[0] == '/':
		return True

	if urlAddr.find(URL_ORG_NAME) == -1:
		return False

	return True	



def adjustUrlAddr(urlAddr, urlPrefix):
	if urlAddr[0] == '/':
		# it's a relative url address.
		urlAddr = urlPrefix + urlAddr

	pos = urlAddr.find('http://', 0)
	if pos == -1:
		fullUrlAddr = 'http://' + urlAddr

	return urlAddr

def addToGloData(urlAddr, urlTopic="", pageType='NOT_PHP'):
	global g_Url_Rec
	global g_Php_Url_Rec

	if urlAddr is None or urlAddr == '':
		return False

	#if urlAddr[0] == '/':
	#	urlAddr = URL_PREFIX + urlAddr
	
	if pageType == 'NOT_PHP':
		if g_Url_Rec.get(urlAddr) is None:
			g_Url_Rec[urlAddr] = urlTopic
			print("add urlAddr: {}".format(urlAddr))
			print("not-php url number: {}".format(len(g_Url_Rec)))
			outToFile("url: {} --> topic: {}, NOT-PHP!".format(urlAddr, urlTopic))
			return True
		else:
			return False
	else:
		if g_Php_Url_Rec.get(urlAddr) is None:
			g_Php_Url_Rec[urlAddr] = urlTopic
			print("add urlAddr: {}".format(urlAddr))
			print("php url number: {}".format(len(g_Php_Url_Rec)))
			outToFile("url: {} --> topic: {}, PHP!".format(urlAddr, urlTopic))
			return True
		else:
			return False

def fixTopic(topicStr):
	outTopic = ''

	# parse the <span> and </span> tag
	spanGroups = re.findall(r'<span[^>]*?>(.*?)</span>', topicStr, re.S)
	if len(spanGroups) != 0:
		for item in spanGroups:
			outTopic += item + ' '
	else:
		outTopic = topicStr

	# remove the '\n'
	outTopic = outTopic.replace('\n', ' ')

	return outTopic



def searchForNonPhpPage(urlAddr):
	print("search for NON-PHP page in URL: {}".format(urlAddr))

	urlPrefix = getUrlPrefix(urlAddr)
	print("current urlAddr: {}, urlPrefix: {}".format(urlAddr, urlPrefix))

	pageSrcCode = getPageHtmlSrc(urlAddr)
	if pageSrcCode == "":
		return

	parentUrlAddr = urlAddr

	#pat1 matchs all the static html/htm link with no picture
	#pat2 matchs static and dynamic link(with ?xx=xx clause)
	#pat1 = r'a +href=[\'\"]([a-zA-Z0-9/\.:_]+?)(html|htm)*[\'\"][^>]*>([^<>]*?)</a>'
	#pat2_1 = r'a[^><]+href=[\'\"]([a-zA-Z0-9/\.:_\?=&]+?)(html|htm)*[\'\"][^>]*>([^<>]*?)</a>'
	pat2 = r'a[^><]+href=[\'\"]([a-zA-Z0-9/\.:_\?=&]+?)(html|htm)*[\'\"][^>]*?>(.*?)</a>'
	groups = re.findall(pat2, pageSrcCode, re.S)
	pdb.set_trace()
	for item in groups:
		urlAddr = item[0] + item[1]
		urlTopic = item[2].rstrip()

		urlTopic = fixTopic(urlTopic)
		urlAddr = adjustUrlAddr(urlAddr, urlPrefix)

		if isLocalUrl(urlAddr):
			print("parentUrlAddr: {}, urlAddr: {}. NON-PHP page.".format(parentUrlAddr, urlAddr))
			ret = addToGloData(urlAddr, urlTopic, "NOT_PHP")
			if not ret:
				continue
			searchForPhpPage(urlAddr)
			searchForNonPhpPage(urlAddr)

			
	#print(g_Url_Rec)




def getUrlPrefix(fullUrlAddr):
	pos = fullUrlAddr.find('http://', 0)
	if pos == -1:
		fullUrlAddr = 'http://' + fullUrlAddr

	pos = fullUrlAddr.find('http://', 0)
	pos = fullUrlAddr.find('/', pos + len('http://'))
	if pos != -1:
		url_prefix = fullUrlAddr[0:pos]
	else:
		url_prefix = fullUrlAddr

	return url_prefix
	


def searchForPhpPage(urlAddr):
	'''
	urlAddr must be the full name url like xxx/aaa/bbb, can't be something like /aaa/bbb
	'''
	print("search for PHP page in URL: {}".format(urlAddr))

	urlPrefix = getUrlPrefix(urlAddr)
	print("current urlAddr: {}, urlPrefix: {}".format(urlAddr, urlPrefix))
	parentUrlAddr = urlAddr

	pageSrcCode = getPageHtmlSrc(urlAddr)
	if pageSrcCode == "":
		return

	pat = r'src=\"([a-zA-Z0-9:\._/]+?\.php)'
	groups = re.findall(pat, pageSrcCode)

	for item in groups:
		urlAddr = item
		urlAddr = adjustUrlAddr(urlAddr, urlPrefix)

		if isLocalUrl(urlAddr):
			print("parentUrlAddr: {}, urlAddr: {}. PHP page.".format(parentUrlAddr, urlAddr))
			ret = addToGloData(urlAddr, "", "PHP")
			if not ret:
				continue
			searchForPhpPage(urlAddr)
			searchForNonPhpPage(urlAddr)

		#print(urlAddr)


def printPhpRec():
	print("-"*10 + "PHP PAGE URL LIST BEGINS"  + "-"*10)
	for key, value in g_Php_Url_Rec.items():
		print("url:{}, topic:{}".format(key, value))
	print("-"*10 + "PHP PAGE URL LIST ENDS"  + "-"*10)

def printNonPhpRec():
	print("-"*10 + "NON-PHP PAGE URL LIST BEGINS"  + "-"*10)
	for key, value in g_Url_Rec.items():
		print("url:{}, topic:{}".format(key, value))
	print("-"*10 + "NON-PHP PAGE URL LIST ENDS"  + "-"*10)


def mainProc():

	searchForPhpPage(WEB_SITE)
	searchForNonPhpPage(WEB_SITE)

	#printPhpRec()
	#printNonPhpRec()

	#mainPageSrcCode = getPageHtmlSrc(WEB_SITE)


	# pat match all the static html/htm link with no picture
	# pat2 match static and dynamic link(with ?xx=xx clause)
	#pat = r'a +href=[\'\"]([a-zA-Z0-9/\.:_]+?)(html|htm)*[\'\"][^>]*>([^<>]*?)</a>'
	#pat2 = r'a +href=[\'\"]([a-zA-Z0-9/\.:_\?=]+?)(html|htm)*[\'\"][^>]*>([^<>]*?)</a>'
	#groups = re.findall(pat2, mainPageSrcCode, re.S)
	#pdb.set_trace()
	#for item in groups:
	#	urlAddr = item[0] + item[1]
 	#	urlTopic = item[2].rstrip()

		#urlAddr = item[0]
		#urlTopic = item[1].rstrip()
		#print('urlAddr:{}!, urlTopic:{}!'.format(urlAddr, urlTopic))

	#mainPageLineList = getLinesFromSrcCode(mainPageSrcCode)

	# parse php tab page in the homepage.
	#tabPhpUrlList = getMainPageTabUrlList(mainPageLineList)
	#print(tabPhpUrlList)
	#for phpUrl in tabPhpUrlList:
	#	getUrlListFromTabPage(phpUrl)


	#getMainPageTab()
	#getMainPageTab(mainPageSrc)

if __name__ == '__main__':
	mainProc()




