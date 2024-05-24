import copy
import json
from datetime import datetime, time, date

import schwab
from schwab.client.base import BaseClient
import streamlit as st
import pandas as pd
from datastructures import Config
from stutils import get_schwab_client

from states import states

ACCOUNT_FIELDS = BaseClient.Account.Fields

def flatten_positions(pjson):
    for pdict in pjson:
        try:
            for k in pdict['instrument']:
                pdict[k] = pdict['instrument'][k]
            del(pdict['instrument'])
        except KeyError as ke:
            print(json.dumps(pdict, indent=4))
            pass
    return

def _get_pos_df(client=None, conf=None):
    if client is None:
        if conf is None:
            if states.CONFIG in st.session_state:
                conf = st.session_state[states.CONFIG]
            else:
                return
        client = get_schwab_client(conf=conf)
    try:
        if states.POSITIONS_JSON not in st.session_state:
            pass
        if states.POSITIONS_JSON in st.session_state:
            position_data = copy.deepcopy(st.session_state[states.POSITIONS_JSON])
        else:
            if states.ACCOUNTS_JSON not in st.session_state:
                acc_json = client.get_account(account_hash=st.session_state[states.ACTIVE_HASH],
                                              fields=[ACCOUNT_FIELDS.POSITIONS]).json()
                st.session_state[states.ACCOUNTS_JSON] = acc_json
                position_data = acc_json['securitiesAccount']['positions']

        flatten_positions(position_data)
        pdf = pd.DataFrame(position_data)
        pdf['spotPrice'] = 0.0
        try:
            symbols = pdf.loc[pdf['underlyingSymbol'].notnull(), 'underlyingSymbol'].unique()
        except KeyError as ke:
            symbols = []
    except Exception as e:
        raise e
    try:
        if len(symbols) > 0:
            quotesj = client.get_quotes(symbols).json()
        else:
            quotesj = []
        #st.json(quotesj)
        curr_price = {}
        for ticker in quotesj:
            tdata = quotesj[ticker]
            curr_price[ticker] = tdata['quote']['lastPrice']
            pdf.loc[pdf['underlyingSymbol']==ticker, 'spotPrice'] = float(tdata['quote']['lastPrice'])
    except Exception as e:
        raise e
    pdf = pdf.loc[pdf['assetType']=="OPTION", :]
    pdf['quantity'] = (pdf['longQuantity'] - pdf['shortQuantity'])
    pdf['currentValue'] = (pdf['marketValue']/abs(pdf['quantity']))/100
    pdf['pnl'] = pdf['averagePrice']/pdf['currentValue']
    pdf['otm'] = -1

    pdf['percentChange'] = (pdf['averagePrice']+pdf['currentValue'])/pdf['averagePrice']*100
    pdf['underlyingOptionSymbol'] = pdf['symbol'].str[0:5]
    pdf['underlyingOptionSymbol'].apply(str.rstrip)
    pdf['strikePrice'] = pdf['symbol'].str.slice(start=13).astype(float)/1000
    pdf['eyear'] = pdf['symbol'].str.slice(start=6, stop=8).astype(int)
    pdf['emonth'] = pdf['symbol'].str.slice(start=8, stop=10).astype(int)
    pdf['eday'] = pdf['symbol'].str.slice(start=10, stop=12).astype(int)
    pdf['ctype'] = pdf['symbol'].str.slice(start=12, stop=13).astype(str)
    pdf['edate'] = pd.to_datetime(pdf['symbol'].str.slice(start=6, stop=12), format='%y%m%d')
    pdf['today'] = datetime.today()
    pdf['dte'] = (pdf['edate']-pdf['today']).dt.days
    pdf['otm'] = abs((pdf['strikePrice']/pdf['spotPrice'])-1)
    pdf.loc[(pdf['ctype']=="C") & (pdf['strikePrice'] < pdf['spotPrice']), 'otm'] *= -1
    pdf.loc[(pdf['ctype']=="P") & (pdf['strikePrice'] > pdf['spotPrice']), 'otm'] *= -1
    #st.dataframe(pdf)
    return pdf

def get_pos_df(client=None, conf=None):
    pdf = _get_pos_df(client=client, conf=conf)
    subdf_columns =         [
            'underlyingSymbol',
            "symbol",
            'description',
            'spotPrice',
            'otm',
            'dte',
            'quantity',
            'averagePrice',
            'currentValue',
            'percentChange',
            'strikePrice',
            'ctype'
        ]
    subdf = pdf.loc[(pdf['assetType']=="OPTION") & (pdf['quantity'] < 0), :]
    if len(subdf) == 0:
        subdf = pd.DataFrame(columns=subdf_columns)
    subdf = subdf[subdf_columns].sort_values(['otm'])
    return subdf




