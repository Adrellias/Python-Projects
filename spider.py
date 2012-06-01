#!/opt/python273/bin/python

import os
import sys
import md5
import ConfigParser
from optparse import OptionParser
import urllib2 as ul
from time import gmtime, strftime

usage="spider.py --verbose --seed=http://someplace.com/"

parser = OptionParser(usage=usage)
parser.add_option("--seed", help="Set the seed (starter) URL. --seed=http://someplace.com")
parser.add_option("--verbose", "-v", action="store_true", help="Verbose mode - Mostly statistical data for now (URLs found per pass)")

def getConfig():
	conf = ConfigParser.ConfigParser()
	if os.path.exists("./spider.conf") == False:
		conffile = open("./spider.conf")
		conf.add_section("Default")
		conf.set("Default", "dbhost", "localhost")
		conf.set("Default", "dbuser", "mysqlusername")
		conf.set("Default", "dbpass", "mysqlpassword")
		conf.set("Default", "dbname", "mysqldatabasename")
		conf.set("Default", "log", "spider.log")
		conf.set("Default", "urls-per-pass", 50)
		conf.write(conffile)
		conffile.close
	else:
		conf.read("./spider.conf")
		opts = conf.options("Default")

		log = conf.get("Default", "log")
		perpass = conf.getint("Default", "urls-per-pass")
		dbhost = conf.get("Default", "dbhost")
		dbuser = conf.get("Default", "dbuser")
		dbpass = conf.get("Default", "dbpass")
		dbname = conf.get("Default", "dbname")

if options.verbose:
	verbose = options.verbose

###

def createTable():
	sql = "CREATE TABLE IF NOT EXISTS spider (  "
	sql += "`id` int not null primary key auto_increment, `url` TEXT, url_hash char(32) UNIQUE,"
	sql += " `parent_url` int, `status` tinyint, `content_size` int, `content` LONGTEXT,"
	sql += " `time_taken` int, `created` datetime, `is_seed` tinyint default 0, INDEX(`created`), INDEX(`url_hash`)"
	sql += " ) engine=innodb"

	# Determine if we are running MySQL 5.5 and if innodb_file_per_table is set
	cur = mdb.cursor()
	cur.execute("SELECT VERSION()")
	ver = cur.fetchone()

	cur = mdb.cursor()
	cur.execute("SHOW GLOBAL VARIABLES LIKE 'innodb_file_per_table'")
	fpt = cur.fetchone()

	if ver["version()"].startswith("5.5") AND fpt["Value"] == "ON":
		sql += " row_format=compressed key_block_size=8"

###

def addSeed(seed):
	cur = mdb.cursor()
	cur.execute("TRUNCATE TABLE spider") 
	cur.execute("INSERT INTO spider VALUES (NULL, %s, %s, '', 0, 0, 0, 0, NOW(), 1)", (seed, md5.md5(seed).hexdigest()))

def logMessage(message, log, verbose):
	fmessage = "["
	fmessage += strftime("%Y-%m-%d %H:%M:%S")
	fmessage += "] " + message + "\n"

	if log != "":
		lfile = open(log, "w")
		lfile.writelines(fmessage)
		lfile.close

	if verbose:
		print fmessage

###

def dbHasContent(): # This is where we assume that we have a seed url if count != 0 
	cur = mdb.cursor()
	cur.execute("SELECT COUNT(*) as cnt FROM `spider`")
	data = cur.fetchone()

	if data["cnt"] > 0:
		return True
	else:
		return False

###

def getURLs(limit=5):
	cur = mdb.cursor()
	cur.execute("SELECT `url` FROM `spider` WHERE `status` = 0 LIMIT %d", (limit))
	rows = cur.fetchall()
	return rows

###

def getContentFromURL(url):
 # Get the content, return raw content

###

def extractURLs(content):
	# Use regex to extract URLs from html content, ignore anything that is a file or non-http/https href

###

def insertContent(urls, parent):
	# Build BULK Query, insert to DB
	cur = mdb.cursor()
	for url in urls:
		content_length = len(url[2]
		cur.execute("INSERT INTO spider VALUES (NULL, %s, %s, 1, %d, %s, %d, NOW(), 0)", (url, md5.md5(url).hexdigest()), len(url[2]), url[3], url[4]))

###

try:
	con = mdb.connect(dbhost, dbuser, dbpass, dbname)
	logMessage("Connected to database Server.", log, verbose)

	if dbHasContent() == False: # We will poorly assume the table doesn't exist and attempt to create it next
		createTable()
		logMessage("urls table not found.\nCreated." log, verbose)

	try:
		# This is where we do the bulk of the work 
		# Would love to thread this, but it's far beyond my knowledge at the moment

except:
	err = "Error %d: %s" % (e.args[0], e.args[1])
	logMessage(err, log, verbose)
	sys.exit(1)
finally:
	if con:
		con.close()