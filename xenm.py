#!/usr/bin/python

import os, sys, inspect, time, argparse, getpass, ConfigParser, csv
import XenAPI

# Our modules
from class_vm import virtual_machine

import pprint # for debugging
pp = pprint.PrettyPrinter(indent=2) # for debugging

# XenAPI doc: http://docs.vmd.citrix.com/XenServer/6.0.0/1.0/en_gb/api/

### Housekeeping functions. TODO - implement proper logging
def error(message):
	# Throw message and exit
	print "ERROR: " + str(message)
	# disconnect()
	exit()

def notify(message):
	# Notify user but don't quit
	print "NOTICE: " + str(message)

# def disconnect():
# 	if session != None:
# 		print "Logging out..."
# 		session.xenapi.logout()
# 	exit()

### Functions for the sub-commands
def action_list():
	# This function should list all virtual machines

	# First instantiate a dummy virtual_machine object to get a connection
	myvm = virtual_machine("dummy")
	myvm.connect_host(host, username, password)

	try:
		# Find a non-template VM object
		all = myvm.session.xenapi.VM.get_all()
		# Lists which we read from
		data=[['name_label', 'power_state', 'restart_priority', 'start_delay', 'order']]

		# Build a list of VMs
		for vm in all:
			record = myvm.session.xenapi.VM.get_record(vm)
			if not(record["is_a_template"]) and not(record["is_control_domain"]) and record["power_state"] == "Running":
				data.append([record["name_label"],record["power_state"],record["ha_restart_priority"],record["start_delay"],record["order"]])

		col_width = max(len(word) for row in data for word in row) + 2

		for row in data:
			print "".join(word.ljust(col_width) for word in row)
		# print "Name\tPower State\t"
		# for n, p, r, s, o in zip(names, powerstates, restart_priorities, start_delays, orders):
		# 	print '{0}\t{1}\t{2}:{3}:{4}'.format(n,p,r,s,o)
	finally:
		myvm.disconnect_host()

def action_start():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			result = vm.start()
			if result == 0:
				print "Start succeeded"
			else:
				error(result)
		else:
			return check_result
	finally:
		vm.disconnect_host()

def action_stop():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			result = vm.clean_shutdown()
			if result == 0:
				print "Stop succeeded"
			else:
				error(result)
		else:
			return check_result
	finally:
		vm.disconnect_host()

def action_restart():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			result = vm.clean_reboot()
			if result == 0:
				print "Restart succeeded"
			else:
				error(result)
		else:
			return check_result
	finally:
		vm.disconnect_host()

def action_remove():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			pass
		else:
			return check_result
	finally:
		vm.disconnect_host()

	error("not implemented yet")

def action_spawn():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			pass
		else:
			return check_result
	finally:
		vm.disconnect_host()

	error("not implemented yet")

def action_respawn():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			pass
		else:
			return check_result
	finally:
		vm.disconnect_host()

	error("not implemented yet")

def action_enforce():
	# Get name from args
	vmname = args.vmname

	try:
		# Create new VM object and connect
		vm = virtual_machine(vmname)
		vm.connect_host(host, username, password)

		check_result = vm.preflight()
		if check_result == 0:
			pass
		else:
			return check_result
	finally:
		vm.disconnect_host()

	error("not implemented yet")

def action_enforce_all():
	# Enforces HA policy on all VMs.
	# This function has to do a lot of the heavy lifting itself

	# Open CSV file for reading
	with open (vm_list, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=' ')

		# Loop over each entry
		for row in reader:
			#pp.pprint(row)
			vmname = row[1]
			order = int(row[0])		# We set as string but this should be an int for comparisons (and eliminates leading 0's)
			priority = "restart"	# Hard-coded for now as we're not defining or computing anywhere

			try:
				# Create new VM object
				vm = virtual_machine(vmname)
				vm.connect_host(host, username, password)

				# Check if the VM exists
				check_result = vm.preflight()
				if check_result != 0:
					notify(check_result)
					# stop this iteration if we can't find the VM
					continue

				# Check order and set if it is not what it should be
				current_order = vm.get_order()

				if int(order) != int(current_order):
					print "Changing order on " + vmname + " from " + str(current_order) + " to " + str(order)
					vm.set_order(str(order))
			finally:
				vm.disconnect_host()

### Now that the functions are defined, do some work

# First we need to parse the commandline arguments. We use Python's argparse.

parser = argparse.ArgumentParser(description='Manages our Xen cluster', add_help=False)
# parser.add_argument('action', help="action to perform")
parser.add_argument("--password", "-p", help="root password for Xen Server (uses config if not set)")
parser.add_argument("--configfile", "-c", help="config file to use (xenm.cfg by default)")
parser.add_argument('--host', help='Xen server host to connect to (must be the master of the cluster)')

# Default options. It is reasonable to guess configfile, but host should be explicit in config or as argument
parser.set_defaults(configfile='xenm.cfg', host=None, password=None)

# We setup subparsers for each mode
subparsers = parser.add_subparsers(dest='action')

# Parent parser for modes which operate on a single VM
parent_parser_onevm = argparse.ArgumentParser(add_help=False)
parent_parser_onevm.add_argument('vmname', help='name of VM to perform action on')
parent_parser_onevm.set_defaults(vmname=None)

# Parent for modes which operate on multiple VMs
parent_parser_multivm = argparse.ArgumentParser(add_help=False)
parent_parser_multivm.add_argument('--vmlist', help='CSV file with a list of VMs and priorities')
parent_parser_multivm.set_defaults(vmlist=None)

# The subparsers, which should include one of the parents above
parser_start = subparsers.add_parser('list', help='list all VMs')
parser_start.set_defaults(func=action_list)
parser_start = subparsers.add_parser('start', help='starts a VM', parents=[parent_parser_onevm])
parser_start.set_defaults(func=action_start)
parser_stop = subparsers.add_parser('stop', help='performs a clean shutdown', parents=[parent_parser_onevm])
parser_stop.set_defaults(func=action_stop)
parser_restart = subparsers.add_parser('restart', help='performs a clean reboot', parents=[parent_parser_onevm])
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
username = config.get('Connection', 'username')
password = config.get('Connection', 'password')

# Override if set on command line
if args.host != None:
	host = args.host
if args.password != None:
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
	message = 'File "' + str(vm_list) + '" does not exist'
	error(message)

# Call the function selected by set_default(func=)
args.func()

exit()





