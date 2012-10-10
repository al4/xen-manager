#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass

import XenAPI


# void set_ha_restart_priority (VM ref, string)
# Set the value of the ha_restart_priority field
# Parameters:	VM ref self	The VM
# 	string value	The value
# Minimum role:	pool-operator
# Published in:	XenServer 5.0	Set the value of the ha_restart_priority field

# int start_delay [read-only]
# The delay to wait before proceeding to the next order in the startup sequence (seconds)
# Default value:	0
# Published in:	XenServer 6.0	The delay to wait before proceeding to the next order in the startup sequence (seconds)

# Build commandline argument parser
parser = argparse.ArgumentParser(description='Set HA properties of a VM')
parser.add_argument("host", help="Host server")
parser.add_argument("name", help="Name of the VM to manage")
parser.add_argument("--priority", "-p", type=int, help="Order in which the VM is restarted (1=first, 100=last)")
parser.add_argument("--delay", "-d", type=int, help="Restart delay")
parser.add_argument("--password", help="root password for Xen Server")

args = parser.parse_args()

# Variables - declarations not need in Python, so most are only to document:
user		=	"root" 			# Our edition doesn't have user management so always need to auth as root. Can easily add as an argument later.
host 		= 	args.host
priority 	=	args.priority 	# HA Priority
delay 		= 	args.delay 		# HA Delay

# Conditional (optional) variables:

if not args.password: 			# Password for API authentication
	password = getpass.getpass("Root password: ")
else:
	password = str(args.password)

if not args.host:				# Host we send the API calls to
	# TODO: auto-detect from a list of servers
	host = raw_input("Xen Host: ")
	# raw_input deprecated in Python 3.x, change to input http://docs.python.org/py3k/whatsnew/3.0.html#builtins
else:
	host = args.host

print ("VM Name: " + str(args.name))
print ("HA Priority: " + str(args.priority))
print ("HA Delay: " + str(args.delay))

# We have all we need, open a Xen session
xenurl = "https://" + host
print "API URL: " + xenurl

# Connect and auth
session = XenAPI.Session(xenurl)
session.xenapi.login_with_password(user, password)

print vars(session)

#### Code goes here...
vms = session.xenapi.VM.get_by_name_label('alex1')
print "Alex1" + str(vms)



####

print "Logging out..."
session.xenapi.session.logout()

exit()






session.xenapi_request(VM.suspend())


dir(handle)

exit()

print vars(session)

# Print list of hosts
hostIDs = session.xenapi.host.get_all()								# <- results in an array of UUIDs
hostlist = [session.xenapi.host.get_name_label(x) for x in hostIDs]	# <- getting the name of each host

#print "Host List: " + ', '.join(hostlist)

session.xenapi_request(VM.suspend())

# for x in hostIDs:
# 	print "Host: " + session.xenapi.host.get_name_label(x)
# 	print "\t - "


# Set HA Priority of given VM
# vmlabel = session.xenapi.VM.get_by_name_label vm

# print var(vmlabel)









