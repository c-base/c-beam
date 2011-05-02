#!/usr/bin/env python

import jsonrpclib

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://localhost:8080')

#print server.rgb(255, 0, 0)
print server.red()
print server.enable()
