#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jsonrpclib
import sys

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://10.0.1.13:1775')

messages = {
    "NONSMOKING": "das verzehren von rauch erzeugenden kohlenstoffen auf dem oberdeck ist nun bitte einzustellen.",
    "SMOKING": "die rauch erzeugung auf dem oberdeck ist nun wieder gestattet. feuer frei.",
}

if messages.has_key(sys.argv[1]):
    server.announce(messages[sys.argv[1]])
else:
    server.announce(" ".join(sys.argv[1:]))
