import os
import sys
import time ## for timing the ul.urlopen process
import smtplib
import ConfigParser
import urllib2 as ul
from bs4 import BeautifulSoup

def sendEmail(from_email, to_email):
		# Send an SMS to user@txtservice.tld
	SUBJECT = "Test email from Python"
	TO = conf["to_user"]
	FROM = conf["from_user"]
	text = "There's a spot open at minecraftserver.net!"

	BODY = string.join((
		"FROM: %s" % FROM,
		"TO: %s" % TO,
		"SUBJECT: %s" % SUBJECT ,
		"",
		text
	), "\r\n")

	server = smtplib.SMTP("localhost")
	server.sendmail(FROM, TO, BODY)
	server.quit()

def getConfig():
	conf = ConfigParser.ConfigParser()
	if not os.path.exists("./mcs_checker.conf"):
		conffile = open("./mcs_checker.conf", "w")

		to_email = raw_input("Enter the TO EMail Address: ")
		from_email = raw_input("Enter the FROM EMail Address: ")
		seconds = raw_input("Enter the number of seconds to wait between checks: ")

		conf.add_section("tool")
		conf.set("tool", "to_email", "my@emailaddress.com")
		conf.set("tool", "from_email", "from@emailaddress.com")
		conf.set("tool", "seconds-between-checks", 60)

		conf.write(conffile)
		conffile.close
		print "Config created (mcs_checker.conf) - edit and re-execute"
		sys.exit(0)
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
			sendEmail(conf["from_email"], conf["to_email"])
			#print "Less than ten items! A spot is open!"
		time.sleep(conf["sbc"])
	except KeyboardInterrupt:
		print "\nCaught KeyboardInterrupt, Exiting..."
		sys.exit(0)