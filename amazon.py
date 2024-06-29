import json
import logging
from datetime import datetime

import boto3
from boto3.dynamodb.types import Decimal

def write_token_to_dynamodb(config: dict):
    dynamodb = boto3.resource('dynamodb')
    table_name = config['aws']['dynamodb']['table']
    primary_key = config['aws']['dynamodb']['primary_key']
    table = dynamodb.Table(table_name)

    try:
        token_file = config.get("schwab").get("tokenfile")
        with open(token_file, 'r') as fh:
            token_data = json.load(fh)
        payload = {
            primary_key: 'authtoken',
            'token': token_data,
            'timestamp': Decimal(datetime.now().timestamp())
        }
        table.put_item(Item=payload)
        print("Token written to DynamoDB successfully.")
    except Exception as e:
        logging.error(f"Error writing token to DynamoDB: {e}")

def __dynamo_decimal_to_int(d):
    for k in d:
        if isinstance(d[k], Decimal):
            d[k] = int(d[k])
        elif isinstance(d[k], dict):
            __dynamo_decimal_to_int(d[k])


def write_token_from_dynamodb(config: dict):
    dynamodb = boto3.resource('dynamodb')
    table_name = config['aws']['dynamodb']['table']
    primary_key = config['aws']['dynamodb']['primary_key']
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key={primary_key: 'authtoken'})['Item']
        # Check if 'Item' is present in the response
        if 'token' in response:
            token_file = config.get("schwab").get("tokenfile")
            token_data = response['token']
            __dynamo_decimal_to_int(token_data)
            #ts: boto3.dynamodb.types.Decimal = token_data['creation_timestamp']
            #token_data['creation_timestamp'] = float(ts)
            with open(token_file, 'w') as fh:
                json.dump(token_data, fh)
            return token_file
        else:
            return None

    except Exception as e:
        logging.error(f"Error writing token from DynamoDB: {e}")