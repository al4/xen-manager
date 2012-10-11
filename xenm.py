#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass, ConfigParser, csv
import XenAPI

import pprint # for debugging
pp = pprint.PrettyPrinter(indent=2) # for debugging

# XenAPI doc: http://docs.vmd.citrix.com/XenServer/6.0.0/1.0/en_gb/api/

# Set session to None so we can test if it's been initialised without throwing an exception
session = None

# Housekeeping functions. TODO - implement proper logging
def error(message):
	# Throw message and exit
	print "ERROR: " + str(message)
	disconnect()

def notify(message):
	# Notify user but don't quit
	print "NOTICE: " + str(message)

def disconnect():
	if session != None:
		print "Logging out..."
		session.xenapi.session.logout()
	exit()

# Right, let's get down to the main class...
class virtual_machine:
	def __init__(self, name):
		# We only set the name on initialisation
		self.name = name

		# Get the ID from the name
		#self.id = self.read_id() 	# Don't do this in the constructor any more because we need to be able to test whether the
									# machine exists before we do something that throws an error

		# Get the rest of the attributes we need
		# self.read_from_xen()

	#### Setting and Getting methods ###
	# "setting" methods simply take input and set the value in the class and Xen
	# "getting" methods return the current value
	# "read" methods get the current settings from Xen or CSV and set them in the class, they do not set them anywhere

	def dump_attrs(self):
		# For debugging, must be a built-in way to do this but I'm not familiar enough with Python yet...
		print "name: " + self.name
		print "id: " + self.id
		print "power_state: " + self.power_state
		print "ha_restart_priority: " + self.ha_restart_priority
		print "start_delay: " + self.start_delay
		print "order: " + self.order
		return 0

	def set_name(self, name):
		# Simple class to set the name (we don't write this back to Xen, only use it for input)
		self.name = name
		return 0

	def read_id(self):
		# Function to get the machine ID from Xen based on the name. Names should be unique so we
		# throw an error if there is more than 1 match.
		try:
			ids = session.xenapi.VM.get_by_name_label(self.name)
		except:
			message = "XenAPI threw exception trying to get ID"
			notify(message)
			return 1

		if len(ids) > 1:
			# This is bad, delete the offending VM! In future we may want to continue anyway and set parameters on both
			# for automated scenarios
			message = "VM name \"" + self.name + "\" has more than one match!"
			notify(message)
			return 1

		if len(ids) == 0:
			message = "VM \"" + self.name + "\" does not exist"
			notify(message)
			return 1

		self.id = ids[0]
		#print "Got ID for " + self.name + ": " + str(ids)
		return ids[0]

	def read_from_xen(self):
		# Reads all required values from Xen and sets them in the class
		try:
			data = session.xenapi.VM.get_record(self.id)
			#pp.pprint(data)
		except:
			# If the XenAPI throws an exception, notify and return 1
			notify("Failed to read VM data from Xen server")
			return 1

		# Parse the values we need and set them in the class. Might be useful:
		# 	ha_restart_priority, start_delay, power_state, order

		# Remember to add a get_ (and possibly set_) method for each field we track

		print "Found VM \"" + self.name + "\":"

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


### Functions for the sub-commands
def action_start():
	message= "not implemented yet"
	error(message)

def action_stop():
	message="not implemented yet"
	error(message)

def action_restart():
	message="not implemented yet"
	error(message)

def action_remove():
	message="not implemented yet"
	error(message)

def action_spawn():
	message="not implemented yet"
	error(message)

def action_respawn():
	message="not implemented yet"
	error(message)

def action_enforce():
	message="not implemented yet"
	error(message)

def action_enforce_all():
	# Enforces HA policy on all VMs.

	# Open CSV file for reading
	with open (vm_list, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=' ')

		# Loop over each entry
		for row in reader:
			#pp.pprint(row)
			vmname = row[1]
			order = int(row[0])		# We set as string but this should be an int for comparisons (and eliminates leading 0's)
			priority = "restart"	# Hard-coded for now as we're not defining or computing anywhere

			# Instantiate vm object
			vm = virtual_machine(vmname)

			# Check if the VM exists
			if vm.read_id() == 1:
				# Move on to next loop iteration, notices should have been printed by vm.read_id
				continue

			print 'Found "' + vmname + '", getting attributes'
			vm.read_from_xen()

			# vm.dump_attrs()

			# Check order and set if not what it should be
			current_order = vm.get_order()

			if int(order) != int(current_order):
				print "Changing order on " + vmname + " from " + str(current_order) + " to " + str(order)
				vm.set_order(str(order))

