#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass

import lib.XenAPI

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

print ("VM Name: " + str(args.name))
print ("HA Priority: " + str(args.priority))
print ("HA Delay: " + str(args.delay))

if not args.password:
	pwd = getpass.getpass("Root password: ")
else:
	pwd = str(args.password)

if not args.host:
	# TODO: auto-detect from a list of servers
	host = raw_input("Xen Host: ")

	# raw_input deprecated in Python 3.x, change to input http://docs.python.org/py3k/whatsnew/3.0.html#builtins
	#var = raw_input("Enter root password: ")
else:
	host = args.host


# We have all we need, open a Xen session
xenurl = "https://" + host
print "API URL: " + xenurl

session = XenAPI.Session(url)
session.xenapi.login_with_password(username, password)
