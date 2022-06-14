import os, ccxt
import json
from flask import request
from flask import Blueprint
from binance.client import Client
from binance.enums import *
from utils.logger import Logger

bp = Blueprint("trader", __name__)
WEBHOOK_PASSPHRASE = os.environ['WEBHOOK_PASSPHRASE']
log = Logger()


@bp.route("/", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    log.info(data)
    if data['passphrase'] == WEBHOOK_PASSPHRASE:
        ticker = data['ticker']
        side = data['strategy']['order_action'].upper()
        quantity = str(data['strategy']['order_contracts'])
        price = data['bar']['close']
        
        if data['client'] == '1':
            #client = Client(os.environ['API_KEY_ONE'], os.environ['API_SECRET_ONE'])
            client = client_one()
        else:
            client = Client(os.environ['API_KEY_TWO'], os.environ['API_SECRET_TWO'])

        order_response = future_order(client, side, quantity, ticker, price)
        #order_response = order(client, side, quantity, ticker)
        log.info(order_response)
        if order_response:
            return buildResponse(200, 'success')
        else:
            log.error(f' [*] - Error Trader - order_response - {order_response}')
            return buildResponse(404, 'fail')
    else:
        return buildResponse(401, 'Error in inf statement')

def order(client, side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        log.info(f"sending order {order_type} - {side} - {quantity} - {symbol}")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
    except Exception as e:
        log.error(f"an exception occured - {e}")
        return False
    return order

def buildResponse(statusCode, body=None):
    response = {
        'statusCode' : statusCode,
        'headers' : {
            'Content-type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body)
    return response

def client_one():
    exchange_class = getattr(ccxt, 'binance')
    exchange = exchange_class({
            'apiKey': os.environ['API_KEY_ONE'],
            'secret': os.environ['API_SECRET_ONE'],
            'timeout': 10000,
            'enableRateLimit': True,
            'rateLimit': 250,
            'options': {
                'defaultType': 'future',
            }
        })
    return exchange

def future_order(exchange, side, quantity, symbol, price, order_type=ORDER_TYPE_MARKET):
    ticker_dict = {"BTCUSDT":"BTC/USDT", "GMTUSDT":"GMT/USDT", "SOLUSDT":"SOL/USDT" }
    try:
        params = {
            'newClientOrderId': "{}-{}".format(price, side),
            'activationPrice': price,  
            'callbackRate': '2',
            'workingType': 'CONTRACT_PRICE',
            'reduceOnly': 'true',
        }
        order = exchange.createOrder(symbol, 'TRAILING_STOP_MARKET', side, quantity, price, params)
        log.info(order)
    except Exception as e:
        log.error(f"an exception occured - {e}")
        return False
    return order
