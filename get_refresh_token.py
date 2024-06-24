#!/usr/bin/env python3
import sys
import argparse
import schwab
import yaml

import stutils
from datastructures import Config

def setup(conf: Config, tokenpath, cfile):
    print("Let's setup the configuration!")
    print("What was your APPKEY?: ")
    conf.apikey = input()
    print("What is your app secret?")
    conf.apisecretkey = input()
    print("What is you callback URL?")
    conf.callbackuri = input()
    print("Do you want a default account number? [Leave blank for None, you can add later]")
    def_account = input()
    if def_account is not None and def_account != "":
        conf.defaultAccount = int(def_account)
    conf.tokenpath = tokenpath
    conf.write_config(cfile)


def setup_client(conf: Config):
    client = schwab.auth.client_from_manual_flow(conf.apikey, conf.apisecretkey, conf.callbackuri, conf.tokenpath)
    return client


if __name__ == '__main__':
    print("Let's get a refresh token")
    ap = argparse.ArgumentParser()
    ap.add_argument("--appconfig", dest="appconfig", default="dashboard_config.yaml")
    ap.add_argument("--nosetup", dest="nosetup", default=False, action="store_true")
    ap.add_argument("--noauth", dest="noauth", default=False, action="store_true")
    args = vars(ap.parse_args())
    with open(args['appconfig'], 'r') as acfg_fh:
        app_config = yaml.safe_load(acfg_fh)
    print(app_config)
    c = Config()
    if args['nosetup'] is False:
        print(c)
        setup(c, app_config['schwab']['tokenfile'], app_config['schwab']['configfile'])
    elif app_config is not None:
        c.read_config(app_config['schwab']['configfile'])
    else:
        raise FileNotFoundError("Config file provided is None and \"--nosetup\" was specified")
    if args['noauth'] is False:
        client = setup_client(c)
    else:
        client = stutils.get_schwab_client(c)
    res = client.get_account_numbers()
    print(res.json())
    sys.exit(0)
