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
	# Polls all Xen servers to gather data
	# First instantiate a dummy virtual_machine object to get a connection

	# Lists which we append to (start with headings in first row)
	data_vms=[['name_label', 'pool', 'power_state', 'restart_priority', 'start_delay', 'order']]

	for host in hosts:
		# First instantiate a dummy virtual_machine object to get a connection
		myvm = virtual_machine("dummy", verbose)
		myvm.connect_host(host, username, password)

		try:
			# Get pools - ASSUMING ONLY ONE POOL PER HOST
			pools = myvm.session.xenapi.pool.get_all()
			if len(pools) > 1: error("Expecting only one pool on a host")

			# Get the name of the pool on this host
			pool = myvm.session.xenapi.pool.get_record(pools[0])
			pool_name = pool["name_label"]

			if verbose:
				print "Getting VMs from " + host + "..."

			vms = myvm.session.xenapi.VM.get_all()

			# Build a list of VMs that are not templates or control domains
			for vm in vms:
				record = myvm.session.xenapi.VM.get_record(vm)
				if not(record["is_a_template"]) and not(record["is_control_domain"]):
					data_vms.append([record["name_label"],pool_name,record["power_state"],record["ha_restart_priority"],record["start_delay"],record["order"]])
		finally:
			myvm.disconnect_host()

	if verbose: print ""
	col_width = max(len(word) for row in data_vms for word in row) + 2

	for row in data_vms:
		print "".join(word.ljust(col_width) for word in row)

	return data_vms

def action_pools():
	# This function should list all pools

	data_pools=['name_label']

	for host in hosts:
		# First instantiate a dummy virtual_machine object to get a connection
		myvm = virtual_machine("dummy", verbose)
		myvm.connect_host(host, username, password)

		try:
			# Get pools - ASSUMING ONLY ONE POOL PER HOST
			pools = myvm.session.xenapi.pool.get_all()
			if len(pools) > 1: error("Expecting only one pool on a host")

			# Get the name of the pool on this host
			pool = myvm.session.xenapi.pool.get_record(pools[0])
			pool_name = pool["name_label"]

			data_pools.append(pool_name)

		finally:
			myvm.disconnect_host()

	if verbose: print "" # Add line between verbose messages and output - looks neater

	for row in data_pools:
		print row

	return data_pools

def action_start():

	global vmname
	global host

	vmname = args.vmname
	host = get_host(vmname)

	# Create new VM object and connect
	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)

	try:
		result = power_on(vm)
	finally:
		vm.disconnect_host()

	return result

def power_on(vm):
	check_result = vm.preflight()
	if check_result == 0:
		print "Starting " + vm.name + "..."
		result = vm.start()
		if result == 0:
			print "Start succeeded"
		else:
			error(result)
	else:
		return check_result
	return 0

def action_stop():
	global vmname
	global host

	vmname = args.vmname
	host = get_host(vmname)

	if host == None:
		error("VM does not exist")

	# Create new VM object and connect
	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)

	try:
		result = shutdown(vm)
	finally:
		vm.disconnect_host()

def shutdown(vm):
	check_result = vm.preflight()
	if check_result == 0:
		print "Stopping " + vm.name + "..."
		result = vm.clean_shutdown()
		if result == 0:
			print "Stop succeeded"
		elif result == 1:
			notify("VM is not running")
		else:
			error("Unknown error")
	else:
		return check_result
	return 0

def action_restart():
	global vmname
	global host

	vmname = args.vmname
	host = get_host(vmname)

	# Create new VM object and connect
	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)

	try:
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
	# CURRENTLY DOES NOT REMOVE DISKS

	global vmname
	global host

	# Get name from args
	vmname = args.vmname
	host = get_host(vmname)

	if host == None:
		error("VM does not exist")

	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)

	try:
		shutdown(vm)
		destroy(vm)
	finally:
		vm.disconnect_host()

def destroy(vm):

	vm.read_id()
	vm.read_from_xen()

	print "Removing " + vmname + " from " + host + "..."

	result = vm.destroy()
	if result == "":
		print "Remove succeeded"
		return 0
	else:
		return result



def action_spawn():
	# Function to spawn a new VM from template
	# Template is defined in config, could make an optional argument at some point

	global vmname
	global host

	# Get name from args, it is required from the CLI for this function
	vmname = args.vmname

	# for spawn, we can only work with a single host
	if len(hosts) > 1:
		error("Spawn requires that only one host is set, define a single host on the command line with the --host option")
	host = hosts[0]

	# object for new vm - new so we don't fetch any attrs
	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)

	# object for the template (to get the ID and make sure it is valid)
	mytemplate = virtual_machine(template, verbose)
	mytemplate.connect_host(host, username, password)

	# get the template attributes from xen into the object
	mytemplate.read_id()
	mytemplate.read_from_xen()

	try:
		clone_from_template(mytemplate, vm)
		set_ha_properties(vm)
		power_on(vm)
	finally:
		vm.disconnect_host()
		mytemplate.disconnect_host()

