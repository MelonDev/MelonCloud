import datetime
import json
import math
from collections import Counter, OrderedDict

from fastapi import APIRouter, Depends, status as code
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
import datetime as dt
from operator import is_not, getitem
from functools import partial
from operator import itemgetter

import requests as req_outside

from src.database.meloncloud.meloncloud_crypto_portfolios_database import MelonCloudCryptoPortfoliosDatabase
from src.environments.database_config import get_db
from src.routers.twitter_api import bad_request_exception
from src.tools.verify_hub import response

router = APIRouter()


def get_data():
    response = req_outside.request("GET", f"https://api.bitkub.com/api/market/ticker", headers={}, data={})
    data = json.loads(response.text)
    return data


@router.get("/")
async def price(db: Session = Depends(get_db)):
    data = get_data()
    return response(data)


@router.get("/portfolio")
async def portfolio(db: Session = Depends(get_db)):
    database = db.query(MelonCloudCryptoPortfoliosDatabase)
    data = get_data()

    portfolios = {}

    total_percent_change = 0
    total_balance_change = 0
    total_balance = 0

    coins = {}

    if portfolios is None or data is None:
        bad_request_exception()

    for item in database:
        if item.portfolio_name not in portfolios:
            portfolios[item.portfolio_name] = {
                "tokens": []
            }
        data_per_coin = data[f'THB_{item.coin_symbol}']
        portfolio = {
            "name": item.coin_name,
            "symbol": item.coin_symbol,
            "price": data_per_coin['last'],
            "percent_change": data_per_coin['percentChange'],
            "price_change": data_per_coin['change'],
            "balance": item.value,
            "balance_baht": data_per_coin['last'] * item.value,
            "balance_change": data_per_coin['change'] * item.value,
        }

        if item.coin_symbol not in coins:
            coins[item.coin_symbol] = {
                "name": item.coin_name,
                "symbol": item.coin_symbol,
                "balance": 0,
                "balance_baht": 0,
                "balance_change": 0
            }
        coins[item.coin_symbol]['balance'] += item.value
        coins[item.coin_symbol]['balance_baht'] += data_per_coin['last'] * item.value
        coins[item.coin_symbol]['balance_change'] += data_per_coin['change'] * item.value

        total_balance += portfolio['balance_baht']
        total_balance_change += portfolio['balance_change']
        portfolios[item.portfolio_name]['tokens'].append(portfolio)

    for k, v in portfolios.items():
        percent_change = 0
        balance_baht = 0
        balance_change = 0
        for token in v['tokens']:
            percent_change += token['percent_change']
            balance_baht += token['balance_baht']
            balance_change += token['balance_change']
        for token in v['tokens']:
            token['percent'] = percent_of(balance_baht, token['balance_baht'])
        v['tokens'] = sorted(v['tokens'], key=itemgetter('percent'), reverse=True)

        portfolios[k]['summary'] = {
            "percent": percent_of(total_balance, balance_baht),
            "percent_change": percent_change / len(v['tokens']),
            'balance': balance_baht,
            'balance_change': balance_change
        }

        total_percent_change += percent_change

    portfolios = OrderedDict(sorted(portfolios.items(), key=lambda x: x[1]['summary']['balance'], reverse=True))
    coins = OrderedDict(sorted(coins.items(), key=lambda x: getitem(x[1], 'balance_baht'), reverse=True))
    for c, v in coins.items():
        status = "Neutral"
        if v['balance_change'] > 0:
            status = "Positive"
        if v['balance_change'] < 0:
            status = "Negative"

        percent = percent_of(total_balance, v['balance_baht'])
        percent_balance_change = percent_of(total_balance_change, v['balance_change'])
        weight = percent_balance_change / abs(percent)
        v['percent'] = percent
        v['weight'] = weight
        v['status'] = status

    result = {
        "portfolios": portfolios,
        "coins": coins,
        "summary": {
            "balance": total_balance,
            "balance_change": total_balance_change,
            "percent_change": total_percent_change / len(portfolios)
        }
    }

    return response(result)


def percent_of(x, y):
    return y / (x / 100)
