import sys
import os

import schwabdata

script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)

from states import states
from datastructures import Config

from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import schwab
import streamlit_dashboard as sd

st.write(st.session_state[states.ACTIVE_ACCOUNT])
st.json(st.session_state, expanded=False)

if states.CONFIG in st.session_state:
    CONFIG = st.session_state[states.CONFIG]

#default_account = CONFIG.defaultAccount
#if states.ACTIVE_ACCOUNT in st.session_state:
#    default_account = st.session_state[states.ACTIVE_ACCOUNT]
#sd.sidebar_account_select(alist=st.session_state[states.ACCOUNT_LIST], default_account=default_account)
sd.sidebar_account_select(alist=st.session_state[states.ACCOUNT_LIST], default_account=st.session_state[states.ACTIVE_ACCOUNT])


sd.sidebar_account_info(account_json=st.session_state[states.ACCOUNTS_JSON])
st.write(st.session_state[states.ACTIVE_ACCOUNT])
st.stop()
#print(__name__)
#print(st.session_state['configfile'])

#FIELDS = tda.client.Client.Account.Fields
#CONFIG = Config()
#CONFIG.read_config(
#    config_file=st.session_state['configfile']
#)

plot = "Open Contracts"
by = "Expiration"
ptype = "Barplot"

def plot_open_contracts_by_expiration(plot_type):
    global CONFIG, FIELDS
    conf = CONFIG
    print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            raw = pentry["instrument"]['symbol'].split("_")[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                "long": 0.0,
                "short": 0.0
            }
            p[raw_exp]['long'] += pentry['longQuantity']
            p[raw_exp]['short'] += pentry['shortQuantity']
    for exp in p:
        for ptype in p[exp]:
            d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['exp', 'ptype', 'count']
    print(df.head())
    if plot_type == "Barplot":
        fig, ax = plt.subplots()
        sns.barplot(
            ax=ax,
            data=df,
            x="exp",
            y="count",
            hue="ptype"
        )
        ax.set_title("Contract count by expiration")
        for xtl in ax.get_xticklabels():
            xtl.set_rotation(90)
        fig.tight_layout()
        return fig,ax

def get_outstanding_premium_by_expiration():
    global CONFIG
    conf = CONFIG
    #print(conf)
    if states.POSITIONS_JSON in st.session_state:
        positions = st.session_state[states.POSITIONS_JSON]
    #client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    #acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    #accdata = acc_json['securitiesAccount']
    #positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    pos_df = schwabdata._get_pos_df(conf=CONFIG)
    pos_df['Opening Price'] = pos_df['averagePrice']*pos_df['quantity']*-1
    pos_df['Current Mark'] = pos_df['currentValue']*pos_df['quantity']
    st.dataframe(pos_df.head())
    for pentry in positions:
        #st.json(pentry)
        symbol = pentry["instrument"]['symbol'][0:6].rstrip()
        #st.write(symbol)
        if symbol == "SPX" or symbol == "SPXW":
            continue
        #print(pentry)
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            raw_exp= pentry["instrument"]['symbol'][6:12]
            if raw_exp not in p:
                p[raw_exp] = {
                "Current Mark": 0.0,
                "Opening Price": 0.0
            }
            p[raw_exp]['Current Mark'] += abs(pentry['marketValue'])
            p[raw_exp]['Opening Price'] += (
                (pentry['longQuantity'] + pentry['shortQuantity']) * pentry['averagePrice']*100
            )
    for exp in p:
        for ptype in p[exp]:
            d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['Expiration', 'Measure', 'Value']
    st.dataframe(df.head())
    return df
    #print(df.head())

def get_otm_df():
    global CONFIG
    conf = CONFIG
    #print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    df = fb.get_red_alert_df2(client, positions)
    df['expiration'] = "000101"
    for idx in df.index:
        sym = df.loc[idx,'symbol']
        raw = sym.split("_")[1][0:6]
        raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
        df.loc[idx, 'expiration'] = raw_exp
    return df.drop(columns='symbol')

def get_pmtlt_db_conn():
    import appdirs
    from appdirs import user_data_dir, user_config_dir
    from pathlib import Path
    import sqlite3
    import sqlalchemy
    global CONFIG
    conf = CONFIG
    PACKAGE_NAME = "pmtlottotracker"
    AUTHOR = "PMTraders"
    CONFIG_DIR = user_config_dir(appname=PACKAGE_NAME, appauthor=AUTHOR)
    CONFIG_PATH = Path(CONFIG_DIR, "config.toml")
    DATA_DIR = user_data_dir(appname=PACKAGE_NAME, appauthor=AUTHOR)
    DB_PATH = Path(DATA_DIR, "Lotto-Tracker.db")
    uri = "sqlite:///{}".format(DB_PATH)
    print(uri)
    conn = sqlalchemy.create_engine(uri)
    print(conn)
    return conn

def get_daily_premium_sold(STARTDATE=None):
    global CONFIG
    conf = CONFIG
    pmtlt_conn = get_pmtlt_db_conn()
    q = """
    SELECT option_symbol, date, price, filled_quantity, underlying_symbol, asset_type, instruction, status
    FROM orders_history
    WHERE status='FILLED'
    """
    if STARTDATE is not None:
        q = q + f" AND date > date({STARTDATE})"
    df = pd.read_sql_query(q, pmtlt_conn)

    df['date'] = pd.to_datetime(df['date'])
    df['total'] = df['price'] * df['filled_quantity']
    df.loc[df['instruction']=="BUY_TO_CLOSE",'total'] = df.loc[df['instruction']=="BUY_TO_CLOSE",'total'] * -1
    df.loc[df['instruction']=="BUY_TO_OPEN",'total'] = df.loc[df['instruction']=="BUY_TO_OPEN",'total'] * -1
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    #print(df.head())
    #print(df.info())
    return df



