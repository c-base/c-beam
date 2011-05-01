#!/usr/bin/env python

import jsonrpclib

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://10.0.1.13:1775')

#print server.rgb(255, 0, 0)
print server.tts('julia', 'foo')
