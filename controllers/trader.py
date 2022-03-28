import os
import json
from flask import request
from flask import Blueprint
from binance.client import Client
from utils.logger import Logger

log = Logger()
bp = Blueprint("trader", __name__)
WEBHOOK_PASSPHRASE = os.environ['WEBHOOK_PASSPHRASE']

@bp.route("/", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    log.info(data)
    if data['passphrase'] != WEBHOOK_PASSPHRASE:
        side = data['strategy']['order_action'].upper()
        quantity = data['strategy']['order_contracts']
        ticker = data['strategy']['ticker']

        if data['client'] == '1':
            client = Client(os.environ['API_KEY_ONE'], os.environ['API_SECRET_ONE'])
        else:
            client = Client(os.environ['API_KEY_TWO'], os.environ['API_SECRET_TWO'])

        order_response = order(client, side, quantity, ticker)

        if order_response:
            return buildResponse(200, 'success')
        else:
            log.error(f' [*] - Error Trader - order_response - {order_response}')
            return buildResponse(404, 'fail')

    return buildResponse(401, 'Error in inf statement')

def order(client, side, quantity, symbol, order_type='ORDER_TYPE_MARKET'):
    try:
        log.info("sending order {} - {} {} {}".format(order_type, side, quantity, symbol))
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        log.info(order)
    except Exception as e:
        log.error("an exception occured - {}".format(e))
        return False
    return True

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