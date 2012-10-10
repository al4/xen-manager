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
	if password = '':
		# Clearly hasn't been set, prompt
		password = getpass.getpass("Root password: ")

# Get defaults:
default_restart_priority = config.get('HA Defaults', 'restart_priority')
default_start_order = config.get('HA Defauls', 'start_order')
default_start_delay = config.get('HA Defaults', 'start_delay')

# Set session to None so we can test if it's been initialised
session = None

# Right, let's get down to the main class...
class virtual_machine:
	def __init__(self, name):
		# We set the name on initialisation
		self.name = name

	def set_name(name):
		# Simple class to set the name (we don't write this back to Xen, only use it for input)
		self.name = name
		return 0

	def set_order(order):
		self.order = order
		print "Setting order to " + str(order)
		session.xenapi.VM.set_order(self.id, str(order))

	def set_priority(priority):
		# Sets the priority by
		self.priority = priority

		print "Setting ha_restart_priority to " + str(priority)

		session.xenapi.VM.set_ha_restart_priority(self.id, "restart")

	def set_delay(delay):
		# set the delay attribute
		self.delay = delay
		print "Setting start_delay to " + str(delay)
		session.xenapi.VM.set_start_delay(self.id, str(delay))	# <- documentation says int but you get FIELD_TYPE_ERROR if you pass an integer here, happy when converted to str

		return 0

	def set_cluster(cluster_name):
		# set the cluster attribute
		self.cluster = cluster_name
		return 0

	def get_cluster():
		# get the cluster name by reading the CSV file
		#
		#
		#
		# lots of code goes here

		cluster = "foo"
		self.set_cluster(cluster)


	def set_machine_id(id):
		# Set the machine ID (probably won't know this without calling get_machine_id)
		self.id = id
		return 0

	def get_machine_id:
		# Function to get the machine ID from Xen based on the name. Names should be unique so we
		# throw an error if there is more than 1 match.
		ids = session.xenapi.VM.get_by_name_label(vmname)
		print vmname + " " + str(ids)

		if len(ids) != 1:
			print "Error: VM name had more than one match"
			exit()

		self.set_machine_id(ids[0])

		return ids[0]

# # Connection class... necessary?
# class connection:
# 	# Defines the connection to the Xen server and provides methods for logging in and logging out
# 	def __init__(self,host,username,password):
# 		# do something
# 	def connect():
# 	def login():
# 		# login to the server, returns a session object
# 	def logout():
# 		# logout from the server

xenurl = "https://" + host
print "API URL: " + xenurl

# Connect and auth
session = XenAPI.Session(xenurl)
session.xenapi.login_with_password(username, password)

#### Code goes here...



####

print "Logging out..."
session.xenapi.session.logout()

exit()
