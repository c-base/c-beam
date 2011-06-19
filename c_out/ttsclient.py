#!/usr/bin/env python

import jsonrpclib
import sys

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://10.0.1.13:1775')

#print server.rgb(255, 0, 0)
print " ".join(sys.argv[1:])
print server.tts('julia', " ".join(sys.argv[1:]))
print server.voices()
