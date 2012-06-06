#!/opt/python273/bin/python

import os
import sys
import md5
import time ## for timing the ul.urlopen process
import ConfigParser
import urllib2 as ul
from bs4 import BeautifulSoup
from optparse import OptionParser
from time import gmtime, strftime
from lepl.apps.rfc3696 import HttpUrl

import spider_funcs

usage="spider.py --verbose --seed=http://someplace.com/"

parser = OptionParser(usage=usage)
parser.add_option("--seed", help="Set the seed (starter) URL. --seed=http://someplace.com")
parser.add_option("--verbose", "-v", action="store_true", help="Verbose mode - Mostly statistical data for now (URLs found per pass)")

###

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
	con = mdb.connect(dbhost, dbuser, dbpass, dbname)
	logMessage("Connected to database Server.", log, verbose)
except:
	err = "Error %d: %s" % (e.args[0], e.args[1])
	logMessage(err, log, verbose)
	sys.exit(1)

# And now we begin the work ...

urls = getURLsFromDb(50)

for url in urls:
	logMessage("Retrieving content from " + url, log, verbose)
	data = getContentFromURL(url)
	logMessage("Content retrieved in " + data["time_taken"] + "ms, code: " + data["code"], log, verbose)
	updateURL(url, data["content"], data["http_code"], data["time_taken"])
	logMessage("Updated " + url + " with the content, http code and time taken")
	urllist = extractURLs(data["content"])
	logMessage("Extracted URLs from " + url, log, verbose)
	insertContent(urllist, url)
	logMessage("Inserted " + len(urllist) + " URLs into the database", log, verbose)