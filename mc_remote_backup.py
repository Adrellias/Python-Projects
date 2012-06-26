import os
import sys
import time
import subprocess
import ConfigParser
from ftplib import FTP

def getConfig():
	conf = ConfigParser.ConfigParser()
	cfile = "pymcbackup.conf"
	if not os.path.exists(cfile):
		conffile = open(cfile, "w")

		ftphost = raw_input("Enter the FTP Hostname: ")
		ftpuser = raw_input("Enter the FTP Username: ")
		ftppass = raw_input("Enter the FTP Password: ")
		ftpport = raw_input("Enter the FTP Port (Default: 21): ")
		mcdir = raw_input("Enter the full path to your minecraft server directory (Ex: /home/minecraft/server): ")
		compress = raw_input("Do you want to compress the backup? ( 0 = No, 1 = Yes ): ")
		# keep_local = raw_input("Do you want to also keep a local copy of the backup? (Default: No): ")

		if ftpport == "":
			ftpport = 21

		conf.add_section("mcbackup")
		conf.set("mcbackup", "ftp_host", ftphost)
		conf.set("mcbackup", "ftp_port", ftpport)
		conf.set("mcbackup", "ftp_user", ftpuser)
		conf.set("mcbackup", "ftp_pass", ftppass)
		conf.set("mcbackup", "minecraft_path", mcdir)
		conf.set("mcbackup", "compress", compress)
		# conf.set("mcbackup", "keep_local", keep_local)
		conf.write(conffile)
		conffile.close()
	else:
		conf.read(cfile)
		opts = conf.options("mcbackup")
		ftphost = conf.get("mcbackup", "ftp_host")
		ftpport = conf.getint("mcbackup", "ftp_port")
		ftpuser = conf.get("mcbackup", "ftp_user")
		ftppass = conf.get("mcbackup", "ftp_pass")
		mcdir = conf.get("mcbackup", "minecraft_path")
		compress = conf.getint("mcbackup", "compress")
		# keep_local = conf.get("mcbackup", "keep_local") ## This is not yet implemented

	return { 'ftphost': ftphost, 'ftpport': ftpport, 'ftpuser': ftpuser, 'ftppass': ftppass, 'minecraft_path': mcdir }

cfg = getConfig()

def mcDirExists():
	if os.path.exists(cfg["mcdir"]):
		return True
	else:
		return False

def doBackup():
	if mcDirExists():
		tar_extra_args = ""
		ext = "tar"
		if cfg["compress"] == 1:
			tar_extra_args = "z"
			ext = "tgz"

		dt = time.strftime("%Y_%m_%d_%H")
		backup_file = "minecraft_" + dt + ext


		subprocess.call("/usr/bin/tar cf" + tar_extra_args + " /temp/" + backup_file " " + cfg["mcdir"])

		ftpUpload(backup_file)