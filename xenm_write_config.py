#!/usr/bin/python

# Config file definition, writes out the file

import ConfigParser # this is configparser in python3

config = ConfigParser.RawConfigParser()

config.add_section('Main')
config.set('Main', 'hosts', 'xen-a01,xen-d01,xen-d02,xen-d09')
config.set('Main', 'username', 'root')
config.set('Main', 'password', '')
config.set('Main', 'puppet_path', '/usr/bin/puppet')			# Path to puppet binary (for cleaning certs)

config.add_section('Input')
# implants_file is the list of the implants with a priorities which we will calculate from
config.set('Input', 'implants_file', 'implants.conf')
# priorities_file is a file with VM names and priorities (this option is temporary until we can calculate from the implants_file)
config.set('Input', 'vmlist', 'priorities.conf')
# the template we clone from
config.set('Input', 'template', 'replicant-')

config.add_section('HA Defaults')
config.set('HA Defaults', 'restart_priority', "best-effort")	# Can be "best-effort", "restart", or ""
config.set('HA Defaults', 'order', "1000")						# Numerical
config.set('HA Defaults', 'start_delay', "0")					# Numerical

config.add_section('Logging')
config.set('Logging', 'level', "debug")

with open('xenm.cfg', 'wb') as configfile:
	config.write(configfile)