fig = None
ax = None
table = None

with st.expander(
    "Plot Selection",
    expanded=True
):
    plot_what = st.selectbox(
        "Plot what?",
        (
            "None",
            "Percent OTM",
            "Open Contracts",
            "Outstanding premium from open positions",
            "Daily Premium"
        ),
        index=0
    )
    if plot_what == "Daily Premium":
        days_back_str = st.text_input(
            "How many days back?",
            "14"
        )
        plot_by = st.selectbox(
            "Show daily premium by?",
            (
                "Date",
            ),
            index=0
        )
        plot_type = st.selectbox(
            "How to view daily premium?",
            (
                "Table",
                "Barplot",
                "Regplot"
            ),
            index=0
        )
        days_back = datetime.today() - timedelta(days=int(days_back_str))

    if plot_what == "Percent OTM":
        plot_by = st.selectbox(
            "Show - Percent OTM by?",
            (
                "None",
                "Table",
                "Total",
                "By Expiration and type"
            )
        )
    if plot_what == "Open Contracts":
        plot_by = st.selectbox(
            "Open Contract - By:",
            (
                "None",
                "Expiration"
            )
        )
        if plot_by == "Expiration":
            plot_type = st.selectbox(
                "Open Contracts by Expiration - How?",
                (
                    "Table"
                    "Barplot",
                ),
                index=0
            )
    if plot_what == "Outstanding premium from open positions":
        by_index = 0
        plot_by = st.selectbox(
            "Plot - Outstanding premium By?",
            (
                "Expiration",
            ),
            index=0
        )
        if plot_by == "Expiration":
            type_index = 0
        plot_type = st.selectbox(
            "Plot - Outstanding Premium by expiration how?",
            (
                "Barplot",
                "Table"
            ),
            index=type_index
        )
        if plot_type == "Barplot":
            hue_set = st.selectbox(
                "Measures to show",
                (
                    "All",
                    "Opening Price",
                    "Current Mark"
                ),
                index=0
            )
## End select box expander



with st.container():
    with st.spinner("Loading plot"):
        if plot_what == "Open Contracts":
            if plot_by == "Expiration":
                if plot_type == "Barplot":
                    fig, ax = plot_open_contracts_by_expiration(plot_type)
        elif plot_what == "Daily Premium":
            order_history_df = get_daily_premium_sold()
            table = trimmed_df = pd.DataFrame(
                order_history_df.loc[order_history_df['date'] >= days_back, :].groupby('date')['total'].sum()
            ).reset_index()
            #print(table.head())
            #print(table.info())
            table['total'] = table['total']*100
            table['date'] = table['date'].dt.strftime("%Y-%m-%d")
            if plot_type == "Barplot":
                #min_width = 6
                #factor = 1.5
                #print("lenght", len(table['date']))
                #if int(len(table['date']) / factor) > min_width:
                #    min_width = int((len(table['date']) / factor)+0.5)
                #height = int((min_width*3)/2)
                fig, ax = plt.subplots()
                sns.barplot(
                    ax=ax,
                    data=table,
                    x="date",
                    y="total"
                )
                for xtl in ax.get_xticklabels():
                    xtl.set_rotation(90)
                if int(days_back_str) < 100:
                    for container in ax.containers:
                        print(container)
                        ax.bar_label(container, rotation=90)

                fig.suptitle("Daily premium sold since {}".format(days_back.strftime("%Y-%m-%d")))
                ax.set_frame_on(False)
                #fig.tight_layout()
            if plot_type == "Regplot":
                lmp = sns.lmplot(
                    #ax=ax,
                    data=table,
                    x="date",
                    y="total"
                )
                fig = lmp.figure
                #for xtl in ax.get_xticklabels():
               #     xtl.set_rotation(90)
                #if int(days_back_str) < 21:
                #    for container in ax.containers:
                 #       ax.bar_label(container)



            #table = order_history_df

        elif plot_what == "Outstanding premium from open positions":
            if plot_by == "Expiration":
                if plot_type == "Barplot":
                    print("Making plot")
                    datadf = get_outstanding_premium_by_expiration().sort_values("Expiration")
                    if hue_set != "All":
                        datadf = datadf.loc[datadf['Measure']==hue_set,:]
                    fig, ax = plt.subplots()
                    sns.barplot(ax=ax, data=datadf, x="Value", y="Expiration", hue="Measure")
                    ax.set_title("Outstanding Premium barplot by expiration")
                    for container in ax.containers:
                        print(container)
                        ax.bar_label(container)
                    fig.tight_layout()
                if plot_type == "Table":
                    table = get_outstanding_premium_by_expiration(plot_type).sort_values("Expiration")
                    print(type(table))
        elif plot_what == "Percent OTM":
            if plot_by != "None":
                table = get_otm_df()
                if plot_by == "Total":
                    table['otm'] = table['otm']*100
                    fig, ax = plt.subplots()
                    sns.histplot(ax=ax, data=table, x='otm')
                    fig.suptitle("Histogram of position %OTM")
                    ax.set_xlabel("% OTM")
                if plot_by == "By Expiration and type":
                    table['otm'] = table['otm']*100
                    table.loc[table['ctype']=='C','ctype'] = "Call"
                    table.loc[table['ctype']=='P','ctype'] = "Put"
                    fg = sns.FacetGrid(data=table, col='expiration', row='ctype')
                    fig = fg.fig
                    fg.map_dataframe(sns.histplot, x="otm")
                    fig.suptitle("Position %OTM histogram for each contract type and expiration")
                    fig.tight_layout()


if fig is not None:
    st.pyplot(fig)
elif table is not None:
    st.dataframe(table)
else:
    st.write("No Plot To Show")
