#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, sys, inspect, time, argparse, getpass, ConfigParser, csv
import XenAPI               # Gee I wonder why we need this
from subprocess import call # for external system calls
import socket               # for socket.getfqdn()

# Our modules
# from class_vm import virtual_machine
from class_vm import block_device
from class_vm import disk_image
from class_vm import host
from class_vm import xen_vm     # This is the same as virtual_machine but takes an ID as input and not a name.
                            # This is the more "correct" way of doing things and functions should be
                            # updated to use this class instead

import pprint # for debugging
pp = pprint.PrettyPrinter(indent=2) # for debugging

# XenAPI doc: http://docs.vmd.citrix.com/XenServer/6.0.0/1.0/en_gb/api/

### Housekeeping functions. TODO - implement proper logging
def error(message):
    # Throw message and exit
    print("ERROR: " + str(message))
    # disconnect()
    exit()

def notify(message):
    # Notify user but don't quit
    print("NOTICE: " + str(message))

### Functions for the sub-commands
def action_list():
    # Polls all Xen servers to gather data

    # Lists which we append to (start with headings in first row)
    header=[['name_label', 'pool', 'power_state', 'restart_priority', 'start_delay', 'order'],
            ['----------', '----', '-----------', '----------------', '-----------', '-----']]
    data_vms=[]

    for host_name in hosts:
        # Initialise the host
        myhost = host(host_name, username, password)
        session = myhost.connect()

        try:
            # Get the name of the pool on this host
            pool_name = myhost.get_pool()

            if verbose:
                print("Getting VMs from " + host + "...")

            vms = myhost.get_vms()

            # Build a list of VMs that are not templates or control domains
            for vm_id in vms:
                myvm = xen_vm(myhost, vm_id)
                record = myvm.get_record()

                if not(record["is_a_template"]) and not(record["is_control_domain"]):
                    data_vms.append([
                        record["name_label"],
                        pool_name,record["power_state"],
                        record["ha_restart_priority"],
                        record["start_delay"],
                        record["order"]
                        ])
        finally:
            myhost.disconnect()

    if verbose: print("")
    col_width = max(len(word) for row in data_vms for word in row) + 2

    for row in header:
        print("".join(word.ljust(col_width) for word in row))
    for row in data_vms:
        print("".join(word.ljust(col_width) for word in row))

    return data_vms

def action_pools():
    # This function should list all pools

    header=[['name_label', 'host'],['----------','----']]
    data_pools=[]

    for host_name in hosts:
        # Create new host object and connect
        myhost = host(host_name, username, password)
        myhost.connect()

        try:
            pool_name = myhost.get_pool()
            data_pools.append([pool_name,host_name])

        finally:
            myhost.disconnect()

    if verbose: print("") # Add line between verbose messages and output - looks neater

    col_width = max(len(word) for row in data_pools for word in row) + 2

    for row in header:
        print("".join(word.ljust(col_width) for word in row))
    for row in data_pools:
        print("".join(word.ljust(col_width) for word in row))

    return data_pools

def action_start():

    global vmname

    vmname = args.vmname
    host_name = get_host(vmname)

    if host_name == None:
        error(vmname + " does not exist on any defined hosts")

    # Create new host object and connect
    myhost = host(host_name, username, password)
    myhost.connect()

    # Get vm_id
    vm_id = myhost.get_vm(vmname)

    # Create xen_vm object
    myvm = xen_vm(myhost, vm_id)
    myvm.read_from_xen()

    try:
        result = power_on(myvm)
    finally:
        myhost.disconnect()

    return result

def power_on(vm):

    check_result = vm.read_from_xen()

    if check_result == 0:
        print("Starting " + vm.name + "...")
        result = vm.start()
        if result == 0:
            print("Start succeeded")
            return result
        elif result == 1:
            notify("VM already running")
            return result
        else:
            error("Unknown return value from vm.start()")
    else:
        notify("Check failed")
        return check_result

def action_stop():

    global vmname

    vmname = args.vmname
    host_name = get_host(vmname)

    if host_name == None:
        error(vmname + " does not exist on any defined hosts")

    # Create new host object and connect
    myhost = host(host_name, username, password)
    myhost.connect()

    # Get vm_id
    vm_id = myhost.get_vm(vmname)

    # Create xen_vm object
    myvm = xen_vm(myhost, vm_id)

    try:
        myvm.read_from_xen()
        result = shutdown(myvm)
    finally:
        myhost.disconnect()

    return result