def get_positions_json(config: Config):
    client = schwab.auth.easy_client(config.apikey, config.apisecretkey, config.callbackuri, config.tokenpath)
    acc_json = client.get_account(config.accountnum, fields=[ACCOUNT_FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    return positions


def get_todays_orders(
        ahash = None,
        conf: Config = None,
        client = None
):
    #print("Getting today's orders")
    if client is None:
        client = schwab.auth.easy_client(conf.apikey, conf.apisecretkey, conf.callbackuri, conf.tokenpath)
    bod = datetime.today().replace(hour=0, minute=0, second=0)
    eod = datetime.today().replace(hour=23, minute=59, second=59)
    order_res = client.get_orders_for_account(account_hash=ahash, from_entered_datetime=bod, to_entered_datetime=eod)
    return json.loads(order_res.text)

def get_order_count(
        conf: Config,
        order_res=None
):
    if order_res is None:
        order_res = get_todays_orders(conf=conf)
    return len(order_res)

def get_order_option_premium(orders):
    net_premium = 0
    for order in orders:
        try:
            if order['status'] != "FILLED":
                continue
            olc = order['orderLegCollection']
            ol_skip = False
            for ol in olc:
                pass
                if ol['orderLegType'] != "OPTION":
                    ol_skip = True
                    break
            if ol_skip is True:
                continue

            ot = order['orderType']
            if ot == "TRAILING_STOP":
                continue
            price = order['price']
            quant = order['filledQuantity']
            tot = price * quant
            pe = None
            cot = order['complexOrderStrategyType']
            if cot == "NONE":
                for olcd in olc:
                    pe = olcd['positionEffect']
                    instruct = olcd['instruction']
                    if instruct == "SELL_TO_OPEN":
                        pass
                    elif instruct == "BUY_TO_OPEN":
                        tot *= -1
                    elif instruct == "SELL_TO_CLOSE":
                        pass
                    elif instruct == "BUY_TO_CLOSE":
                        tot *= -1
            else:
                ot = order['orderType']
                if ot == "NET_DEBIT":
                    tot *= -1
                elif ot == "NET_CREDIT":
                    pass
                else:
                    raise Exception("invalid order found {}".format(json.dumps(order, indent=4)))
            net_premium += tot
        except Exception as e:
            #print(order)
            print(e)
            raise e
    #print(json.dumps(orders, indent=4))
    return net_premium

def premium_today_df(client: schwab.client.Client, config: Config):
    #print("Getting premium today df")
    TODAY = datetime.today()
    bod = datetime.combine(TODAY, time.min)
    eod = datetime.combine(TODAY, time.max)
    orders = client.get_orders_for_account(
        st.session_state[states.ACTIVE_HASH],
        to_entered_datetime=eod,
        from_entered_datetime=bod
    )
    orders = json.loads(orders.text)
    #print(json.dumps(orders, indent=4))
    t = 0
    l = []
    for order in orders:
        qd = {}
        if order['status'] != "FILLED":
            continue
        t += 1
        if t==1:
            pass
            #print(json.dumps(order, indent=4))
        for olc in order['orderLegCollection']:
            if olc['instrument']['assetType']=="EQUITY":
                continue

            legid = olc['legId']
            qd[legid] = {}
            try:
                qd[legid]['contract'] = olc['instrument']['symbol']
                qd[legid]['underlying'] = olc['instrument']['underlyingSymbol']
            except KeyError as ke:
                print(json.dumps(order, indent=4))
                print(ke)
                print(olc)
                raise
            qd['quantity'] = 0
            quant = 1
            instruct = olc['instruction']
            if instruct == "SELL_TO_OPEN":
                pass
            elif instruct == "BUY_TO_OPEN":
                quant = -1
            elif instruct == "SELL_TO_CLOSE":
                pass
            elif instruct == "BUY_TO_CLOSE":
                quant = -1
            qd[legid]['qmod'] = quant

        oac_count = 0
        for oac in order['orderActivityCollection']:
            if oac['executionType'] != "FILL":
                continue
            for leg in oac['executionLegs']:
                oac_count += 1
                try:
                    d = copy.copy(qd[leg['legId']])
                except KeyError as ke:
                    continue
                d['quantity'] = leg['quantity'] * d['qmod']
                d['price'] = leg['price']
                d['total'] = d['quantity'] * d['price']
                if oac_count == 1 and t == 1:
                    print(json.dumps(d, indent=4))
                l.append(d)
        #continue
    df = pd.DataFrame(l)
    return df