#!/usr/bin/env python
# Copyright (c) 2006-2007 XenSource, Inc.
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import atexit
import cmd
import pprint
import readline
import shlex
import string
import sys

import XenAPI

dir(XenAPI)

def logout():
    try:
        server.xenapi.session.logout()
    except:
        pass
atexit.register(logout)

class Shell(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.identchars = string.ascii_letters + string.digits + '_.'
        self.prompt = "xe> "

    def preloop(self):
        cmd.Cmd.preloop(self)
        readline.set_completer_delims(' ')

    def default(self, line):
        words = shlex.split(line)
        if len(words) > 0:
            res = session.xenapi_request(words[0], tuple(words[1:]))
            if res is not None and res != '':
                pprint.pprint(res)
        return False

    def completedefault(self, text, line, begidx, endidx):
        words = shlex.split(line[:begidx])
        clas, func = words[0].split('.')
        if len(words) > 1 or \
           func.startswith('get_by_') or \
           func == 'get_all':
            return []
        uuids = session.xenapi_request('%s.get_all' % clas, ())
        return [u + " " for u in uuids if u.startswith(text)]

    def emptyline(self):
        pass

    def do_EOF(self, line):
        print
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) <> 4:
        print "Usage:"
        print sys.argv[0], " <url> <username> <password>"
        sys.exit(1)
    url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    # First acquire a valid session by logging in:
    session = XenAPI.Session(url)
    session.xenapi.login_with_password(username, password)

    Shell().cmdloop('Welcome to the XenServer shell. (Try "VM.get_all")')
