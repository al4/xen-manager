#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass, ConfigParser, csv
import XenAPI

import pprint # for debugging
pp = pprint.PrettyPrinter(indent=2) # for debugging

# XenAPI doc: http://docs.vmd.citrix.com/XenServer/6.0.0/1.0/en_gb/api/

# Build commandline argument parser
parser = argparse.ArgumentParser(description='Sets HA properties across our Xen cluster')
parser.add_argument("--password", "-p", help="root password for Xen Server (uses config if not set)")
parser.add_argument("--file", "-f", help="CSV file to parse values from (see comments for format)")

args = parser.parse_args()

config = ConfigParser.RawConfigParser()
config.read('xen_manage.cfg')

username	=	config.get('Connection', 'username') 	# Our license doesn't have user management so always need to auth as root. Can easily add as an argument later.
host 		= 	config.get('Connection', 'host')		# API sever we're connection to (the Xen master)

if not args.password:
	password = config.get('Connection', 'password')		# Don't commit this to VCS...
	if password == None:
		# Clearly hasn't been set, prompt
		password = getpass.getpass("Root password: ")

# Get defaults:
default_ha_restart_priority = config.get('HA Defaults', 'restart_priority')
default_order = config.get('HA Defaults', 'order')
default_start_delay = config.get('HA Defaults', 'start_delay')

# Set session to None so we can test if it's been initialised
session = None

def error(message):
	# Throw message and exit
	print "ERROR: " + str(message)
	print "Logging out..."
	session.xenapi.session.logout()
	exit()

def notify(messge):
	# Notify user but don't quit
	print "NOTICE: " + str(message)

# Right, let's get down to the main class...
class virtual_machine:
	def __init__(self, name):
		# We set the name on initialisation
		self.name = name

		# Get the ID from the name
		self.id = self.read_id()

		# Get the rest of the attributes we need
		self.read_from_xen()

	#### Setting and Getting methods ###
	# "setting" methods simply take input and set the value in the class and Xen
	# "getting" methods return the current value
	# "read" methods get the current settings from Xen or CSV and set them in the class, they do not set them anywhere

	def set_name(self, name):
		# Simple class to set the name (we don't write this back to Xen, only use it for input)
		self.name = name
		return 0

	def read_id(self):
		# Function to get the machine ID from Xen based on the name. Names should be unique so we
		# throw an error if there is more than 1 match.
		ids = session.xenapi.VM.get_by_name_label(self.name)

		if len(ids) > 1:
			error("VM name has more than one match")
			exit()

		if len(ids) == 0:
			message = "VM " + self.name + " does not exist"
			notify(message)
			return 1

		print "Got ID for " + self.name + ": " + str(ids)

		#self.id = ids[0]
		return ids[0]

	def read_from_xen(self):
		# Reads all required values from Xen and sets them in the class
		try:
			data = session.xenapi.VM.get_record(self.id)
			#pp.pprint(data)

		except:
			error("Failed to read VM data from Xen cluster")

		# Now we just need to parse the values we need and set in the class. Might useful:
		# ha_restart_priority, start_delay, power_state, ha_always_run,
		print "Got record: "
		print " - power_state: " + str(data['power_state'])
		self.power_state = str(data['power_state'])
		print " - ha_restart_priority: " + str(data['ha_restart_priority'])
		self.ha_restart_priority = str(data['ha_restart_priority'])
		print " - start_delay: " + str(data['start_delay'])
		self.start_delay = str(data['start_delay'])
		print " - order: " + str(data['order'])
		self.order = str(data['order'])

		return 0

	def set_order(self, order):
		self.order = order
		print "Setting order for " + self.name + " to " + str(order)
		session.xenapi.VM.set_order(self.id, str(order))

	def get_order(self):
		return self.order

	def set_ha_restart_priority(self, priority):
		# Sets the priority. Can be "best-effort", "restart", or ""
		self.ha_restart_priority = priority
		print "Setting ha_restart_priority to " + str(priority)
		session.xenapi.VM.set_ha_restart_priority(self.id, "restart")
		return 0

	def get_ha_restart_priotiry(self):
		return self.ha_restart_priority

	def set_start_delay(self, start_delay):
		# set the delay attribute
		self.start_delay = start_delay
		print "Setting start_delay for " + self.name + " to " + str(start_delay)
		session.xenapi.VM.set_start_delay(self.id, str(start_delay))	# <- documentation says int but you get FIELD_TYPE_ERROR if you pass an integer here, happy when converted to str
		return self.start_delay

	def get_start_delay(self):
		return self.start_delay

	def set_cluster(self, cluster_name):
		# set the cluster attribute
		self.cluster = cluster_name
		return 0

	def get_cluster(self):
		# get the cluster name by reading the CSV file
		#
		# not sure if this is the right way to do it, logic should probably be outside of class
		#
		#

		cluster = "foo"
		self.set_cluster(cluster)
		return self.cluster

	def get_implant(self):
		# get the implant from DNS TXT record
		return 0




### Sequential Logic
# Use a try:finally around anything which calls XenAPI to ensure we logout

# try:
# Connect and auth
xenurl = "https://" + host
session = XenAPI.Session(xenurl)
session.xenapi.login_with_password(username, password)

# Open CSV files for reading
priorities_file = config.get('Input', 'priorities_file')

with open (priorities_file, 'rb') as csvfile:
	reader = csv.reader(csvfile, delimiter=' ')

	for row in reader:
		pp.pprint(row)
		vmname = row[1]
		order = int(row[0])		# We set as string but this should be an int for comparisons (and eliminates leading 0's)
		priority = "restart"	# Hard-coded for now as we're not defining or computing anywhere

		try:
			# Instantiate vm object. This also gets the values we need from the server and sets them
			vm = virtual_machine(vmname)
		except:
			error("Failed to create vm object")

		print "foo: " + str(order)
		# Check order and set if not what it should be
		current_order = vm.get_order()

		if int(order) != int(current_order):
			print "Changing order on " + vmname + " from " + str(current_order) + " to " + str(order)
			vm.set_order(str(order))


# finally:

print "Logging out..."
session.xenapi.session.logout()

exit()











