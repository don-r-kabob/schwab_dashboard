import json

import schwab
import streamlit as st
import yaml

import shutils
from datastructures import Config
from states import states

@st.cache_data
def get_cache_config(config_file):
    c = Config()
    c.read_config(config_file)
    return c

@st.cache_data
def get_cache_appconfig(appconfig_file):
    with open(appconfig_file, 'r') as ac_fh:
        APP_CONFIG = yaml.safe_load(ac_fh)
    return APP_CONFIG

def __get_schwab_cache_client(appconfig: dict=None, schwab_config: Config=None) -> schwab.client.Client:
    return __get_schwab_cache_client(appconfig=appconfig, _schwab_config=schwab_config)

@st.cache_resource(ttl=300)
def get_schwab_cache_client(appconfig: dict=None, _schwab_config: Config=None) -> schwab.client.Client:
    return shutils.get_schwab_client(appconfig=appconfig, schwab_config=_schwab_config)


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
            client = schwab.auth.client_from_token_file(
                conf.tokenpath,
                api_key=conf.apikey,
                app_secret=conf.apisecretkey,
                asyncio=False
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
