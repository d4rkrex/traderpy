from binance.client import Client 
from binance.enums import *
from flask import Flask , request
#from binance.websockets import BinanceSocketManager
#from twisted.internet import reactor
import json, configparser
app = Flask(__name__)


def getVars(section, v):
    config_file = "./vars.conf"
    config = configparser.ConfigParser()
    config.read(config_file)
    varObj = config[section]
    _var = varObj.get(v)
    return _var

def print_banner(text):
    print('\n')
    print(colored('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=', 'grey'))
    print(colored('=-=-=-=-=-=-=-=-=-=-=-=-=-=- {} -=-=-=-=-=-=-=-=-=-=-=-=-=-=-='.format(text), 'yellow'))
    print(colored('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=', 'grey'))

client = Client(getVars('VARS', 'API_KEY'), getVars('VARS', 'API_SECRET'))

def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        print ("sending order {} - {} {} {}".format(order_type, side, quantity, symbol))
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True

@app.route("/ping", methods=['GET'])
def ping():
    return "PONG"

@app.route("/webhook", methods=['POST'])
def webhook():   
    data = json.loads(request.data)
    print(data)
    if data['passphrase'] != getVars('VARS', 'WEBHOOK_PASSPHRASE'):
        side = data['strategy']['order_action'].upper()
        quantity = data['strategy']['order_contracts']
        ticker = data['strategy']['ticker']
        order_response = order(side, quantity, ticker)
        if order_response:
            return  {
            "code": "success"
            }
        else: 
            print("fail") 
            return {
                "code": "error"
            } 
    return {
                "code": "error",
                "message": "error in if statement"
            } 
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)