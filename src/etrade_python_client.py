"""This Python script provides examples on using the E*TRADE API endpoints"""
from __future__ import print_function
import webbrowser
import json
import logging
import configparser
import sys
import csv
import requests
from rauth import OAuth1Service
from logging.handlers import RotatingFileHandler
from accounts.accounts import Accounts
from market.market import Market
from order.order import Order
import pprint 
pp = pprint.PrettyPrinter(indent=1)

# loading configuration file
config = configparser.ConfigParser()
config.read('/Users/puberoy/.etrade/config.ini')

# logger settings
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("python_client.log", maxBytes=5*1024*1024, backupCount=3)
FORMAT = "%(asctime)-15s %(message)s"
fmt = logging.Formatter(FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(fmt)
logger.addHandler(handler)


def oauth():
    """Allows user authorization for the sample application with OAuth 1"""
    etrade = OAuth1Service(
        name="etrade",
        consumer_key=config["DEFAULT"]["CONSUMER_KEY"],
        consumer_secret=config["DEFAULT"]["CONSUMER_SECRET"],
        request_token_url="https://api.etrade.com/oauth/request_token",
        access_token_url="https://api.etrade.com/oauth/access_token",
        authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
        base_url="https://api.etrade.com")

    base_url = config["DEFAULT"]["PROD_BASE_URL"]
    # Step 1: Get OAuth 1 request token and secret
    request_token, request_token_secret = etrade.get_request_token(
        params={"oauth_callback": "oob", "format": "json"})

    # Step 2: Go through the authentication flow. Login to E*TRADE.
    # After you login, the page will provide a text code to enter.
    authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
    webbrowser.open(authorize_url)
    text_code = input("Please accept agreement and enter text code from browser: ")

    # Step 3: Exchange the authorized request token for an authenticated OAuth 1 session
    session = etrade.get_auth_session(request_token,
                                  request_token_secret,
                                  params={"oauth_verifier": text_code})

    main_menu(session, base_url)

    def writeCSV(self, list):
        with open('port.csv', 'w', newline='') as csvfile:
            fieldnames = ['action', 'type', 'price', 'accountIdKey', 'symbolDescription', 'quantity', 'lastTrade', 'pricePaid', 'totalGain', 'marketValue',  'totalGainPct', 'daysGainPct', 'daysGain']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for port in list:
                port['action'] = "None"
                port['type'] = "STOP"
                port['lastTrade']=port['Quick']['lastTrade']
                port['price'] = int(port['Quick']['lastTrade'] * 95)/100
                writer.writerow(port)

def checkAccountOrder(act, ord):
    with open('diff.csv', 'w', newline='') as csvfile:
        fieldnames = ['action', 'type', 'price', 'accountIdKey', 'symbolDescription', 'quantity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for accountId in act.keys():
            port = act[accountId]
            for stock in port:
                sym = stock['symbolDescription']
                quant = stock['quantity']
               # print("Look for %s %s %s " %(accountId, sym, quant)), 
                foundSame = False 
                if ord[accountId] != None: 
                    for order in ord[accountId]:
                        if (order['symbol']==sym and order['price_type']=='STOP'):
                            if (order['quantity']==quant):
                                foundSame = True 
                            else:
                                #cancel order
                                print ("Cancel Order", sym, quant, order['quantity'])
                                stock['action'] = 'CANCEL_ORDER'
                                stock['type'] = "STOP"
                                stock['price'] = order['order_id']
                                writer.writerow(stock)
                if (foundSame):
                    print ("No Change For", sym, quant)
                else:
                    print ("*** Generate new Order", sym, quant)
                    stock['action'] = "SELL"
                    stock['type'] = "STOP"
                    stock['lastTrade']=stock['Quick']['lastTrade']
                    stock['price'] = int(stock['Quick']['lastTrade'] * 95)/100                    
                    writer.writerow(stock)

def main_menu(session, base_url):
    """
    Provides the different options for the sample application: Market Quotes, Account List

    :param session: authenticated session
    """

    market = Market(session, base_url)
    accounts = Accounts(session, base_url)
    order = Order(session, {}, base_url)

    # ret = market.quoteCommon("vsat")
    # print ("MARKET FOR VST", ret)

    accountsObj = accounts.printPorfolio()
    accountsList = accountsObj['acct']
    accountsPort = accountsObj['port']
    ordersAcct = {}
    for account in accountsList:
        ordersAcct[account['accountId']] = order.viewOpenOrder(account, False)
    checkAccountOrder(accountsPort, ordersAcct)
    menu_items = {"1": "Market Quotes",
                  "2": "Account List",
                  "3": "Place File order", 
                  "4": "Cancel all open orders",
                  "5": "Cancel ALL orders and redo on current price",
                  "6": "redo diff orders",
                  "7": "Exit"}

    while True:
        print("")
        options = menu_items.keys()
        for entry in options:
            print(entry + ")\t" + menu_items[entry])
        selection = input("Please select an option: ")
        if selection == "1":
            market.quotes()
        elif selection == "2":
            accounts.account_list()
        elif selection == "3":
            order.readCSV(False)
        elif selection == "4":
            for account in accountsList:
                order.viewOpenOrder(account, True)
        elif selection == "5":
            for account in accountsList:
                order.viewOpenOrder(account, True)
            order.readCSV(True)
        elif selection == "6":
            order.dodiff()
        elif selection == "7":
            break
        else:
            print("Unknown Option Selected!")


if __name__ == "__main__":
    oauth()
