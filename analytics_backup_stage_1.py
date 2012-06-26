import os, os.path
import sys
import ConfigParser
import urllib2 as ul
import MySQLdb as mdb
from ftplib import FTP

def getConfig():
	conf = ConfigParser.ConfigParser()
	if not os.path.exists("./analytics_ftp.conf"):
		conffile = open("./analytics_ftp.conf", "w")

		backup_path = raw_input("Directory where files should be stored locally prior to remote push (trailing slash not required): ")

		myhost = raw_input("Enter the MySQL Hostname: ")
		myuser = raw_input("Enter the MySQL User: ")
		mypass = raw_input("Enter the MySQL Password")
		mydb = raw_input("Enter the name of the database: ")
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
		conf.set("tool", "backup_path", backup_path)
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
		backup_path = conf.get("tool", "backup_path")

	return { 'ftphost': ftphost, 'ftpport': ftpport, 'ftpuser': ftpuser, 'ftppass': ftppass, 'myhost': myhost, 'myuser': myuser, 'mypass': mypass, 'myport': myport, 'backup_path': backup_path }

cfg = getConfig()

try:
	con = mdb.connect(cfg["my_host"], cfg["my_user"], cfg["my_pass"], cfg["my_db"])
except:
	print "Error: %d : %s" % (e.args[0], e.args[1])

# Test+Setup FTP Connection.
#try:
#	ftp = FTP('ip.add.re.ss')
#	ftp.login('someuser', 'somepass')
#except:
#	print "Error with FTP - %d : %s" % (e.args[0], e.args[1])


# Now that we have a connection to the DB and FTP..
# Get all the tables for visit_events_20* and media_events_20*
# .. and dump them to .dat files
cur = con.cursor()
cur.execute("show tables like 'visit_events_20%'")
ve = cur.fetchall()

cur.execute("show tables like 'media_events_20%'")
me = cur.fetchall()

# Pop off the last two list dict elements (most recent archive tables, in case they may get late inserts)
ve_slice = ve[:-2]
me_slice = me[:-2]

expected_files_count = len(me_slice) + len(ve_slice)

for vevent in ve_slice:
	cur.execute("SELECT * FROM " + vevent[0] + " INTO OUTFILE '" + backup_path + "\\" + vevent[0] + ".dat'")

for mevent in me_slice:
	cur.execute("SELECT * FROM " + mevent[0] + " INTO OUTFILE '" + backup_path + "\\" + mevent[0] + ".dat'")

files = glob.glob1(cfg["backup_path"], "*.dat")
dat_count = len(files)

for item in files:
	subprocess.call("7zip -some -flags " + item)

if dat_count == expected_files_count:
	newpath = "/" + year + "/" + month
	ftp.sendcmd("MKDIR " + newpath)
	ftp.cwd(newpath)
	for item in glob.glob1(cfg["backup_path"], "*.7z"):
		f = open(item, "r")
		ftp.storbinary("STOR "+ item +, f)
		f.close()
else:
	print "Error: Total files in the directory do not match the total expected number of files."