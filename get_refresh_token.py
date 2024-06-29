#!/usr/bin/env python3
import json
import logging
import os
import sys
import argparse
import schwab
import yaml

import amazon
import stutils
from datastructures import Config

def read_json_file(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return None
    else:
        print("File does not exist.")
        return None

def setup_schwab_config(conf: Config, tokenpath, cfile):
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

def __write_to_amazon(appconfig: dict, conf: Config):
    if appconfig.get('app', None).get('aws'):
        try:
            token = conf.tokenpath
            if token:
                amazon.write_token_to_dynamodb(appconfig)
                logging.info("Token saved to AWS")
            else:
                logging.error("Token not found in config.")
        except Exception as e:
            logging.error("failed aws")
def main(
        appconfig={},
        setup=False,
        noauth=False,
        **kwargs
):
    schwab_config_file = appconfig.get('schwab', {}).get('configfile')
    conf: Config
    if noauth is True:
        conf = Config()
        conf.read_config(schwab_config_file)
        __write_to_amazon(appconfig=appconfig, conf=conf)
        return
    if (schwab_config_file and os.path.exists(schwab_config_file) and (setup is False)):
        conf = Config()
        conf.read_config(schwab_config_file)
    elif noauth is False:
        conf = setup_schwab_config()

    client = setup_client(conf=conf)

    if client:
        try:
            account_numbers = client.get_account_numbers().json()
            print("Client setup successful, account numbers retrieved.")
            print(json.dumps(account_numbers, indent=4))
        except Exception as e:
            logging.error(f"Error retrieving account numbers: {e}")
        if appconfig.get('app', None).get('aws'):
            try:
                token = conf.tokenpath
                if token:
                    amazon.write_token_to_dynamodb(appconfig)
                    logging.info("Token saved to AWS")
                else:
                    logging.error("Token not found in config.")
            except Exception as e:
                logging.error("failed aws")
    else:
        logging.error("Client setup failed.")



if __name__ == '__main__':
    print("Let's get a refresh token")
    ap = argparse.ArgumentParser()
    ap.add_argument("--appconfig", dest="appconfig", default="dashboard_config.yaml")
    ap.add_argument("--setup", dest="setup", default=False, action="store_true")
    ap.add_argument("--noauth", dest="noauth", default=False, action="store_true")
    args = vars(ap.parse_args())
    with open(args['appconfig'], 'r') as acfg_fh:
        app_config = yaml.safe_load(acfg_fh)
    main(
        appconfig=app_config,
        setup=args['setup'],
        noauth=args['noauth']
    )
    sys.exit(0)