def shutdown(vm):

    check_result = vm.read_from_xen()

    if check_result == 0:
        print("Stopping " + vm.name + "...")
        result = vm.clean_shutdown()
        if result == 0:
            print("Stop succeeded")
            return result
        elif result == 1:
            notify("VM already halted")
            return result
        else:
            error("Unknown return value from vm.clean_shutdown()")
    else:
        notify("Check failed")
        return check_result

def action_restart():

    global vmname

    vmname = args.vmname
    host_name = get_host(vmname)

    if host_name == None:
        error(vmname + " does not exist on any defined hosts")

    # Create new host object and connect
    myhost = host(host_name, username, password)
    myhost.connect()

    # Get vm_id
    vm_id = myhost.get_vm(vmname)

    # Create xen_vm object
    myvm = xen_vm(myhost, vm_id)
    myvm.read_from_xen()

    try:
        if myvm.power_state == "Running":
            result = clean_reboot(myvm)
        elif myvm.power_state == "Halted":
            notify(myvm.name + " was halted")
            result = power_on(myvm)
    finally:
        myhost.disconnect()

    return result

def clean_reboot(vm):

    check_result = vm.read_from_xen()

    if check_result == 0:
        print("Restarting " + vm.name + "...")
        result = vm.clean_reboot()
        if result == 0:
            print("Reboot succeeded")
        elif result == 1:
            notify("reboot failed")
        else:
            error("Unknown return value from vm.clean_reboot()")
        return result
    else:
        notify("Check failed")
        return check_result

def action_remove():

    global vmname

    vmname = args.vmname
    host_name = get_host(vmname)

    if host_name == None:
        error(vmname + " does not exist on any defined hosts")

    # Create new host object and connect
    myhost = host(host_name, username, password)
    myhost.connect()

    # Get vm_id
    vm_id = myhost.get_vm(vmname)

    # Create xen_vm object
    myvm = xen_vm(myhost, vm_id)
    myvm.read_from_xen()

    try:
        shutdown(myvm)
        remove_disks(myvm)
        destroy(myvm)
        puppet_clean(myvm)
    finally:
        myhost.disconnect()

def destroy(vm):

    check_result = vm.read_from_xen()

    if check_result == 0:
        print("Removing " + vm.name + " from " + vm.host.name + "...")

        result = vm.destroy()
        if result == 0:
            print("Remove succeeded")
            return 0
        else:
            return result

def remove_disks(vm):
    # Remove all disks from a VM.
    vbd_ids = vm.read_vbds()

    if len(vbd_ids) == 0:
        notify(vm.name + "has no disks to remove")

    # vms can have multiple vbds so we loop over them
    for id in vbd_ids:
        # This next bit is probably quite hard to read.
        # The vbd and vdi classes both need and ID and session passed to them.
        # for the vbd, this is the ID return from the vm class (as it is one of its block devices)
        # for vdi, this is the ID returned from the vbd class (vbd.VDI)
        vbd = block_device(id, vm.session)

        # vbd can only have one vdi (at least I hope so, it is not returning a list), so here
        # we check if it is NULL and if not delete it
        if vbd.vdi_id == 'OpaqueRef:NULL':
            # No vdi to delete
            continue
        elif len(vbd.vdi_id) == 46:
            # Looks like a valid VDI attached to a valid VBD attached to a VM we are removing...
            vdi = disk_image(vbd.vdi_id, vm.session)

            # Check this VDI is not attached to any other VBDs
            if len(vdi.VBDs) > 1:
                notify("Not removing VBD with ID " + vdi.id + " as it is attached to another VM")
            else:
                print("Deleting " + vbd.device + " from " + vm.name + "...")
                vdi.destroy()
        else:
            error = "Unexpected VDI ID"
            return 1
    return 0

def action_spawn():
    # Function to spawn a new VM from template
    # Would be nice if this also set the name_label on associated VDIs.

    global vmname
    global hosts
    global template

    # Get name from args, it is required from the CLI for this function
    vmname = args.vmname

    # for spawn, we can only work with a single host
    host_name = hosts[0]

    # instantiate host
    myhost = host(host_name, username, password)
    myhost.connect()
    myhost.get_pool()

    if len(hosts) > 1:
        #error("Spawn requires that only one host is set, define a single host on the command line with the --host option")
        # We take the first one instead:
        notify("Host was not set explicitly, using " + myhost.pool + " (" + myhost.name + ") to spawn VM")

    try:
        # get id of template
        template_id = myhost.get_vm(template)

        # Check template exists
        if template_id == None:
            error("Template " + template + " does not exist on pool " + myhost.pool)

        # object for the template (to get the ID and make sure it is valid)
        mytemplate = xen_vm(myhost, template_id)
        # get the template attributes from xen into the object
        mytemplate.read_from_xen()

        # Check vmname doesn't already exist
        check = myhost.get_vm(vmname)
        if check != None:
            error(vmname + " already exists")

        newvm = clone_from_template(mytemplate, vmname)
        newvm.read_from_xen()

        set_ha_properties(newvm)
        power_on(newvm)
    finally:
        myhost.disconnect()

