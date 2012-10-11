#!/usr/bin/python

# Config file definition, writes out the file

import ConfigParser # this is configparser in python3

config = ConfigParser.RawConfigParser()

config.add_section('Connection')
config.set('Connection', 'host', 'xen-a01')
config.set('Connection', 'username', 'root')
config.set('Connection', 'password', '')

config.add_section('Input')
config.set('Input', 'implants_file', 'implants.conf')
config.set('Input', '')

config.add_section('HA Defaults')
config.set('HA Defaults', 'restart_priority', "")
config.set('HA Defaults', 'start_order', "1000")
config.set('HA Defaults', 'start_delay', "0")

with open('xen_manage.cfg', 'wb') as configfile:
	config.write(configfile)