#!/usr/bin/python

# Config file definition, writes out the file

import ConfigParser # this is configparser in python3

config = ConfigParser.RawConfigParser()

config.add_section('Connection')
config.set('Connection', 'host', 'xen-a01')
config.set('Connection', 'username', 'root')
config.set('Connection', 'password', 'password')

with open('xen_manage.cfg', 'wb') as configfile:
	config.write(configfile)