#!/usr/bin/env python3

import json

class Config(object):
    def __init__(self):
        self.apikey = None
        self.apisecretkey = None
        self.callbackuri = None
        self.tokenpath = None
        self.defaultAccount = None

    def read_config(self, config_file):
        print("Reading config")
        fh = open(config_file, 'r')
        c = json.load(fh)
        fh.close()
        for k in c:
            setattr(self, k, c[k])

    def write_config(self, cfile):
        fh = open(cfile, 'w')
        fh.write(json.dumps(self.__dict__))
        fh.close()

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)
