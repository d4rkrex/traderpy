import os, ccxt
import json
from flask import request
from flask import Blueprint
from binance.client import Client
from binance.enums import *
from utils.logger import Logger
from datetime import datetime, timedelta
from bingX import BingX



#### Variables
bp = Blueprint("trader", __name__)
WEBHOOK_PASSPHRASE = os.environ['WEBHOOK_PASSPHRASE']
log = Logger()
days_delta = 3
price_delta = 1
total2 = {"BNBUSDT":0.2,"MATICUSDT":45,"NEARUSDT":6,"DOTUSDT":15,"ADAUSDT":150}
total2sell = {"BNBUSDT":0.1,"MATICUSDT":15,"NEARUSDT":2,"DOTUSDT":5,"ADAUSDT":50}

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
            check_and_open_position(ticker, quantity, side)
            return buildResponse(200, 'success')
            #client = client_one()
            #order_response = future_order(client, side, quantity, ticker)
        else:
            #client = Client(os.environ['API_KEY_TWO'], os.environ['API_SECRET_TWO'])
            client = Client(os.environ['API_KEY_ONE'], os.environ['API_SECRET_ONE'])
        
        if ticker == "total2":
            if side == "buy":
                for t in total2:
                    print(t)
                    log.info(t)
                    if order_approval(client, side, t):
                        order_response = order(client, side, total2[t], t)
                        log.info(order_response)
                    else: order_response = False
            else:
                for t in total2sell:
                    print(t)
                    log.info(t)
                    if order_approval(client, side, t):
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
    print(symbol)
    try:
        orders = client.get_all_orders(symbol=symbol, limit=1)
        print("Ultima orden fue:")
        print(orders)
        if not orders:
            return True
    except Exception as e:
        log.error(f"an exception occured - {e}") 
    if side == 'SELL': return True
    else:
        try:
            Last_action = orders[-1]['side']
        except Exception as e:
            print(f"Error al obtener ultima orden: {e}")
            log.error(f"[*] - Error al obtener ultima orden: {e}")
            return True
        actual_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        print(f"actual price: {actual_price}")
        last_buy_price = float(orders[-1]['cummulativeQuoteQty']) * float(orders[-1]['origQty'])
        print(f"last buy: {last_buy_price}")
        delta_percentage = last_buy_price * 0.05
        if Last_action == 'SELL':
            log.info(f"[*] - Last action SELL")
            return True    
        else:
            if last_buy_price - actual_price > delta_percentage:
                print(f"[*] - Price delta is last {last_buy_price} - actual {actual_price} = {last_buy_price - actual_price} es mayor que {delta_percentage}")
                log.info(f"[*] - Price delta is last {last_buy_price} - actual {actual_price} = {last_buy_price - actual_price} es mayor que {delta_percentage}") 
                return True
            else:
                log.error(f"[*] - Price delta is under 5%")
                return False

def order_creator(exchange, order_type, symbol, side, quantity, price, params):
    try:
        order = exchange.createOrder(symbol, order_type, side, quantity, price, params)
    except Exception as e:
        log.error("{} - an exception occured en la orden".format(order_type, e))
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


def get_current_price(symbol):
    try:
        # Obtén el precio actual del símbolo
        ticker_response = bingx_client.perpetual_v2.market.get_ticker(symbol)
        current_price = float(ticker_response['lastPrice'])
        return current_price
    except Exception as e:
        print(f"Error al obtener el precio actual: {e}")
        log.error(f"[*] - Error al ejecutar la orden ")
        return None

def check_and_open_position(symbol, quantity, side):
    try:
        # Obtén todas las posiciones abiertas
        keyS = os.environ['API_KEY_2']
        secretK = os.environ['API_SECRET_2']
        bingx_client = BingX(api_key=keyS, secret_key=secretK)
        positions_response = bingx_client.perpetual_v2.account.get_swap_positions()
    except Exception as e:
        print(f"Error al obtener posiciones: {e}")
        log.info(f"[*] - Error al obtener posiciones:")
        return
    # Busca una posición existente del símbolo
    existing_position = None
    for position in positions_response:
        if position['symbol'] == symbol:
            existing_position = position
            break
    # Si existe una posición, verifica el precio actual
    if existing_position:
        entry_price = float(existing_position['entryPrice'])
        current_price = get_current_price(symbol)
        if current_price is None or current_price >= entry_price * 0.95:
            print("El precio actual no está un 5% por debajo del precio de apertura o no se pudo obtener el precio actual.")
            log.info(f"[*] - El precio actual no está un 5% por debajo del precio de apertura o no se pudo obtener el precio actual.")
            return
    # Si no existe una posición o si el precio actual está un 5% por debajo del precio de apertura,
    # abre una nueva posición con un apalancamiento de 10x
    try:
        order_response = bingx_client.perpetual_v2.trade.create_order(
            symbol=symbol,
            side=side,  # "BUY" para abrir, "SELL" para cerrar
            type="MARKET",
            quantity=quantity,
            leverage="10"  # Apalancamiento de 10x
        )
        print(f"Orden {side} ejecutada con éxito: {order_response}")
        log.info(f"Orden {side} ejecutada con éxito: {order_response}")
    except Exception as e:
        print(f"Error al ejecutar la orden {side}: {e}")
        log.error(f"[*] - Error al ejecutar la orden ")