def clone_from_template(mytemplate, vm):
	# Make sure template VM is actually a template
	is_template = mytemplate.get_template_status()
	check_vm = vm.read_id()
	mytemplate.read_id()

	if len(str(check_vm)) == 46:
		error("VM already exists, try respawn")
	if is_template == False:
		error("Template VM given is not a template")
	elif is_template == True:
		# Create new VM object and connect
		vm = virtual_machine(vmname, verbose)
		vm.connect_host(host, username, password)

		print "Cloning " + template + " to " + vmname
		vm.clone(mytemplate.id)
		myid = vm.read_id()

		# Cloned VMs are made as templates, we need to set is_a_template to false
		vm.set_template_status(False)

	else: error("Unexpected return value from get_template_status")
	print "Clone successful"
	return 0

def action_respawn():
	global vmname
	global host
	global hosts

	# Get name from args
	vmname = args.vmname
	host = get_host(vmname)

	if host == None:
		error("VM does not exist")

	# Spawn requires that only one host is in the hosts array, so indulge it by overwriting the list with the output from get_host:
	del hosts
	hosts = [host]

	# Setup objects
	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)
	mytemplate = virtual_machine(template, verbose)
	mytemplate.connect_host(host, username, password)

	try:
		mytemplate.read_id()
		mytemplate.read_from_xen

		shutdown(vm)
		destroy(vm)
		clone_from_template(mytemplate, vm)
		set_ha_properties(vm)
		power_on(vm)
	finally:
		vm.disconnect_host
		mytemplate.disconnect_host

def action_enforce():
	global vmname
	global host

	vmname = args.vmname
	host = get_host(vmname)

	vm = virtual_machine(vmname, verbose)
	vm.connect_host(host, username, password)

	try:
		set_ha_properties(vm)
	finally:
		vm.disconnect_host()

def set_ha_properties(vm):
	print "Setting HA priorities..."
	count = 0

	with open(vmlist, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=' ')

		for row in reader:
			if row[1] == vmname:
				count += 1

				check_result = vm.preflight()
				if check_result == 0:
					# Check order and set if it is not what it should be
					current_order = vm.get_order()
					order = row[0]

					if int(order) != int(current_order):
						vm.set_order(str(order))
						if verbose: print "Changed order on " + vmname + " from " + str(current_order) + " to " + str(order)

				else:
					return check_result
			else:
				continue
		if count == 0:
			"Did not find entry for" + vm.name + " in " + vmlist + ", skipping ha config"

def action_enforce_all():
	global host
	# Enforces HA policy on all VMs.
	# This function has to do a lot of the heavy lifting itself

	# Open CSV file for reading
	with open (vmlist, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=' ')

		count = 0
		changed_vms=[]

		# Loop over each entry
		for row in reader:
			#pp.pprint(row)
			vmname = row[1]
			order = int(row[0])		# We set as string but this should be an int for comparisons (and eliminates leading 0's)
			priority = "restart"	# Hard-coded for now as we're not defining or computing anywhere

			vm = virtual_machine(vmname, verbose)

			for host in hosts:
				vm.connect_host(host, username, password)

				try:
					# Check if the VM exists
					check_result = vm.preflight()
					if check_result != 0:
						# stop this iteration if we can't find the VM
						continue

					# Check order and set if it is not what it should be
					current_order = vm.get_order()

					if int(order) != int(current_order):
						count += 1
						changed_vms.append(vmname)
						print "Changing order on " + vmname + " from " + str(current_order) + " to " + str(order)
						vm.set_order(str(order))
				finally:
					vm.disconnect_host()
		if count > 0:
			print "Changed " + str(count) + " VMs:"
			# for row in changed_vms:
			# 	print row
		else:
			print "No VMs changed"

def action_status():
	pass

## Helper functions

def get_host(vm_name):
	# Find the host a VM is on.
	# Input: vm name
	# Returns: host name

	if not str(vm_name): error("must pass vm_name to get_host")
	host_list = []

	for host in hosts:
		# First instantiate a dummy virtual_machine object to get a connection
		myvm = virtual_machine("dummy", verbose)
		myvm.connect_host(host, username, password)

		if verbose: print "Looking for " + vm_name + " on " + host
		try:
			# Get
			myvm_id = myvm.session.xenapi.VM.get_by_name_label(vmname)

			if len(myvm_id) == 1:
			 	host_list.append(host)

		finally:
			myvm.disconnect_host()

	if len(host_list) == 0:
		return None
	if len(host_list) > 1:
		return 1
	if len(host_list) == 1:
		if verbose: print "Found " + vm_name + " on " + host_list[0]
		return host_list[0]
	return 0

# First we need to parse the commandline arguments. We use Python's argparse.
parser = argparse.ArgumentParser(description='Manages our Xen cluster', add_help=False)

