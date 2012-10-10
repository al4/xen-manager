#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass

import XenAPI

import pprint # for debugging

# XenAPI doc: http://docs.vmd.citrix.com/XenServer/6.0.0/1.0/en_gb/api/

# void set_start_delay (VM ref, int)
# Set this VM's start delay in seconds
# void set_order (VM ref, int)
# Set this VM's boot order

# Build commandline argument parser
parser = argparse.ArgumentParser(description='Set HA properties of a VM')
parser.add_argument("host", help="Host server")
parser.add_argument("name", help="Name of the VM to manage")
parser.add_argument("--password", help="root password for Xen Server")
parser.add_argument("--priority", "-p", type=str, help='HA restart Priority [""/"restart"/"best-effort"] ("restart" by default')
parser.add_argument("--delay", "-d", type=int, help="The delay to wait before proceeding to the next order in the startup sequence (seconds)")
parser.add_argument("--order", "-o", type=int, help="The point in the startup or shutdown sequence at which the VM will be started")

args = parser.parse_args()

# Variables - declarations not need in Python, so most are only to document:
user		=	"root" 			# Our license doesn't have user management so always need to auth as root. Can easily add as an argument later.
host 		= 	args.host
vmname		=	args.name 		# Name of VM to manage
priority 	=	args.priority 	# HA priority
delay 		= 	args.delay 		# HA Start delay
order 		=	args.order 		# HA Start order

# Conditional (optional) variables:

if not args.priority:
	# Set this to a sensible default
	priority = "restart"

if not args.order and not args.delay:
	print "Must set order or delay"
	exit()

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

print ("VM Name: " + vmname)
print ("Start order: " + str())
print ("HA Priority: " + str(priority))
print ("HA Delay: " + str(delay))

# We have all we need, open a Xen session
xenurl = "https://" + host
print "API URL: " + xenurl

# Connect and auth
session = XenAPI.Session(xenurl)
session.xenapi.login_with_password(user, password)

#### Code goes here...
vms = session.xenapi.VM.get_by_name_label(vmname)
print vmname + " " + str(vms)

# check length to ensure we are only setting 1 vm
# if len(vms) > 1:
# print "error: " + str(len(vms))

# set HA for this VM
print "Setting ha_restart_priority to " + str(priority)
#print session.xenapi.VM.get_record(vms[0])
session.xenapi.VM.set_ha_restart_priority(vms[0], "restart")

print "Setting start_delay to " + str(delay)
session.xenapi.VM.set_start_delay(vms[0], str(delay))	# <- documentation says int but you get FIELD_TYPE_ERROR if you pass an integer here, happy when converted to str

print "Setting order to " + str(order)
session.xenapi.VM.set_order(vms[0], str(order))

####

print "Logging out..."
session.xenapi.session.logout()

exit()
