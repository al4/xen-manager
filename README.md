xen-manager
===========
This is a tool I wrote for my employer to manage our Xen clusters. 

I am a sysadmin, not a Python developer, so coding standards are non-existant and I basically wrote this in an ad-hoc
fashion with the Python docs open on a second screen. It also contains many conventions specific to our environment and
would require significant adaptation to work elsewhere.

In the future I hope to improve upon the code and make it more generally useful.

---

usage: xenm [-h] [--configfile CONFIGFILE] [--username USERNAME]
            [--password PASSWORD] [--hosts HOSTS] [--vmlist VMLIST]
            [--verbose]
            
            {list,list-pools,pools,start,stop,status,restart,remove,spawn,respawn,enforce,enforce-all,debug}
            ...

Manages our Xen cluster. First positional argument is action, use {action} -h
for more help.

positional arguments:
  {list,list-pools,pools,start,stop,status,restart,remove,spawn,respawn,enforce,enforce-all,debug}
    list                list all VMs
    list-pools          list all pools
    pools               alias for list-pools
    start               starts a VM
    stop                performs a shutdown, clean unless force is set
    status              shows the status of a VM
    restart             performs a reboot, clean unless force is set
    remove              removes a VM
    spawn               spawns a new VM
    respawn             removes and spawns a new copy of a VM
    enforce             enforce the HA policy on one VM
    enforce-all         check the HA policy on all VMs and enforce the policy
                        (config must be set)
    debug               debug method, used for testing

optional arguments:
  -h, --help            show this help message and exit
  --configfile CONFIGFILE, -c CONFIGFILE
                        config file to use (/etc/opta/xenm/xenm.cfg by
                        default)
  --username USERNAME, -u USERNAME
                        user name for Xen Server (default set in config
  --password PASSWORD, -p PASSWORD
                        root password for Xen Server (default set in config)
  --hosts HOSTS         Xen host(s) to connect to. These hosts must be the
                        master of their cluster. Separate multiple hosts with
                        commas.
  --vmlist VMLIST       CSV file with a list of VMs and priorities
  --verbose, -v         print more output
