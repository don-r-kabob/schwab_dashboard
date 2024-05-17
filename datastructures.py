#!/usr/bin/env python3

import json

import streamlit as st

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


def get_schwab_client(conf: Config = None):
    import schwab
    import authlib as authlib
    from states import states
    c = conf
    if c is None:
        if states.CONFIG in st.session_state:
            c = st.session_state[states.CONFIG]
        else:
            raise Exception("Unable to create client")
    if c is not None:
        #sys.stderr.write(json.dumps(c.__dict__, indent=4))
        try:
            return schwab.auth.easy_client(
                c.apikey,
                c.apisecretkey,
                c.callbackuri,
                c.tokenpath
            )
        except authlib.integrations.base_client.errors.OAuthError as oae:
            st.write("Please recreate authorization token")
            st.stop()
        except TypeError as te:
            st.json(c.__dict__)
    else:
        raise Exception("Unable to create client")
