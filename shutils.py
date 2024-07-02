import json
import logging
import os

import schwab.auth

import amazon
from datastructures import Config

def __setup_client(config: Config):
    token_file = config.tokenpath

    if os.path.exists(token_file):
        client = schwab.auth.client_from_token_file(token_file, config.apikey, config.apisecretkey)
    else:
        logging.error("Token file does not exist.")
        client = None

    return client

def get_schwab_client(schwab_config: Config=None, appconfig: dict=None) -> schwab.client.Client:
    client = __setup_client(config=schwab_config)
    if client:
        try:
            account_numbers = client.get_account_numbers().json()
            print("Client setup successful, account numbers retrieved.")
            print(json.dumps(account_numbers, indent=4))
            return client
        except Exception as e:
            logging.error(f"Error retrieving account numbers: {e}")
    if appconfig['app']['aws']:
        try:
            token_file = schwab_config.tokenpath
            if token_file:
                amazon.write_token_from_dynamodb(appconfig)
                client = __setup_client(config=schwab_config)
                account_numbers = client.get_account_numbers().json()
                #print(json.dumps(account_numbers, indent=4))
                return client
            else:
                logging.error("Token not found in config.")
        except Exception as e:
            logging.error("failed aws")
    else:
        logging.error("Client setup failed.")
    return client