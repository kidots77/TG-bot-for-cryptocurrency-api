import os
import json

from dotenv import load_dotenv
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

load_dotenv()

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
  'start': '1',
  'limit': '100',
  'convert': 'USD'
}
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': os.getenv('API_KEY'),
}

session = Session()
session.headers.update(headers)


def coin_name():
    try:
        response = session.get(url, params=parameters)
        result = json.loads(response.text)['data']
        my_list = [result[i]['name'] for i in range(len(result))]
        return my_list
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)


def coin_price(coin_name):
    try:
        response = session.get(url, params=parameters)
        result = json.loads(response.text)['data']
        for i in range(len(result)):
            name = result[i]
            if name['name'] == coin_name:
                return name['quote']['USD']['price']
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
