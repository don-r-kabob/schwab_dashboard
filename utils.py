import json

import schwab
import streamlit as st

from states import states


def config_from_file(configFile=None):
    from datastructures import Config
    if configFile is None:
        if states.CONFIG_FILE is st.session_state:
            configFile = st.session_state[states.CONFIG_FILE]
        else:
            st.json(st.session_state)
            print(json.loads(st.session_state, indent=4))
            raise Exception("No config file available")
    conf = Config()
    conf.read_config(configFile)
    st.session_state[states.CONFIG] = conf
    return conf