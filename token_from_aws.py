import argparse
import logging
import sys

import yaml
import os
import schwab
from authlib.integrations.base_client import OAuthError
from schwab.auth import client_from_access_functions, client_from_token_file

import amazon
from datastructures import Config


def main(appconfig, **kwargs):
    conf = Config()
    conf.read_config(appconfig['schwab']['configfile'])
    amazon.write_token_from_dynamodb(config=appconfig)


if __name__ == '__main__':
    print("Let's get the AWS refresh token")
    ap = argparse.ArgumentParser()
    ap.add_argument("--appconfig", dest="appconfig", default="dashboard_config.yaml")
    args = vars(ap.parse_args())
    with open(args['appconfig'], 'r') as acfg_fh:
        app_config = yaml.safe_load(acfg_fh)
    main(
        appconfig=app_config
    )
    sys.exit(0)

def get_token_from_dynamodb(config):
    import boto3
    dynamodb = boto3.resource('dynamodb')
    table_name = config['aws']['dynamodb']['table']
    primary_key = config['aws']['dynamodb']['primary key']
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key={primary_key: config['aws']['dynamodb']['primary key value']})
        if 'Item' in response:
            return response['Item']
        else:
            logging.error(f"Item with key {primary_key} not found in DynamoDB table {table_name}.")
            return None
    except Exception as e:
        logging.error(f"Error fetching token from DynamoDB: {e}")
        return None


def write_token_to_file(token_data, token_file):
    try:
        if 'authtoken' in token_data:
            del token_data['authtoken']
        with open(token_file, 'w') as file:
            yaml.dump(token_data, file)
    except Exception as e:
        logging.error(f"Error writing token to file: {e}")


def get_client_from_file(token_file: str, sconfig: Config):
    try:
        return client_from_token_file(
            token_path=token_file,
            api_key=sconfig.apikey,
            app_secret=sconfig.apisecretkey
        )
    except Exception as e:
        logging.error(f"Error creating client from token file: {e}")
        return None


def get_accounts(client: schwab.client.Client):
    try:
        accounts = client.get_account_numbers()
        return accounts
    except OAuthError as oae:
        logging.error(f"Error getting accounts: {oae}")
        return None


def get_schwab_client(config):
    token_file = config['schwab']['tokenfile']

    sconfig = Config()
    sconfig.read_config(config['schwab']['configfile'])

    # Check if token file exists
    if os.path.exists(token_file):
        client = get_client_from_file(token_file, sconfig)
    else:
        client = None

    if client:
        accounts = get_accounts(client)
        if accounts:
            return client

    if config.get('aws', {}).get('useaws', False):
        token_data = get_token_from_dynamodb(config)
        if token_data:
            write_token_to_file(token_data, token_file)
            client = get_client_from_file(token_file)
            if client:
                accounts = get_accounts(client)
                if accounts:
                    return client
                else:
                    logging.error("Failed to retrieve accounts after updating token.")
            else:
                logging.error("Client creation from updated token file failed.")
        else:
            logging.error("Failed to retrieve token from DynamoDB.")
    else:
        logging.error("Config 'aws.useaws' is not set to true, cannot refresh token from DynamoDB.")
    return None
