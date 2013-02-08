# -*- coding: utf-8 -*-

import XenAPI

class host:
    # Host class should have existed from the start and is what should logically own a connection.
    # Most of the code presently assumes the connection is in virtual_machine however

    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password
        return None

    def connect(self):
        # Connect and auth
        xenurl = "https://" + str(self.name)
        # if self.verbose: print "Connecting to " + str(host) + "..."
        # try:
        session = XenAPI.Session(xenurl)
        session.xenapi.login_with_password(self.username, self.password)

        # except:
        # message = 'Failed to connect to "' + host + '"'
        # print message
        # exit()

        self.session = session
        return session

    def disconnect(self):
        self.session.xenapi.logout()
        return 0

    def get_pool(self):
        # Expect only one pool on a host, i.e. a 1:1 relationship. Thus it should be OK to keep them in the same class
        # However judging by the fact that the API returns list, it appears to be possible to have more than one pool per host.
        pools = self.session.xenapi.pool.get_all()
        pool = self.session.xenapi.pool.get_record(pools[0])
        pool_name = pool["name_label"]
        self.pool = pool_name
        return pool_name

    def get_vms(self):
        vms = self.session.xenapi.VM.get_all()
        return vms

    def get_vm(self, vm_name):
        # Returns a list but we keep names unique...
        vms = self.session.xenapi.VM.get_by_name_label(vm_name)

        # Don't like notifying here but it's easier this way...
        if len(vms) > 1:
            print("Found more than one VM with name/label " + vm_name + ", using the first")
        if len(vms) == 0:
            return None
        return vms[0]

class xen_vm:
    # This class replaces the original "virtual_machine" class that I originally wrote
    # It takes the ID as input and doesn't "guess" the ID from the name
    # When calling this class we should already be connected to a host, and know the ID of the VM we're dealing with

    def __init__(self, hostObj, id):
        self.id = id                    # The id of the virtual machine
        self.host = hostObj             # The host object that this machine is running on
        self.session = hostObj.session  # Shortcut to the hosts session (i.e. how we are connected to Xen)

    def get_name(self):
        self.name = self.session.xenapi.get_name_label(self.id)
        return self.name

    def get_record(self):
        self.record = self.session.xenapi.VM.get_record(self.id)
        return self.record
    def read_from_xen(self):
        # Reads all required values from Xen and sets them in the class
        try:
            data = self.session.xenapi.VM.get_record(self.id)
            #pp.pprint(data)
        except:
            print 'Failed to read VM attributes for ' + str(self.id)
            return 1

        # Parse the values we need and set them in the class.
        # Remember to add get_ (and possibly set_) methods for each field we track
        self.name = str(data['name_label'])
        self.power_state = str(data['power_state'])
        self.ha_restart_priority = str(data['ha_restart_priority'])
        self.start_delay = str(data['start_delay'])
        self.order = str(data['order'])
        self.is_a_template = data['is_a_template']
        self.is_control_domain = data['is_control_domain']
        self.tags = data['tags']

        return 0

    def set_order(self, order):
        self.order = order
        #if self.verbose: print "Setting order for " + self.name + " to " + str(order)
        return self.session.xenapi.VM.set_order(self.id, str(order))

    def get_order(self):
        self.order = self.session.xenapi.VM.get_order(self.id)
        return self.order

    def set_ha_restart_priority(self, priority):
        # Sets the priority. Can be "best-effort", "restart", or ""
        self.ha_restart_priority = str(priority)
        #if self.verbose: print "Setting ha_restart_priority to " + str(priority)
        self.session.xenapi.VM.set_ha_restart_priority(self.id, self.ha_restart_priority)
        return 0

    def get_ha_restart_priority(self):
        self.ha_restart_priority = self.session.xenapi.VM.get_ha_restart_priority(self.id)
        return self.ha_restart_priority

    def set_start_delay(self, start_delay):
        # set the delay attribute

        self.start_delay = start_delay
        #if self.verbose: print "Setting start_delay for " + self.name + " to " + str(start_delay)
        self.session.xenapi.VM.set_start_delay(self.id, str(start_delay))   # <- documentation says int but you get FIELD_TYPE_ERROR if you pass an integer here, happy when converted to str
        return self.start_delay

    def get_start_delay(self):
        self.start_delay = self.session.xenapi.VM.get_start_delay(self.id)
        return self.start_delay

    def get_implant(self):
        # get the implant from DNS TXT record
        pass
        return 0

    def get_tags(self):
        # Get the tags of the VM (presently used to track replicant status)
        self.tags = self.session.xenapi.VM.get_tags(self.id)
        return self.tags

    def add_tag(self, tag):
        # Annoyingly we cant just add a tag, we have to get the tags, add to the set, and set them
        tags = self.get_tags()
        new_tags = tags + [ tag ]

        return self.session.xenapi.VM.set_tags(self.id, new_tags)

    def get_all(self):
        return self.session.VM.get_all(self.id)

    # Actions we can perform
    # Named to be consistent with the functions in the Xen API

    def start(self):
        if self.power_state == "Running":
            return 1
        else:
            # Need more robust checking, wouldn't know if Xen returned an error
            self.session.xenapi.VM.start(self.id, False, False)
            return 0

    def clean_reboot(self):
        # Extra check to ensure the VM is not running
        if self.power_state == "Halted":
            return 2
        elif self.power_state != "Running":
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

    def hard_shutdown(self):
        if self.power_state != "Running":
            return 1
        else:
            # Need more robust checking, wouldn't know if Xen returned an error
            self.session.xenapi.VM.hard_shutdown(self.id)
            return 0

    def hard_reboot(self):
        if self.power_state != "Running":
            return 1
        else:
            # Need more robust checking, wouldn't know if Xen returned an error
            self.session.xenapi.VM.hard_reboot(self.id)
            return 0

    def clone(self, template, new_name):
        # template is a vm id/reference (usually self.id), as we should be calling clone from the template vm object
        # should return the id of the clone

        result = self.session.xenapi.VM.clone(template, new_name)
        return result

    def get_template_status(self):
        return self.session.xenapi.VM.get_is_a_template(self.id)

    def set_template_status(self, status):
        # Requires a boolean status to be passed
        self.template = self.session.xenapi.VM.set_is_a_template(self.id, status)
        return self.template

    def destroy(self):
        # Destroys the VM
        result = self.session.xenapi.VM.destroy(self.id)
        if result == "":
            return 0
        else:
            print("result")
            return 1

    def read_vbds(self):
        self.vbds = self.session.xenapi.VM.get_VBDs(self.id)
        return self.vbds

class block_device:
    # Class for a virtual block device.
    # Block devices are attached to VMs, could be a CDROM, hard disk, etc
    # We need to know about the VBD before we can do anything to associated VDIs

    def __init__(self, id, session):
        self.id = id            # ID of the block device
        self.session = session  # The session we are connected through (owned by the host)

        # Get the data about the VBD from Xen
        record = self.session.xenapi.VBD.get_record(self.id)

        # Attributes we want
        # VDI will be NULL if it does not have an associated disk image
        self.vdi_id = record['VDI']
        self.device = record['device']
        self.vm_id = record['VM']

        return None

class disk_image:
    # Class for a virtual disk image
    # Typically owned by a VBD (block_device).

    def __init__(self, id, session):
        self.id = id
        self.session = session

        # get data
        record = self.session.xenapi.VDI.get_record(self.id)
        # print record

        self.VBDs = record['VBDs']


        return None

    def destroy(self):
        return self.session.xenapi.VDI.destroy(self.id)








