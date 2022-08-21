import os, ccxt
import json
from flask import request
from flask import Blueprint
from binance.client import Client
from binance.enums import *
from utils.logger import Logger
from datetime import datetime, timedelta



#### Variables
bp = Blueprint("trader", __name__)
WEBHOOK_PASSPHRASE = os.environ['WEBHOOK_PASSPHRASE']
log = Logger()
days_delta = 3
price_delta = 1
total2 = {"BNBUSDT":0.2,"MATICUSDT":30,"NEARUSDT":4,"SOLUSDT":1.3,"ADAUSDT":70}

@bp.route("/", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    log.info(data)
    if data['passphrase'] == WEBHOOK_PASSPHRASE:
        ticker = data['ticker']
        side = data['strategy']['order_action'].upper()
        quantity = str(data['strategy']['order_contracts'])
        price = data['bar']['close']
        
        if data['client'] == 'futures':
            #client = Client(os.environ['API_KEY_ONE'], os.environ['API_SECRET_ONE'])
            client = client_one()
            order_response = future_order(client, side, quantity, ticker)
        else:
            #client = Client(os.environ['API_KEY_TWO'], os.environ['API_SECRET_TWO'])
            client = Client(os.environ['API_KEY_ONE'], os.environ['API_SECRET_ONE'])
        
        if ticker == "total2":
            for t in total2:
                if order_approval(client, side, t):
                    log.info(t)
                    order_response = order(client, side, total2[t], t)
                    log.info(order_response)
                else: order_response = False
        else:
            if order_approval(client, side, ticker):
                order_response = order(client, side, quantity, ticker)
            else: order_response = False
        
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
    try:
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
    except Exception as e:
        log.error(f"an exception occured - {e}")
        return False
    return exchange

def trailing_order(exchange, side, quantity, symbol, price, order_type=ORDER_TYPE_MARKET):
    try:
        params = {
            'newClientOrderId': "{}-{}".format(price, side),
            'activationPrice': price,  
            'callbackRate': '2',
            'workingType': 'CONTRACT_PRICE',
            'reduceOnly': 'true',
        }
        order = exchange.createOrder(symbol, 'TRAILING_STOP_MARKET', side, quantity, price, params)
    except Exception as e:
        log.error(f"an exception occured - {e}")
        return False
    return order

def order_approval(client, side, symbol):
    try:
        orders = client.get_all_orders(symbol=symbol, limit=1)
    except Exception as e:
        log.error(f"an exception occured - {e}") 
    if side == 'SELL': return True
    else:
        Last_action = orders[-1]['side']
        actual_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        last_buy_price = float(orders[-1]['cummulativeQuoteQty']) * float(orders[-1]['origQty'])
        delta_percentage = last_buy_price * 0.05
        if Last_action == 'SELL':
            log.info(f"[*] - Last action SELL")
            return True    
        else:
            if last_buy_price - actual_price > delta_percentage:
                log.info(f"[*] - Price delta is last {last_buy_price} - actual {actual_price} = {last_buy_price - actual_price} es mayor que {delta_percentage}") 
                return True
            else:
                log.error(f"[*] - Price delta is under 5%")
                return False






def order_creator(exchange, order_type, symbol, side, quantity, price, params):
    try:
        order = exchange.createOrder(symbol, order_type, side, quantity, price, params)
    except Exception as e:
        log.error("{} - an exception occured".format(order_type, e))
        return False
    return order

def future_order(exchange, side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        tickerDict = {"BTCUSDT":"BTC/USDT", "GMTUSDT":"GMT/USDT", "SOLUSDT":"SOL/USDT" }
        symbol = tickerDict[symbol]
        marketPrice = exchange.fetchFundingRate(symbol)['info']['markPrice'][:-9]
        if side == 'buy':
            stopPrice = int(marketPrice) - 0.005*int(marketPrice)
            trailingPrice = int(marketPrice) + 0.003*int(marketPrice)
            order = order_creator(exchange, 'LIMIT', symbol, side, quantity, marketPrice, {'stopPrice': marketPrice , 'timeInForce':'GTC'} )
            stopParams = {"stopPrice": stopPrice-1}
            stopOrder = order_creator(exchange,'STOP_MARKET', symbol, 'sell', quantity, stopPrice, stopParams )
            log.info(stopOrder)
            params = {
                'newClientOrderId': "{}-{}".format(trailingPrice, side),
                'activationPrice': trailingPrice-1,  
                'callbackRate': '2',
                'workingType': 'CONTRACT_PRICE',
                'reduceOnly': 'true',
            }
            trailingOrder = order_creator(exchange,'TRAILING_STOP_MARKET', symbol, side, quantity, trailingPrice, params)
            log.info(trailingOrder)
        else: 
            stopPrice = int(marketPrice) + 0.005*int(marketPrice)
            trailingPrice = int(marketPrice) - 0.003*int(marketPrice)
            stopParams = {"stopPrice": stopPrice+1}
            order = order_creator(exchange, 'LIMIT', symbol, side, quantity, marketPrice, {'stopPrice': marketPrice , 'timeInForce':'GTC'} )
            stopOrder = order_creator(exchange,'STOP_MARKET', symbol, 'buy', quantity, stopPrice, stopParams )
            params = {
                'newClientOrderId': "{}-{}".format(trailingPrice, side),
                'activationPrice': trailingPrice+1,  
                'callbackRate': '2',
                'workingType': 'CONTRACT_PRICE',
                'reduceOnly': 'true',
            }
            trailingOrder = order_creator(exchange,'TRAILING_STOP_MARKET', symbol, side, quantity,trailingPrice, params)
            log.info(trailingOrder)
    except Exception as e:
        log.error(f"an exception occured - {e}")
        return False
    return order