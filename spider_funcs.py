###

def getConfig():
	conf = ConfigParser.ConfigParser()
	if not os.path.exists("./spider.conf"):
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
		logMessage("Config file created. Edit it and then re-run with --seed=http://your.starter.website.com/, add --verbose if you would like to see messages on-screen", log, verbose)
		sys.exit(1)
	else:
		conf.read("./spider.conf")
		opts = conf.options("Default")

		log = conf.get("Default", "log")
		perpass = conf.getint("Default", "urls-per-pass")
		dbhost = conf.get("Default", "dbhost")
		dbuser = conf.get("Default", "dbuser")
		dbpass = conf.get("Default", "dbpass")
		dbname = conf.get("Default", "dbname")
		
		return { 'log': log, 'perpass': perpass, 'dbhost': dbhost, 'dbuser': dbuser, 'dbpass': dbpass, 'dbname': dbname }

###

def createTable():
	sql = "CREATE TABLE IF NOT EXISTS spider (  "
	sql += "`id` int not null primary key auto_increment, `url` TEXT, url_hash char(32) UNIQUE,"
	sql += " `parent_url` int, `status` tinyint, `content_size` int, `content` LONGTEXT, `http_code` int,"
	sql += " `time_taken` int, `created` datetime, INDEX(`created`), INDEX(`url_hash`)"
	sql += " ) engine=innodb"

	cur = con.cursor()
	cur.execute("SHOW TABLES LIKE 'spider'")
	exists = cur.fetchone()
	if len(exists) == 0:
		# Determine if we are running MySQL 5.5 and if innodb_file_per_table is set
		cur.execute("SELECT VERSION()")
		ver = cur.fetchone()

		# Determine if innodb_file_per_table is ON or not.
		cur.execute("SHOW GLOBAL VARIABLES LIKE 'innodb_file_per_table'")
		fpt = cur.fetchone()

		# Check if mysql version and configuration is capable of handling compressed rows
		if ver["version()"].startswith("5.5") AND fpt["Value"] == "ON":
			logMessage("Detected MySQL 5.5 with innodb_file_per_table. Adding row compression.", log, verbose)
			sql += " row_format=compressed key_block_size=8"

		# Create the table
		cur.execute(sql)
	else:
		logMessage("Table exists.", log, verbose)

###

def addSeed(seed):
	# Stuff it in the DB and fetch it prior to moving on.
	cur = con.cursor()
	cur.execute("TRUNCATE TABLE `spider`") 
	cur.execute("INSERT INTO `spider` VALUES (NULL, %s, %s, '', 0, 0, 0, 0, NOW(), 1)", (seed, md5.md5(seed).hexdigest()))
	content = getContentFromURL(seed)
	urls = extractURLs(content)
	for items in urls:
		cur.execute("UPDATE `spider` SET `content` = %s, `content_length` = %d, `status` = 1 WHERE `url_hash` = %s", (content, len(content), md5.md5(seed).hexdigest()))

###

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

def dbHasContent():
	# This is where we assume that we have a seed url if count != 0 
	cur = con.cursor()
	cur.execute("SELECT COUNT(*) as cnt FROM `spider`")
	data = cur.fetchone()

	if data[0] > 0:
		return True
	else:
		return False

###

def getURLsFromDb(limit=5):
	# Get URLs from DB, limited to limit
	cur = con.cursor()
	cur.execute("SELECT `url` FROM `spider` WHERE `status` = 0 LIMIT %d", (limit))
	rows = cur.fetchall()
	cur.execute("UPDATE `urls` SET `status` = 1 WHERE `id` = %d", (",".join(i["id"])) )
	return rows

###

def getContentFromURL(url):
	# Get the content, return dict with content + time_taken (in millis)
	req = ul.Request(url)
	start = time.time() * 1000
	response = ul.urlopen(req)

	logMessage("Retrieving content from " + url, log, verbose)

	content = response.read()
	code = response.getcode()
	end = time.time() * 1000

	time_taken = int(round(end - start))

	logMessage("Content retrieved in " + time_taken + "ms, code: " + code, log, verbose)

	return { 'content': content, 'http_code': code, 'time_taken': time_taken }

###

def extractURLs(content):
	urls = []
	soup = BeautifulSoup(content)
	for link in soup.find_all('a'):
		urls.append(link.get('href'))

	uniq = set(urls) #Yay, uniqueness just by changing the type from a list to a set!
	fixedlist = []

	# filter our list of URLs down to items that begin with http
	for url in uniq:
		strurl = str(url)
		if strurl.startswith('http'):
			fixedlist.append(strurl)

	return fixedlist

###

def insertContent(urllist, parent):
	cur = con.cursor()
	cur.execute("SELECT id FROM spider WHERE url_hash = %s", (md5.md5(parent).hexdigest()))
	parentId = cur.fetchone()
	for item in urllist:
		cur.execute("INSERT INTO `spider` (id, url, url_hash, parent_url, created) VALUES (NULL, %s, %s, %d, NOW())", (item, md5.md5(item).hexdigest(), parentId["id"]))

###

def updateURL(url, content, http_code, time_taken):
	cur = con.cursor()
	cur.execute("UPDATE `spider` SET `content` = %s, `content_size` = %d, `http_code` = %d, `time_taken` = %d WHERE `url` = %s", (content, len(content), http_code, time_taken, md5.md5(url).hexdigest()))
	logMessage("Updated " + url + " - Content Length: " + len(content) + ", HTTP Code: " + http_code + ", Time Taken: " + time_taken + "ms", log, verbose)