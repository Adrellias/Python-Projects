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

		config = { 'log': log, 'perpass': perpass, 'dbhost': dbhost, 'dbuser': dbuser, 'dbpass': dbpass, 'dbname': dbname }
		return config

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

	cur.execute("SHOW GLOBAL VARIABLES LIKE 'innodb_file_per_table'")
	fpt = cur.fetchone()

	# Check if mysql version and configuration is capable of handling compressed rows
	if ver["version()"].startswith("5.5") AND fpt["Value"] == "ON":
		logMessage = "Detected MySQL 5.5 with innodb_file_per_table. Adding row compression."
		sql += " row_format=compressed key_block_size=8"

	# Create the table
	cur.execute(sql)

###

def addSeed(seed):
	cur = mdb.cursor()
	cur.execute("TRUNCATE TABLE spider") 
	cur.execute("INSERT INTO spider VALUES (NULL, %s, %s, '', 0, 0, 0, 0, NOW(), 1)", (seed, md5.md5(seed).hexdigest()))

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
	cur = mdb.cursor()
	cur.execute("SELECT COUNT(*) as cnt FROM `spider`")
	data = cur.fetchone()

	if data["cnt"] > 0:
		return True
	else:
		return False

###

def getURLsFromDb(limit=5):
	# Get URLs from DB, limited to limit
	cur = mdb.cursor()
	cur.execute("SELECT `url` FROM `spider` WHERE `status` = 0 LIMIT %d", (limit))
	rows = cur.fetchall()
	for i in rows:
		cur.execute("UPDATE `urls` SET `stats` = 1 WHERE `id` = %d", (i["id"]))
	return rows

###

def getContentFromURL(url):
	# Get the content, return raw
	req = ul.Request(url)
	response = ul.urlopen(req)
	return response.read()

###

def extractURLs(content):
	urls = []
	soup = BeautifulSoup(content)
	for link in soup.find_all('a'):
		urls.append(link.get('href'))
	return urls

###

def insertContent(url, parent, content, time_taken):
	cur = mdb.cursor()
	cur.execute("INSERT INTO spider VALUES (NULL, %s, %s, %s, 1, %d, %s, %d, NOW(), 0)", (url, md5.md5(url).hexdigest(), parent, len(content), content, time_taken))

###