def clone_from_template(mytemplate, vm_name):
    ''' Inputs: mytemplate  ==  template xen_vm object (must have a host)
                vm_name     ==  string, name of vm
        Returns: xen_vm object (created from the clone)
    '''

    # Check that we don't already have a valid vm with the same name
    check = mytemplate.host.get_vm(vm_name)
    if check != None:
        error(vm_name + " already exists")

    # Make sure template VM is actually a template
    is_template = mytemplate.get_template_status()
    if is_template == False:
        error("Template VM given is not a template")
    elif is_template == True:
        print("Cloning " + mytemplate.name + " to " + vm_name + "...")
        new_id = mytemplate.clone(mytemplate.id, vm_name)

        # Instantiate a new VM object with the VM we just created by cloning. Pass through host object of the template
        myvm = xen_vm(mytemplate.host,new_id)

        check = myvm.read_from_xen()
        if check != 0:
            error("Clone failed")

        # Cloned VMs are made as templates, we need to set is_a_template to false
        if myvm.is_a_template == True:
            myvm.set_template_status(False)
        elif myvm.is_a_template == False:
            notify("Expected new clone to be a template but this was not the case, investigate?")
        else:
            error("Could not get template status of " + myvm.name)

    else: error("Could not get template status of " + mytemplate.name)

    # return the new vm object
    return myvm

def action_respawn():
    # Function to respawn an existing VM from template

    global vmname
    global hosts
    global template

    # Get name from args, it is required from the CLI for this function
    vmname = args.vmname

    # for spawn, we can only work with a single host
    host_name = hosts[0]

    # instantiate host
    myhost = host(host_name, username, password)
    myhost.connect()
    myhost.get_pool()

    if len(hosts) > 1:
        #error("Spawn requires that only one host is set, define a single host on the command line with the --host option")
        # We take the first one instead:
        notify("Host was not set explicitly, using " + myhost.pool + " (" + myhost.name + ") to spawn VM")

    try:
        # get id of template
        template_id = myhost.get_vm(template)
        vm_id = myhost.get_vm(vmname)

        # Check template exists
        if template_id == None:
            error("Template " + template + " does not exist on pool " + myhost.pool)

        # Check vm exists
        check = myhost.get_vm(vmname)
        if check == None:
            error(vmname + " does not exist")

        # object for the template (to get the ID and make sure it is valid)
        mytemplate = xen_vm(myhost, template_id)
        # get the template attributes from xen into the object
        mytemplate.read_from_xen()

        # object for the existing vm
        myvm = xen_vm(myhost, vm_id)
        myvm.read_from_xen()

        # ready to go, destroy
        result = shutdown(myvm)
        if result != 0: notify("Failed to shut down " + myvm.name)

        result = remove_disks(myvm)
        if result != 0: error("Failed to remove disks from " + myvm.name)

        result = destroy(myvm)
        if result != 0: error("Failed to remove vm " + myvm.name)

        result = puppet_clean(myvm)

        # clone a new one
        newvm = clone_from_template(mytemplate, vmname)
        newvm.read_from_xen()

        # Set HA and power on
        set_ha_properties(newvm)
        power_on(newvm)

    finally:
        myhost.disconnect()

    # try:
    #   mytemplate.read_id()
    #   mytemplate.read_from_xen

    #   shutdown(vm)
    #   destroy(vm)
    #   puppet_clean(vm)
    #   clone_from_template(mytemplate, vm)
    #   set_ha_properties(vm)
    #   power_on(vm)
    # finally:
    #   vm.disconnect_host
    #   mytemplate.disconnect_host

def action_enforce():
    global vmname
    global host

    # Get name from args, it is required from the CLI for this function
    vmname = args.vmname
    host_name = get_host(vmname)

    if host_name == None:
        error(vmname + " does not exist on any defined hosts")

    # Create new host object and connect
    myhost = host(host_name, username, password)
    myhost.connect()

    try:
        # Get vm_id
        vm_id = myhost.get_vm(vmname)

        # Create xen_vm object
        myvm = xen_vm(myhost, vm_id)
        myvm.read_from_xen()

        # Check
        check_result = myvm.read_from_xen()

        if check_result == 0:
            # Do it
            set_ha_properties(myvm)
        else:
            error("Check failed")
    finally:
        myhost.disconnect()