# parser.add_argument('action', help="action to perform")
parser.add_argument("--password", "-p", help="root password for Xen Server (uses config if not set)")
parser.add_argument("--configfile", "-c", help="config file to use (xenm.cfg by default)")
parser.add_argument('--hosts', help='Xen host(s) to connect to. These hosts must be the master of their cluster. Separate multiple hosts with commas.')
parser.add_argument('--verbose', '-v', action='store_true', help='print more output')

# Default options. It is reasonable to guess configfile, but host should be explicit in config or as argument
parser.set_defaults(configfile='xenm.cfg', hosts=None)

# We setup subparsers for each mode
subparsers = parser.add_subparsers(dest='action')

# Parent parser for modes which operate on a single VM
parent_parser_onevm = argparse.ArgumentParser(add_help=False)
parent_parser_onevm.add_argument('vmname', help='name of VM to perform action on')
# parent_parser_onevm.set_defaults(vmname=None)

# Parent for modes which operate on multiple VMs
parent_parser_multivm = argparse.ArgumentParser(add_help=False)
parent_parser_multivm.add_argument('--vmlist', help='CSV file with a list of VMs and priorities')
# parent_parser_multivm.set_defaults(vmlist=None)

# Parent for any option that uses a template
parent_parser_template = argparse.ArgumentParser(add_help=False)
parent_parser_template.add_argument('--template', '-t', help='name of template to use')
# parent_parser_template.set_defaults(template=None)

# The subparsers, which should include one of the parents above
parser_start = subparsers.add_parser('list', help='list all VMs')
parser_start = subparsers.add_parser('list-pools', help='list all pools')
parser_start = subparsers.add_parser('start', help='starts a VM', parents=[parent_parser_onevm])
parser_stop = subparsers.add_parser('stop', help='performs a clean shutdown', parents=[parent_parser_onevm])
parser_status = subparsers.add_parser('status', help='shows the status of a VM', parents=[parent_parser_onevm])
parser_restart = subparsers.add_parser('restart', help='performs a clean reboot', parents=[parent_parser_onevm])
parser_remove = subparsers.add_parser('remove', help='removes a VM', parents=[parent_parser_onevm])
parser_spawn = subparsers.add_parser('spawn', help='spawns a new VM', parents=[parent_parser_onevm, parent_parser_template])
parser_respawn = subparsers.add_parser('respawn', help='removes and spawns a new copy of a VM', parents=[parent_parser_onevm, parent_parser_template])
parser_enforce = subparsers.add_parser('enforce', help='enforce the HA policy on one VM', parents=[parent_parser_onevm])
parser_enforce_all = subparsers.add_parser('enforce-all', help='check the HA policy on all VMs and enforce the policy (config must be set)', parents=[parent_parser_multivm])

# Set the functions to be called by each sub-parser
parser_start.set_defaults(func=action_list)
parser_start.set_defaults(func=action_pools)
parser_start.set_defaults(func=action_start)
parser_stop.set_defaults(func=action_stop)
parser_status.set_defaults(func=action_status)
parser_restart.set_defaults(func=action_restart)
parser_remove.set_defaults(func=action_remove)
parser_spawn.set_defaults(func=action_spawn)
parser_respawn.set_defaults(func=action_respawn)
parser_enforce.set_defaults(func=action_enforce)
parser_enforce_all.set_defaults(func=action_enforce_all)

args = parser.parse_args()

# Set verbose mode. args.verbose is set by action='store_true' option in parser.
if args.verbose:
	verbose=True
	print "Verbose on"
else:
	verbose=False

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

# Get config options
hosts = config.get('Connection', 'hosts').split(',')
username = config.get('Connection', 'username')
password = config.get('Connection', 'password')
template = config.get('Input', 'template')
vmlist = config.get('Input', 'vmlist')
implants_file = config.get('Input', 'implants_file')

# Override config if set on command line
if args.hosts != None: # args.hosts is a list and and hasattr requires a string for some reason! So the default must be set above
	hosts = args.hosts.split(',')
if hasattr(args,password):
	password = args.password
if hasattr(args, template):
 	template = args.template
if hasattr(args, vmlist):
	vllist = args.vmlist

if verbose: print 'Hosts: ' + str(hosts)

# Get defaults (not sure if we'll use these):
default_ha_restart_priority = config.get('HA Defaults', 'restart_priority')
default_order = config.get('HA Defaults', 'order')
default_start_delay = config.get('HA Defaults', 'start_delay')

# Check the files specified are present
if not os.path.isfile(vmlist):
	message = 'File "' + str(vmlist) + '" does not exist'
	error(message)

# Debug line to dump out command line args
# print vars(args)

# Call the function selected by set_default(func=)
result = args.func()

# Analyse what is returned
if result == 1:
	error("function returned error code")

exit()





