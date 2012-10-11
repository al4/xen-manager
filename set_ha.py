#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass, ConfigParser
import XenAPI

import pprint # for debugging

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
	print password + str(type(password))
	if password == None:
		# Clearly hasn't been set, prompt
		password = getpass.getpass("Root password: ")

# Get defaults:
default_restart_priority = config.get('HA Defaults', 'restart_priority')
default_start_order = config.get('HA Defaults', 'start_order')
default_start_delay = config.get('HA Defaults', 'start_delay')

# Set session to None so we can test if it's been initialised
session = None

# Right, let's get down to the main class...
class virtual_machine:
	def __init__(self, name):
		# We set the name on initialisation
		self.name = name
		# Does the VM exist in Xen? If so set the class values to match.
		# TODO

	#### Setting and Getting methods ###
	# "setting" methods we are simply taking input and setting the value in the class and Xen
	# "getting" methods we are computing or parsing the value somehow
	# "read" methods get the current settings from Xen and set them in the class

	def set_name(self, name):
		# Simple class to set the name (we don't write this back to Xen, only use it for input)
		self.name = name
		return 0

	def set_order(self, order):
		self.order = order
		print "Setting order to " + str(order)
		session.xenapi.VM.set_order(self.id, str(order))

	def set_priority(self, priority):
		# Sets the priority by
		self.priority = priority

		print "Setting ha_restart_priority to " + str(priority)

		session.xenapi.VM.set_ha_restart_priority(self.id, "restart")

	def set_delay(self, delay):
		# set the delay attribute
		self.delay = delay
		print "Setting start_delay for " + self.name + " to " + str(delay)
		session.xenapi.VM.set_start_delay(self.id, str(delay))	# <- documentation says int but you get FIELD_TYPE_ERROR if you pass an integer here, happy when converted to str

		return 0

	def set_cluster(self, cluster_name):
		# set the cluster attribute
		self.cluster = cluster_name
		return 0

	def get_cluster(self):
		# get the cluster name by reading the CSV file
		#
		#
		#
		# lots of code goes here

		cluster = "foo"
		self.set_cluster(cluster)

	def get_implant(self):
		# get the implant from DNS TXT record
		return 0

	def set_machine_id(self, id):
		# Set the machine ID (probably won't know this without calling get_machine_id)
		self.id = id
		return 0

	def get_machine_id(self):
		# Function to get the machine ID from Xen based on the name. Names should be unique so we
		# throw an error if there is more than 1 match.
		ids = session.xenapi.VM.get_by_name_label(self.name)
		print self.name + " " + str(ids)

		if len(ids) != 1:
			print "Error: VM name had more than one match"
			exit()

		self.set_machine_id(ids[0])

		return ids[0]


xenurl = "https://" + host
print "API URL: " + xenurl

# Connect and auth
session = XenAPI.Session(xenurl)
session.xenapi.login_with_password(username, password)

#### Code goes here...

vm = virtual_machine("alex1")
myid = vm.get_machine_id()
vm.set_machine_id(myid)
vm.set_delay(10)

####

print "Logging out..."
session.xenapi.session.logout()

exit()
