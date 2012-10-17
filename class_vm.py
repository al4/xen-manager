# -*- coding: utf-8 -*-

import XenAPI

# Right, let's get down to the main class...
class virtual_machine:
	def __init__(self, name, verbose=False):
		# We only set the name on instantiation
		self.name = name
		self.verbose = verbose
		# Get the ID from the name
		#self.id = self.read_id() 	# Don't do this in the constructor any more because we need to be
									# able to test whether the machine exists before we do something
									# that throws an error

		# Get the rest of the attributes we need
		# self.read_from_xen()

	#### Setting and Getting methods ###
	# "setting" methods simply take input and set the value in the class and Xen
	# "getting" methods return the current value
	# "read" methods get the current settings from Xen or CSV and set them in the class, they do not set them anywhere

	def connect_host(self, host, username, password):
		# Connect and auth
		xenurl = "https://" + str(host)
		# if self.verbose: print "Connecting to " + str(host) + "..."
		# try:
		session = XenAPI.Session(xenurl)
		session.xenapi.login_with_password(username, password)

		# except:
		# message = 'Failed to connect to "' + host + '"'
		# print message
		# exit()

		self.session = session
		return session

	def disconnect_host(self):
		# if self.verbose: print "Disconnecting..."
		self.session.xenapi.logout()
		return 0

	def dump_attrs(self):
		# For debugging, must be a built-in way to do this but I'm not familiar enough with Python yet...
		print "name: " + self.name
		print "id: " + self.id
		print "power_state: " + self.power_state
		print "ha_restart_priority: " + self.ha_restart_priority
		print "start_delay: " + self.start_delay
		print "order: " + self.order
		return 0

	def preflight(self):
		# Check we have a session
		if not hasattr(self, 'session'):
			self.disconnect_host()
			print "No connection to Xen server! \nThis is probably a programming error, call connect_host(host, username, password) before doing a preflight."
			return 1

		# Check this VM exists
		if self.read_id() == 1:
			# couldn't find ID
			return 1

		# read_from_xen will return 0 on success, which we pass straight through
		# Should this return the power_state?
		return self.read_from_xen()


	def set_name(self, name):
		# Simple class to set the name (we don't write this back to Xen, only use it for input)
		self.name = name
		return 0

	def read_id(self):
		# Function to get the machine ID from Xen based on the name. Names should be unique so we
		# throw an error if there is more than 1 match.
		# This is called by preflight() so has to handle its own error cases
		try:
			ids = self.session.xenapi.VM.get_by_name_label(self.name)
		except:
			message = "XenAPI threw exception trying to get ID"
			print message
			self.disconnect_host()

		if len(ids) > 1:
			# This is bad, delete the offending VM! In future we may want to continue anyway and set parameters on both
			# for automated scenarios
			message = "VM name \"" + self.name + "\" has more than one match!"
			if self.verbose: print message
			return 2

		if len(ids) == 0:
			# No result
			return 1

		self.id = ids[0]
		#print "Got ID for " + self.name + ": " + str(ids)
		return ids[0]

	def read_from_xen(self):
		# Reads all required values from Xen and sets them in the class
		try:
			data = self.session.xenapi.VM.get_record(self.id)
			#pp.pprint(data)
		except:
			print 'Failed to read VM attributes for ' + self.name
			return 1

		# Parse the values we need and set them in the class. Might be useful:
		# 	ha_restart_priority, start_delay, power_state, order

		# Remember to add a get_ (and possibly set_) method for each field we track

		self.power_state = str(data['power_state'])
		self.ha_restart_priority = str(data['ha_restart_priority'])
		self.start_delay = str(data['start_delay'])
		self.order = str(data['order'])

		# if self.verbose: print "Found VM \"" + self.name + "\":"
		# if self.verbose: print " - power_state: " + str(data['power_state'])
		# if self.verbose: print " - ha_restart_priority: " + str(data['ha_restart_priority'])
		# if self.verbose: print " - start_delay: " + str(data['start_delay'])
		# if self.verbose: print " - order: " + str(data['order'])

		return 0

	def set_order(self, order):
		self.order = order
		if self.verbose: print "Setting order for " + self.name + " to " + str(order)
		self.session.xenapi.VM.set_order(self.id, str(order))

	def get_order(self):
		return self.order

	def set_ha_restart_priority(self, priority):
		# Sets the priority. Can be "best-effort", "restart", or ""

		self.ha_restart_priority = priority
		if self.verbose: print "Setting ha_restart_priority to " + str(priority)
		self.session.xenapi.VM.set_ha_restart_priority(self.id, "restart")
		return 0

	def get_ha_restart_priotiry(self):
		return self.ha_restart_priority

	def set_start_delay(self, start_delay):
		# set the delay attribute

		self.start_delay = start_delay
		if self.verbose: print "Setting start_delay for " + self.name + " to " + str(start_delay)
		self.session.xenapi.VM.set_start_delay(self.id, str(start_delay))	# <- documentation says int but you get FIELD_TYPE_ERROR if you pass an integer here, happy when converted to str
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

	# Actions we can perform
	# Named to be consistent with the functions in the Xen API

	def list(self):
		return 0

	def start(self):
		if self.power_state == "Running":
			return "Machine is already running"
		else:
			# Need more robust checking, wouldn't know if Xen returned an error
			self.session.xenapi.VM.start(self.id, False, False)
			return 0

	def clean_reboot(self):
		# Extra check to ensure the VM is not running
		if self.power_state != "Running":
			return 1
		else:
			# Need more robust checking, wouldn't know if Xen returned an error
			self.session.xenapi.VM.clean_reboot(self.id)
			return 0

	def clean_shutdown(self):
		if self.power_state != "Running":
			return 1
		else:
			# Need more robust checking, wouldn't know if Xen returned an error
			self.session.xenapi.VM.clean_shutdown(self.id)
			return 0

	def clone(self, template):
		# template is a vm reference
		self.session.xenapi.VM.clone(template, self.name)
		self.session.xenapi.VM.is_a_template = False

	def get_template_status(self):
		return self.session.xenapi.VM.get_is_a_template(self.id)

	def set_template_status(self, status):
		# Requires a boolean status to be passed
		return self.session.xenapi.VM.set_is_a_template(self.id, status)

	def destroy(self):
		# Destroys the VM
		return self.session.xenapi.VM.destroy(self.id)

	def read_vbds(self):
		return self.session.xenapi.VM.get_VBDs(self.id)

class block_device:
	# Class for a virtual block device.
	# Block devices are attached to VMs, could be a CDROM, hard disk, etc
	# We need to know about the VBD before we can do anything to associated VDIs

	# This class differs a bit from the approach taken with virtual_machine, in that the input is
	# an ID rather than the name.

	# Putting the connection stuff in the virtul_machine class was a bit of a mistake, should really be separate.
	# Doesn't really affect this code as it needs a session passed anyway, but it does in the application as you
	# need to pass the virtual_machine's session object through.

	def __init__(self, id, session):
		self.id = id
		self.session = session
		# would probably call this read_record but went with read_from_xen to be consistent with the vm class
		record = self.session.xenapi.VBD.get_record(self.id)

		# Attributes we want
		# VDI will be NULL if it does not have an associated disk image
		self.vdi_id = record['VDI']
		self.device = record['device']
		self.vm_id = record['VM']

		return None

class disk_image:
	# Class for a virtual disk image
	# Typically owned by a VBD.

	def __init__(self, id, session):
		self.id = id
		self.session = session

		# get data
		record = self.session.xenapi.VDI.get_record(self.id)
		print record

		self.VBDs = record['VBDs']


		return None

	def destroy(self):
		return self.session.xenapi.VDI.destroy(self.id)





