#!/opt/python273/bin/python

import os, sys, md5
import ConfigParser
import urllib2 as ul
from optparse import OptionParser
from bs4 import BeautifulSoup
from time import gmtime, strftime
from lepl.apps.rfc3696 import HttpUrl

import spider_funcs

usage="spider.py --verbose --seed=http://someplace.com/"

parser = OptionParser(usage=usage)
parser.add_option("--seed", help="Set the seed (starter) URL. --seed=http://someplace.com")
parser.add_option("--verbose", "-v", action="store_true", help="Verbose mode - Mostly statistical data for now (URLs found per pass)")

###

conf = getConfig()

if options.verbose:
	verbose = options.verbose

validator = HttpUrl()
if options.seed AND validator(options.seed):
	createTable()
	addSeed(options.seed)

if not dbHasContent(): 
	# We will poorly assume the table doesn't exist and attempt to create it next
	logMessage("urls table is empty or missing, use --seed=http://domain.com/ flag to create and seed it.", log, verbose)

## Try to connect to the DB, throw exception if failed
try:
	con = mdb.connect(conf["dbhost"], conf["dbuser"], conf["dbpass"], conf["dbname"])
	logMessage("Connected to database Server.", log, verbose)
except:
	err = "Error %d: %s" % (e.args[0], e.args[1])
	logMessage(err, log, verbose)
	sys.exit(1)

# And now we begin the work ...

urls = getURLsFromDb(50)

while(1):
	try:
		for url in urls:
			data = getContentFromURL(url)
			updateURL(url, data["content"], data["http_code"], data["time_taken"])
			urllist = extractURLs(data["content"])
			logMessage("Extracted URLs from " + url, log, verbose)
			insertContent(urllist, url)
			logMessage("Inserted " + len(urllist) + " URLs into the database", log, verbose)
	except KeyboardInterrupt:
		print "\nCaught KeyboardInterrupt Exception, exiting ..."
		sys.exit(0)