# %%
import logging
import os

import pandas as pd
import requests
import yaml

logging.basicConfig(level=logging.INFO)

with open('config.yaml') as f:
    tasks = yaml.safe_load(f)

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

writer = pd.ExcelWriter('fundingRate.xlsx', engine='xlsxwriter')

# %% FTX
logging.info('Generating FTX sheet')
# require data
df_FTX = pd.DataFrame(columns=['instrument', 'last_price', 'bid_price', 'best_ask', 'index_price', 'next_funding_rate', 'next_funding_time'])
for task in tasks:
    for instrument in task['instruments']:
        futures = requests.get(f'https://ftx.com/api/futures/{instrument}/stats').json()['result']
        prices = requests.get(f'https://ftx.com/api/futures/{instrument}').json()['result']
        df_FTX.loc[len(df_FTX)] = [instrument] + [prices[k] for k in ['last', 'bid', 'ask', 'index']] + [futures[k] for k in ['nextFundingRate', 'nextFundingTime']]  # type: ignore

# process data
df_FTX['annualised_funding_rate'] = df_FTX['next_funding_rate'] * 24 * 365

df_FTX.head()
df_FTX.to_excel(writer, index=False, sheet_name='FTX')

# %% Gate.io
logging.info('Generating Gate.io sheet')
# require data
host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
url = '/futures/usdt/tickers'
query_param = ''

r = requests.request('GET', host + prefix + url, headers=headers).json()
df_Gate = pd.DataFrame(r)[['contract', 'last', 'index_price', 'mark_price', 'funding_rate_indicative']]

# process data
df_Gate.columns = ['instrument', 'last_price', 'index_price', 'mark_price', 'next_funding_rate']

df_Gate.head()
df_Gate.set_index('instrument').sort_index().to_excel(writer, index=True, sheet_name='Gate.io')

# %% Combined
logging.info('Generating combined sheet')
df_FTX['instrument'] = df_FTX['instrument'].str[:-5]
df_FTX['exchange'] = 'FTX'
df_Gate['instrument'] = df_Gate['instrument'].str[:-5]
df_Gate = df_Gate[df_Gate['instrument'].isin(df_FTX['instrument'].tolist())]
df_Gate['exchange'] = 'Gate.io'
df_Gate['annualised_funding_rate'] = pd.to_numeric(df_Gate['next_funding_rate']) * 24 * 365

header = ['instrument', 'exchange', 'last_price', 'index_price', 'next_funding_rate', 'annualised_funding_rate']
df_combined = pd.concat([df_FTX[header], df_Gate[header]])
df_combined = df_combined.set_index(header[:2]).sort_index()
df_combined.head()
df_combined.to_excel(writer, index=True, sheet_name='Combined')

# %%
writer.save()
logging.info('excel saved')
# %%
