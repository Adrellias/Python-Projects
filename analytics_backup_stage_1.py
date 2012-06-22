import os
import sys
import urllib2 as ul
import MySQLdb as mdb
from ftplib import FTP
from time import gmtime, strftime

# Test+Setup MySQL Connection

def getConfig():
	conf = ConfigParser.ConfigParser()
	if not os.path.exists("./analytics_ftp.conf"):
		conffile = open("./analytics_ftp.conf", "w")

		myhost = raw_input("Enter the MySQL Hostname: ")
		myuser = raw_input("Enter the MySQL User: ")
		mypass = raw_input("Enter the MySQL Password")
		myport = 3306

		ftphost = raw_input("Enter the FTP Hostname: ")
		ftpuser = raw_input("Enter the FTP Username: ")
		ftppass = raw_input("Enter the FTP Password: ")
		ftpport = 21

		conf.add_section("tool")
		conf.set("tool", "host", ftphost)
		conf.set("tool", "port", ftpport)
		conf.set("tool", "user", ftpuser)
		conf.set("tool", "pass", ftppass)
		conf.write(conffile)
		print "You will need to edit the config file if your FTP or MySQL services run on alternative ports."
		conffile.close()
		print "Execute again to run the tool with the new configuration."
		sys.exit(0)
	else:
		conf.read("./analytics_ftp.conf")
		opts = conf.options("tool")
		ftphost = conf.get("tool", "ftp_host")
		ftpport = conf.getint("tool", "ftp_port")
		ftpuser = conf.get("tool", "ftp_user")
		ftppass = conf.get("tool", "ftp_pass")
		myhost = conf.get("tool", "my_host")
		myuser = conf.get("tool", "my_user")
		mypass = conf.get("tool", "my_pass")
		myport = conf.getint("tool", "my_port")
		passwd = conf.get("tool", "ftp_pass")

	return { 'ftphost': ftphost, 'ftpport': ftpport, 'ftpuser': ftpuser, 'ftppass': ftppass, 'myhost': myhost, 'myuser': myuser, 'mypass': mypass, 'myport': myport }

try:
	con = mdb.connect('localhost', 'user', 'pass', 'analytics')
except:
	print "Failed to connect to database."
	print "Error: %d : %s" % (e.args[0], e.args[1])

# Test+Setup FTP Connection.
#try:
#	ftp = FTP('ip.add.re.ss')
#	ftp.login('someuser', 'somepass')
#except:
#	print "Error with FTP - %d : %s" % (e.args[0], e.args[1])


# Now that we have a connection to the DB and FTP..

cur = con.cursor()
cur.execute("show tables like 'visit_events_20%'")
ve = cur.fetchall()

ve_slice = ve[:-2]

for item in ve_slice:
	print item