def set_ha_properties(myvm):

    count = 0

    # Read csv file
    with open(vmlist, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')

        # Get current values
        current_order = myvm.get_order()
        current_start_delay = myvm.start_delay
        current_priority = myvm.ha_restart_priority

        # Find out what the HA values should be
        # Check the config file:
        count = 0
        for row in reader:
            # See if this is the row we want
            if row[1] == vmname:
                count += 1

                # Check order and set if it is not what it should be

                order = row[0]

                if int(order) != int(current_order):
                    myvm.set_order(str(order))
                    if verbose: print("Changed order on " + myvm.name + " from " + str(current_order) + " to " + str(order))

            else:
                continue

    # if we didn't find the vm in the config, use defaults:
    if count == 0:
        print("Could not find entry for " + myvm.name + " in " + vmlist + ", using defaults")
        order = default_order
        start_delay = default_start_delay
        priority = default_ha_restart_priority

    # Now set them if they differ
    if int(order) != int(current_order):
        print(myvm.name + " order: " + str(current_order) + " => " + str(order))
        myvm.set_order(str(order))
    if int(current_start_delay) != int(start_delay):
        print(myvm.name + " start_delay: " + str(current_start_delay) + " => " + str(start_delay))
        myvm.set_start_delay(str(start_delay))
    if str(current_priority) != str(priority):
        print(myvm.name + " priority: " + str(current_priority) + " => " + str(priority))
        myvm.set_ha_restart_priority(str(priority))

def action_enforce_all():
    # Loop over each VM on each host, look for appropriate entry in the CSV file, and fix if different

    # Load CSV data into list
    with open (vmlist, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')

        ha_config = {}
        # Loop over each entry
        for row in reader:
            #pp.pprint(row)
            vmname = row[1]
            order = int(row[0])         # We set as string but this should be an int for comparisons (and eliminates leading 0's)
            priority = 'restart'        # Hard-coded for now as we're not defining or computing anywhere
                                        ## Overridden by hack later
            start_delay = 0             # Also hard-coded for now until we compute it somewhere

            # Put the values in a dictionary. The key is prefixed by vmname
            ha_config[vmname + '_order'] = order
            ha_config[vmname + '_priority'] = priority
            ha_config[vmname + '_start_delay'] = start_delay

    count = 0   # count for changes made

    # ha_config is loaded, now to compare and set it
    for host_name in hosts:
        # Initialise the host
        myhost = host(host_name, username, password)
        session = myhost.connect()

        try:
            # Get the name of the pool on this host
            pool_name = myhost.get_pool()
            if verbose: print("Checking VMs on " + pool_name + "...")
            vm_list = myhost.get_vms()

            # Loop over VMs
            for vm_id in vm_list:
                myvm = xen_vm(myhost, vm_id)
                myvm.read_from_xen()    # Loads the values we need into the class

                # Don't want to modify templates or control domains!
                if myvm.is_control_domain == False and myvm.is_a_template == False:
                    # Check the values
                    current_order = myvm.order
                    current_start_delay = myvm.start_delay
                    current_priority = myvm.ha_restart_priority

                    if myvm.name + "_order" in ha_config:
                        # this VM has config defined, set it
                        order = ha_config[myvm.name + '_order']
                        start_delay = ha_config[myvm.name + '_start_delay']
                        priority = ha_config[myvm.name + '_priority']

                        # Hack to set start_delay to "restart if possible" if order > 1000
                        # because we aren't defining this in config yet
                        if int(order) > 1000:
                            priority = 'best-effort'
                        else:
                            priority = 'restart'
                    else:
                        # print(myvm.name + " is not in config")
                        # enforce defaults
                        order = default_order
                        start_delay = default_start_delay
                        priority = default_ha_restart_priority

                    # Now set them
                    if int(order) != int(current_order):
                        count += 1
                        print(myvm.name + " order: " + str(current_order) + " => " + str(order))
                        myvm.set_order(str(order))
                    if int(current_start_delay) != int(start_delay):
                        count += 1
                        print(myvm.name + " start_delay: " + str(current_start_delay) + " => " + str(start_delay))
                        myvm.set_start_delay(str(start_delay))
                    if str(current_priority) != str(priority):
                        count += 1
                        print(myvm.name + " priority: " + str(current_priority) + " => " + str(priority))
                        myvm.set_ha_restart_priority(str(priority))
                else:
                    continue
        finally:
            myhost.disconnect()
    print("Changed " + str(count))

def action_status():
    global vmname

    vmname = args.vmname
    host_name = get_host(vmname)

    if host_name == None:
        error(vmname + " does not exist on any defined hosts")

    header=[['name_label', 'pool', 'power_state', 'restart_priority', 'start_delay', 'order'],
            ['----------', '----', '-----------', '----------------', '-----------', '-----']]
    data_vms=[]

    # Create new host object and connect
    myhost = host(host_name, username, password)
    myhost.connect()

    try:
        # Get vm_id
        vm_id = myhost.get_vm(vmname)

        # Create xen_vm object
        myvm = xen_vm(myhost, vm_id)
        myvm.read_from_xen()

        pool_name = myvm.host.get_pool()
        record = myvm.get_record()

        data_vms.append([
            record["name_label"],
            pool_name,
            record["power_state"],
            record["ha_restart_priority"],
            record["start_delay"],
            record["order"]
                ])

        if verbose: print("")

        col_width1 = max(len(word) for row in data_vms for word in row) + 2
        col_width2 = max(len(word) for row in header for word in row) + 2

        col_width = max(col_width1,col_width2)

        for row in header:
            print("".join(word.ljust(col_width) for word in row))
        for row in data_vms:
            print("".join(word.ljust(col_width) for word in row))


    finally:
        myhost.disconnect()

    return 0

## Helper functions

def get_host(vm_name):
    # Find the host a VM is on.
    # Input: vm name
    # Returns: host name

    if not str(vm_name): error("must pass vm_name to get_host")
    host_list = []

    for host_name in hosts:
        # Get a connection
        myhost = host(host_name, username, password)
        myhost.connect()

        if verbose: print("Looking for " + vm_name + " on " + host_name)
        try:
            # Get vm id
            vm_id = myhost.get_vm(vm_name)

            # kinda bad as
            if vm_id == None:
                # vm not found
                pass
            elif len(vm_id) == 46:
                # found it
                host_list.append(host_name)
        finally:
            myhost.disconnect()

    if len(host_list) == 0:
        print("Could not find " + vm_name + " on any hosts")
        return None
    if len(host_list) > 1:
        print("Found " + vm_name + " on multiple hosts")
        return 1
    if len(host_list) == 1:
        if verbose: print("Found " + vm_name + " on " + host_list[0])
        return host_list[0]
    return 0

def puppet_clean(vm):
    # Get fully qualified domain from vm name
    fqdn = socket.getfqdn(vm.name)

    # Check puppet is on this box
    if not os.path.isfile(puppet_path):
        notify(puppet_path + " does not exist on this machine. Please run 'puppet cert clean " + fqdn + "' on nms")
        # We could do an ssh call here....
        return 1

    if verbose: print("Cleaning up " + fqdn + " from puppet...")
    return_code = call([puppet_path,"cert","clean",fqdn], shell=False)

    if str(return_code) == "24":
        # Puppet returns 24 when it can't find the hostname. Usually this is because it is not a fqdn,
        # socket.getfqdn returns exactly what you give it if it can't find a fully-qualified host name.
        notify("Could not find the hostname in puppet, ensure DNS entries are set correctly")
    return return_code

## end of functions

# Parse the commandline arguments using Python's argparse.
parser = argparse.ArgumentParser(description='Manages our Xen cluster', add_help=False)

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
parser_list = subparsers.add_parser('list', help='list all VMs')
parser_listpools = subparsers.add_parser('list-pools', help='list all pools')
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
parser_list.set_defaults(func=action_list)
parser_listpools.set_defaults(func=action_pools)
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
    print("Verbose on")
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
hosts = config.get('Main', 'hosts').split(',')
username = config.get('Main', 'username')
password = config.get('Main', 'password')
puppet_path = config.get('Main', 'puppet_path')
template = config.get('Input', 'template')
vmlist = config.get('Input', 'vmlist')
implants_file = config.get('Input', 'implants_file')

# Override config if set on command line
if args.hosts != None: # args.hosts is a list and and hasattr requires a string for some reason! So the default must be set above
    hosts = args.hosts.split(',')
if hasattr(args, password):
    password = args.password
if hasattr(args, template):
    template = args.template
if hasattr(args, vmlist):
    vllist = args.vmlist

if verbose: print('Hosts: ' + str(hosts))

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

# # Analyse what is returned
# if result == 1:
#   error("function returned error code")

exit()





