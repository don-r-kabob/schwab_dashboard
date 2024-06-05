import sys
import os

import yaml

import schwabdata
import stutils
from account import AccountList

script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)

from states import states

from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit_dashboard as sd

with open("dashboard_config.yaml", 'r') as dconf_fh:
    dashconfig = yaml.load(dconf_fh, Loader=yaml.Loader)

if states.CONFIG in st.session_state:
    CONFIG = st.session_state[states.CONFIG]
if states.ACCOUNT_LIST not in st.session_state:
    client = stutils.get_schwab_client(CONFIG)
    accounts_json = client.get_account_numbers().json()
    alist = AccountList(jdata=accounts_json)


sd.sidebar_account_select(alist=st.session_state[states.ACCOUNT_LIST], default_account=st.session_state[states.ACTIVE_ACCOUNT])




#sd.sidebar_account_select(alist=st.session_state[states.ACCOUNT_LIST], default_account=default_account)
#sd.sidebar_account_select(alist=st.session_state[states.ACCOUNT_LIST], default_account=default_account)

sd.sidebar_account_info(account_json=st.session_state[states.ACCOUNTS_JSON])
#st.write(st.session_state[states.ACTIVE_ACCOUNT])
sd.__account_change(active_account=st.session_state[states.ACTIVE_ACCOUNT])
#st.json(st.session_state, expanded=False)
#st.stop()
#print(__name__)
#print(st.session_state['configfile'])

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
    #st.dataframe(pos_df.head())
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
    #st.dataframe(df.head())
    return df
    #print(df.head())

fig = None
ax = None
table = None

plot_control_con = st.expander("Plot Control", expanded=True)

with plot_control_con:
    plot_what = st.selectbox(
        "Plot what?",
        (
            "None",
            #"Percent OTM",
            #"Open Contracts",
            "Outstanding premium from open positions",
            #"Daily Premium"
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
        units = st.selectbox(
            "op_units",
            (
                "Percent",
                "Dollars"
            ),
            index=0
        )
## End select box expander

data_con = st.container()


with data_con:
    with st.spinner("Loading plot"):
        if plot_what == "Outstanding premium from open positions":
            if plot_by == "Expiration":
                if plot_type == "Barplot":
                    datadf = get_outstanding_premium_by_expiration().sort_values("Expiration")
                    #st.dataframe(datadf)
                    if hue_set != "All":
                        datadf = datadf.loc[datadf['Measure']==hue_set,:]
                    if units == "Percent":
                        nlv = schwabdata.get_account_nlv(st.session_state[states.ACCOUNTS_JSON])
                        datadf['Value'] = round(datadf['Value']/float(nlv)*100, ndigits=2)

                    exp_filter = st.multiselect("Expirations Filter", datadf['Expiration'].unique())
                    datadf = datadf.loc[~datadf['Expiration'].isin(exp_filter), :]
                    fig, ax = plt.subplots()
                    sns.barplot(ax=ax, data=datadf, x="Value", y="Expiration", hue="Measure")
                    ax.set_title(f"Outstanding Premium in {units} by {plot_by}")
                    for container in ax.containers:
                        ax.bar_label(container)
                    fig.tight_layout()
                if plot_type == "Table":
                    table = get_outstanding_premium_by_expiration().sort_values("Expiration")


if fig is not None:
    st.pyplot(fig)
elif table is not None:
    st.dataframe(table)
else:
    st.write("No Plot To Show")
