#!/usr/bin/env python3

import json
import os
import shutil

import yaml


class Config(object):
    def __init__(self):
        self.apikey = None
        self.apisecretkey = None
        self.callbackuri = None
        self.tokenpath = None
        self.defaultAccount = None

    def read_config(self, config_file):
        #print("Reading config")
        fh = open(config_file, 'r')
        c = json.load(fh)
        fh.close()
        for k in c:
            setattr(self, k, c[k])
        if self.defaultAccount is int:
            self.defaultAccount = str(self.defaultAccount)

    def write_config(self, cfile):
        fh = open(cfile, 'w')
        fh.write(json.dumps(self.__dict__))
        fh.close()

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)


def read_yaml_file(file_path):
    if not os.path.exists(file_path):
        shutil.copy2("dashboard_config.default.yaml", "dashboard_config.yaml")
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None
