import json

import schwab
import streamlit as st

from datastructures import Config
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
            client = schwab.auth.easy_client(
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
            st.stop()
    else:
        raise Exception("Unable to create client")
    if client is None:
        st.json(c.__dict__)
        raise Exception("Client is still none")
    return client
