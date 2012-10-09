import sys, time, argparse

import XenAPI, provision

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

parser = argparse.ArgumentParser(description='Set HA properties of a VM')
parser.add_argument("--name", help="Name of the VM to manage")
parser.add_argument("--restart-priority", "-p", type=int, help="Order in which the VM is restarted (1=first, 100=last)")
parser.add_argument("--restart-delay", "-d", type=int, help="Restart delay")

args = parser.parseargs

