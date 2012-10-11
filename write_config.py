#!/usr/bin/python

# Config file definition, writes out the file

import ConfigParser # this is configparser in python3

config = ConfigParser.RawConfigParser()

config.add_section('Connection')
config.set('Connection', 'host', 'xen-a01')
config.set('Connection', 'username', 'root')
config.set('Connection', 'password', '')

config.add_section('Input')
# implants_file is the list of the implants with a priorities which we will calculate from
config.set('Input', 'implants_file', 'implants.conf')
# priorities_file is a file with VM names and priorities (this option is temporary until we can calculate from the implants_file)
config.set('Input', 'priorities_file', 'priorities.conf')

config.add_section('HA Defaults')
config.set('HA Defaults', 'restart_priority', "best-effort")	# Can be "best-effort", "restart", or ""
config.set('HA Defaults', 'order', "1000")						# Numerical
config.set('HA Defaults', 'start_delay', "0")					# Numerical

config.add_section('Logging')
config.set('Logging', 'level', "debug")

with open('xenm.cfg', 'wb') as configfile:
	config.write(configfile)