### Now that the functions and classes are defined, do some work:

# First we need to parse the commandline arguments. We use Python's argparse.
parser = argparse.ArgumentParser(description='Manages our Xen cluster', add_help=False)
# parser.add_argument('action', help="action to perform")
parser.add_argument("--password", "-p", help="root password for Xen Server (uses config if not set)")
parser.add_argument("--configfile", "-c", help="config file to use (xenm.cfg by default)")

# We setup subparsers for each mode
subparsers = parser.add_subparsers(dest='action')

# Parent parser for modes which operate on a single VM
parent_parser_onevm = argparse.ArgumentParser(add_help=False)
parent_parser_onevm.add_argument('vmname', help='name of VM to perform action on')
parent_parser_onevm.add_argument('--host', help='Xen server host to connect to (must be the master of the cluster)')

# Parent for modes which operate on multiple VMs
parent_parser_multivm = argparse.ArgumentParser(add_help=False)
parent_parser_multivm.add_argument('--vmlist', help='CSV file with a list of VMs and priorities')

# The subparsers, which should include one of the parents above
parser_start = subparsers.add_parser('start', help='starts a VM', parents=[parent_parser_onevm])
parser_start.set_defaults(func=action_start)
parser_stop = subparsers.add_parser('stop', help='stops a VM', parents=[parent_parser_onevm])
parser_stop.set_defaults(func=action_stop)
parser_restart = subparsers.add_parser('restart', help='restarts a VM', parents=[parent_parser_onevm])
parser_restart.set_defaults(func=action_restart)
parser_remove = subparsers.add_parser('remove', help='removes a VM', parents=[parent_parser_onevm])
parser_remove.set_defaults(func=action_remove)
parser_spawn = subparsers.add_parser('spawn', help='spawns a new VM', parents=[parent_parser_onevm])
parser_spawn.set_defaults(func=action_spawn)
parser_respawn = subparsers.add_parser('respawn', help='removes and spawns a new copy of a VM', parents=[parent_parser_onevm])
parser_respawn.set_defaults(func=action_respawn)
parser_enforce = subparsers.add_parser('enforce', help='enforce the HA policy on one VM', parents=[parent_parser_onevm])
parser_enforce.set_defaults(func=action_enforce)
parser_enforce_all = subparsers.add_parser('enforce-all', help='check the HA policy on all VMs and enforce the policy (config must be set)', parents=[parent_parser_multivm])
parser_enforce_all.set_defaults(func=action_enforce_all)

args = parser.parse_args()

# Get config options from xenm.cfg if not set on command line
config = ConfigParser.RawConfigParser()

# If we haven't specified config file on command line, use default
if not args.configfile:
	configfile = 'xenm.cfg'
else:
	configfile = args.configfile

# Check our config file exists
if os.path.isfile(configfile):
	config.read(configfile)
else:
	message = 'Config file "' + str(configfile) + '" does not exist'
	error(message)

host = config.get('Connection', 'host')
username = config.get('Connection', 'username') 	# Our license doesn't have user management so always need to auth as root. Can easily add as an argument later.
password = config.get('Connection', 'password')

# Override if set on command line
if args.host:
	host = args.host

if args.password:
	password = args.password

# Get defaults (not sure if we'll use these):
default_ha_restart_priority = config.get('HA Defaults', 'restart_priority')
default_order = config.get('HA Defaults', 'order')
default_start_delay = config.get('HA Defaults', 'start_delay')

try:
	vm_list = config.get('Input', 'vm_list')
	implants_file = config.get('Input', 'implants_file')
except:
	error("Failed to parse config")

# Check the files specified are present
if not os.path.isfile(vm_list):
	message = 'Config file "' + str(configfile) + '" does not exist'
	error(message)

# Connect and auth
xenurl = "https://" + host
print "Connecting to Xen Server..."
try:
	session = XenAPI.Session(xenurl)
	session.xenapi.login_with_password(username, password)
except:
	error("Failed to connect to the Xen server")

# Now that we're connected we can calls the function select by args (func=)
args.func()

disconnect()

exit()





exit()





