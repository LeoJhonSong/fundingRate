import pandas as pd
import requests
import yaml
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
data = pd.DataFrame(columns=["instrument", "nextFundingRate", "nextFundingTime"])

with open('config.yaml') as f:
    tasks = yaml.safe_load(f)


for task in tasks:
    # append balance of BTC data
    for instrument in task["instrument"]:
        futures = requests.get(f'https://ftx.com/api/futures/{instrument}/stats').json()
        for item in futures:
            data.loc[len(data)] = [task["instrument"]] + [item[k] for k in ['nextFundingRate', 'nextFundingTime']]
    print(data)
