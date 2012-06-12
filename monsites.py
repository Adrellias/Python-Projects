import os
import time
import urllib2 as ul
import ConfigParser
import MySQLdb as mdb

# CREATE TABLE `domains`
# (
# 	id int not null primary key auto_increment,
# 	uid int, -- ID of the user that owns this domain.
#	url varchar(255),
#	last_http_code int,
#	last_check datetime,
#	status int default 1,
#	index(uid),
#	index(url)
#	index(domtest)
# ) engine = innodb row_format = compressed;

# CREATE TABLE `domain_status`
# (
#	`did` int,
#	`http_code` int,
#	`stamp` datetime,
#	index(stamp)
# ) engine = innodb row_format = compressed;

def getConfig():
	conf = ConfigParser.ConfigParser()
	if not os.path.exists("./monsites.conf"):
		conffile = open("./monsites.conf", "w")

		# Get default values for DB Server Config
		dbhost = raw_input("Enter Hostname for Database Server: ")
		dbuser = raw_input("Enter Username for Database Server: ")
		dbpass = raw_input("Enter Password for Database Server: ")
		dbname = raw_input("Enter Database name for Database Server: ")
		verbose = 0

		conf.add_section("tool")
		conf.set("tool", "dbhost", dbhost)
		conf.set("tool", "dbuser", dbuser)
		conf.set("tool", "dbpass", dbpass)
		conf.set("tool", "dbname", dbname)
		conf.set("tool", "verbose", 0)
		conf.write(conffile)
		conffile.close
	else:
		conf.read("./monsites.conf")
		opts = conf.options("tool")

		# Read the config values
		dbhost = conf.get("tool", "dbhost")
		dbuser = conf.get("tool", "dbuser")
		dbpass = conf.get("tool", "dbpass")
		dbname = conf.get("tool", "dbname")
		verbose = conf.getint("tool", "verbose")
		
	return { 'verbose': verbose, 'dbhost': dbhost, 'dbuser': dbuser, 'dbpass': dbpass, 'dbname': dbname }

def beVerbose(message, verbose):
	if verbose == 1:
		print message

def getDomainsForCheck():
	cur = con.cursor()
	dt = time.strftime("%Y-%m-%d %H:%M:%S")
	cur.execute("SELECT `url`, `last_http_code` FROM `domains` WHERE `last_check` <= %s - INTERVAL 5 MINUTE", (dt))
	data = cur.fetchall()
	return data

def setLastChecked(domlist):
	cur = con.cursor()
	for dom in domlist:
		cur.execute("UPDATE `domains` SET `last_check` = NOW() WHERE url = %s", (dom[0]))
	con.commit()

def setTimeTaken(url, time_taken):
	cur = con.cursor()
	cur.execute("UPDATE `domains` SET last_time_taken = %s WHERE url = %s", (time_taken, url))
	con.commit();

def getContentFromURL(url):
	# Get the content, return dict with content + time_taken (in millis)
	req = ul.Request(url)
	start = time.time() * 1000
	response = ul.urlopen(req)
	code = response.getcode()
	end = time.time() * 1000

	return { 'http_code': code, 'time_taken': int(round(end - start)) }

def statusChange(url, http_code):
	cur = con.cursor()
	cur.execute("UPDATE `domains` SET `last_http_code` = %s, last_check = NOW() WHERE `url` = %s", (http_code, url))
	cur.execute("SELECT `id` FROM `domains` WHERE `url` = %s", (url))
	data = cur.fetchone()
	cur.execute("INSERT INTO `domain_status` VALUES (%s, %s, NOW())", (data[0], http_code))
	con.commit()

### Core Application ###

conf = getConfig()

con = mdb.connect(conf["dbhost"], conf["dbuser"], conf["dbpass"], conf["dbname"])

while(1):
	
	domStatusChange = 0

	beVerbose("Getting list of domains ... ", conf["verbose"])
	domlist = getDomainsForCheck()
	beVerbose("Executing for loop ... ", conf["verbose"])
	for dom in domlist:
		domStatusChange = 0
		beVerbose("Executing getContentFromURL() on " + dom[0] + " ... ", conf["verbose"])
		res = getContentFromURL("http://" + dom[0])
		if res["http_code"] != 200 and dom[1] == 200:
			beVerbose("Marking domain (" + dom[0] + ") as down ... ", conf["verbose"])
			statusChange(dom[0], res["http_code"])
			domStatusChange = 1

		if res["http_code"] == 200 and dom[1] != 200:
			beVerbose("Marking domain (" + dom[0] + ") as up ... ", conf["verbose"])
			statusChange(dom[0], res["http_code"])
			domStatusChange = 1

		beVerbose("Time taken: " + str(res["time_taken"]) + " ms ... ", conf["verbose"])
		setTimeTaken(dom[0], res["time_taken"])

		if domStatusChange == 1:
			beVerbose("Domain status changed ... ", conf["verbose"])
		else:
			beVerbose("Domain status unchanged ... ", conf["verbose"])

	beVerbose("Executing setLastChecked() ... ", conf["verbose"])
	setLastChecked(domlist)
	domlist = None
	beVerbose("Sleeping ... ", conf["verbose"])
	time.sleep(30)