import os
import sys
import time
import string
import smtplib
import ConfigParser
import urllib2 as ul
from bs4 import BeautifulSoup

def sendEmail(url):
	# Get the content, return dict with content + time_taken (in millis)
	req = ul.Request(url)
	response = ul.urlopen(req)

def getConfig():
	conf = ConfigParser.ConfigParser()
	if not os.path.exists("./mcs_checker.conf"):
		conffile = open("./mcs_checker.conf", "w")

		te = raw_input("Enter the TO EMail Address: ")
		fe = raw_input("Enter the FROM EMail Address: ")
		sbc = raw_input("Enter the number of seconds to wait between checks: ")

		conf.add_section("tool")
		conf.set("tool", "to_email", te)
		conf.set("tool", "from_email", fe)
		conf.set("tool", "seconds-between-checks", sbc)

		conf.write(conffile)
		conffile.close
	else:
		conf.read("./mcs_checker.conf")
		opts = conf.options("tool")
		sbc = conf.getint("tool", "seconds-between-checks")
		te = conf.get("tool", "to_email")
		fe = conf.get("tool", "from_email")

		return { 'sbc': sbc, 'to_email': te, 'from_email': fe }

def getContentFromURL(url):
	req = ul.Request(url)
	response = ul.urlopen(req)
	content = response.read()
	return content

def getTotalDiamonds(content):
	soup = BeautifulSoup(content)
	items = []
	for item in soup.find_all('li', {'class':'server2'}):
		items.append(item)
	return len(items)

conf = getConfig()

while(1):
	try:
		content = getContentFromURL("http://minecraftservers.net")
		if getTotalDiamonds(content) < 10:
			sendEmail("http://bettercraft.net/stats/file.php")
			#print "Less than ten items! A spot is open!"
		time.sleep(conf["sbc"])
	except KeyboardInterrupt:
		print "\nCaught KeyboardInterrupt, Exiting..."
		sys.exit(0)
