import sys, time

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

