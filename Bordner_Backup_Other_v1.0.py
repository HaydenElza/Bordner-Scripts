# ------------------------------------------------------------------------------------------------
# Script name: Bordner Backup Other
# Created on: Jan 25, 2015
# Author: Hayden Elza
# Purpose: 	This script is intended for use in backing up the bordner data, including geodatabases.
#			A log file is kept to track potential errors.
#			SMS messages are sent to notify sys admin of errors immediately.
# Version: 1.0
# History: 	- Modified earlier Bordner backup script to now handle a list input.
#			- Removed "Z:\\Topology.tbx" from SourceList
# -------------------------------------------------------------------------------------------------


import os, sys, time, datetime
from shutil import copytree, copy2, copystat, make_archive, rmtree, ignore_patterns, move


SourceList = [
	"Z:\\bordner_standardization_test\\",
	"Z:\\DNR_DOA_Maps\\",
	"Z:\\Domains\\",
	"Z:\\Drivers and help programs\\",
	"Z:\\gis\\",
	"Z:\\MN_Conversion\\",
	"Z:\\Progress\\",
	"Z:\\Rhemtulla_MN\\",
	"Z:\\Tablet Configurations\\",
	"Z:\\Templates\\",
	"Z:\\wi_sections.gdb\\",
	"Z:\\Bordner.tbx"
] #A list of folders and files you want to backup
RemoteBackupDrive = "G:\\Bordner_Backups\\"		#The folder to backup to
LocalBackupFolder = "C:\\bordner_backup\\"		#Temp working directory to copy to before archiving, can also place script here as permenant location for use with task schedualer in windows
TempBackupFolder = "C:\\bordner_backup\\temp\\"	#This will be the name of the temp folder everything is stored in while the script runs, this folder is created by the script


# A simple class used to redirect sys.stdout to file
class WritableObject:
	def __init__(self):
		self.content = []
	def write(self, string):
		self.content.append(string)
# Open writable object
logFile = "Other_Log_" + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")
log = open(LocalBackupFolder + logFile, "w")
# Set sys.stdout to write to log, !!!Don't forget to reset sys.stdout!!!
sys.stdout = log


def copytree(src, dst, symlinks=False, ignore=None):
	# Create list filled with file and directory names
	names = os.listdir(src)
	print names
	# Recursive directory creation at destination
	if os.path.isdir(dst) is False:
		os.makedirs(dst)
	# Create empty list to store errors in
	errors = []
	# Copy loop
	for name in names:
		if names.index(name)==0:
			print len(names),"files, Copied file: ",
		print str(names.index(name)+1)+"...",
		# Build file paths
		srcname = os.path.join(src, name)
		dstname = os.path.join(dst, name)
		try:
			# Check for symlink condition and just link source and destination where applicable
			if symlinks and os.path.islink(srcname):
				linkto = os.readlink(srcname)
				os.symlink(linkto, dstname)
			# If not using symlinks and source is a directory, copy tree, ignore where necessary
			elif os.path.isdir(srcname):
				copytree(srcname, dstname, symlinks, ignore)
			# If not using symlinks and source is a file, copy
			else:
				copy2(srcname, dstname)
			# Could also be devices, sockets etc. See except block.
		# Catch the Error from the recursive copytree so that we can continue with other files
		except (IOError, os.error) as why:
			errors.append((srcname, dstname, str(why)))
			print "ERROR:", why
		# Other errors
		#except Error as err:
		#	errors.extend(err.args[0])
	# Use copystat to copy permissions and times of directores that are copied (copy2 alreay copied metadata for files)
	try:
		copystat(src, dst)
	# Catch possible errors
	except WindowsError:
		# Can't copy file access times on Windows
		pass
	except OSError as why:
		errors.extend((src, dst, str(why)))
		print "ERROR:", why
	# If there are erros raise them to users attention
	#if errors:
	#	print errors
	#	raise Error(errors)

def compress():
	env.workspace = Source
	arcpy.Compact_management("bordner_townships.gdb")
	arcpy.Compact_management("bordner_townships_attributed.gdb")

def archive(root_dir):
	print "Archiving...",
	# Build archive name
	archive_name = "BordnerBackup_Other_" + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")
	#root_dir = folder
	make_archive(LocalBackupFolder+archive_name, "zip", root_dir)
	print "DONE.",
	# Move archive to the remote backup location
	move(LocalBackupFolder+archive_name+".zip",RemoteBackupDrive+archive_name+".zip")
	print "Archive moved."

def send_sms(msg):
	import smtplib

	# Set message parameters
	gmail_user = "email@gmail.com" #email removed for publishing
	gmail_pwd = "pwd" #password removed for publishing
	FROM = 'email@gmail.com' #email removed for publishing (same as above)
	TO = ['0000000000@email-to-smsgateway'] #must be a list (phone number removed for publishing)
	SUBJECT = " Bordner Backup"
	TEXT = msg

	# Prepare actual message
	message = """\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
	try:
		server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
		server.ehlo()
		server.starttls()
		server.login(gmail_user, gmail_pwd)
		server.sendmail(FROM, TO, message)
		server.close()
		print "Successfully sent SMS."
	except:
		print "Failed to send SMS."


#-------------------------------------------
# Main - copy, archive, clean up, and notify
#-------------------------------------------
try: # Try/Except block to notify by sms that the backup failed
	# Send sms to notify start
	send_sms("Other backup was started. " + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M"))
	#print "Copy started:", datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M")
	# Copy contents of Source to TempBackupFolder
	for Source in SourceList:
		try:
			# If file is path, use copy2 to copy to temp folder rather than copytree
			if os.path.isfile(Source) is True:
				copy2(Source,TempBackupFolder)
				print "Copied %s to %s" % (Source,TempBackupFolder)
			else:
				print TempBackupFolder+Source.split("\\")[1]+"\\"
				os.makedirs(TempBackupFolder+Source.split("\\")[1]+"\\")
				copytree(Source,TempBackupFolder+Source.split("\\")[1]+"\\",False,ignore_patterns("*.lock"))
		except:
			print Source, "does not exist. Skipping..."
	print "\nCopy finished, archive started: " + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M")
	send_sms("Copy finished, archive started. " + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M"))
	# Archive the copied contents
	archive(TempBackupFolder)
	print "Archive finished:", datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M")
	# Remove temp folder after archive has finished
	try:
		rmtree(TempBackupFolder)
		print TempBackupFolder, "was removed."
		# Send sms if backup was successful
		send_sms("Other backup was successful. " + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M"))
	except Exception, err:
		print TempBackupFolder, "was not removed!"
		print sys.exc_info()[0]
		# Send sms if backup was successful
		send_sms("Other backup was successful, but temp folder was not removed. " + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M"))
except Exception, err: # In the event error, a message is sent
	print sys.exc_info()[0]
	send_sms("Other backup failed! " + datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M")+" PLEASE REMEDIATE IMMEDIATELY!")


# Reset sys.stdout
sys.stdout = sys.__stdout__
# Close and move log file to remote backup location
log.close()
move(LocalBackupFolder+logFile,RemoteBackupDrive+logFile)
