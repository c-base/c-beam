#!/usr/bin/env python

import jsonrpclib
import sys

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://localhost:8080')

if len(sys.argv) <= 1:
    print '%s <command> [parameters]' % sys.argv[0]
elif sys.argv[1] in ['off', 'disable']:
    print server.disable()
elif sys.argv[1] in ['on', 'enable']:
    print server.enable()
elif sys.argv[1] in ['red', 'puff']:
    print server.red()
elif sys.argv[1] in ['program', 'prg']:
    program = 0
    try: program = int(sys.argv[2])
    except: pass
    server.setprogram(program)
