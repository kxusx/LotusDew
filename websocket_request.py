import websocket
import ssl
import pandas as pd
from websocket import create_connection, WebSocketConnectionClosedException
import json

ws = websocket.create_connection("wss://api.airalgo.com/socket/websocket", sslopt={"cert_reqs": ssl.CERT_NONE})
conn = {
    "topic" : "api:join",
    "event" : "phx_join",
    "payload" :
        {
            "phone_no" :"8008338216"
        },
    "ref" : ""
    }
ws.send(json.dumps(conn))
print(ws.recv())

def getCurrentPrice(tickerList):
    # get current prices
    currentPricesList = {key : [] for key in tickerList}

    while True:
      data = json.loads(ws.recv())
      print(data)
      p = data['payload']
      price = p[2]
      symbol = p[0]['symbol']
      # ensure only 300 prices are stored for each ticker
      if len(currentPricesList[symbol]) < 1:
          currentPricesList[symbol].append(price)
      # check if all tickers have 300 prices, then break
      if all(len(pricesList[key]) >= 1 for key in tickers):
          break
    
    return currentPricesList

def create_payload(tickers):
    symbol_list = []
    for i in tickers:
        symbol_list.append(i)

    payload = {
      "topic" : "api:join",
      "event" : "ltp_quote", 
      "payload" : symbol_list, 
      "ref" : ""
      }
    return payload

def buy_stocks(key, currentPricesList):
    order = {
      "topic" : "api:join", 
      "event" : "order", 
      "payload" : {
          "phone_no" : "8008338216", 
          "symbol" : key, 
          "buy_sell" : "B", 
          "quantity" : 1, 
          # refer to last element in pricesList for the key
          "price" : currentPricesList[key][-1]/100,
          }, 
        "ref" : ""
        }
    ws.send(json.dumps(order))

def sell_stocks(key, currentPricesList):
    order = {
        "topic" : "api:join", 
        "event" : "order", 
        "payload" : {
            "phone_no" : "8008338216", 
            "symbol" : key, 
            "buy_sell" : "S", 
            "quantity" : 1, 
            "price" : currentPricesList[key][0]/100,
            }, 
          "ref" : ""
        }
    ws.send(json.dumps(order))

def calculateMovingAverage(pricesList, numberOfPrices, alpha=0.1): 
    movingAverageList = {key: [] for key in tickers}

    for key in tickers:
        prices = [float(price) for price in pricesList[key]]
        ema = [prices[0]]  # Initialize with the first price

        for i in range(1, len(prices)):
            ema.append(alpha * prices[i] + (1 - alpha) * ema[-1])

        movingAverageList[key] = ema

    # Calculate sell price
    sellingPricesList = {key: [movingAverageList[key][-1]] for key in tickers}

    return sellingPricesList


def executeStrategy(pricesList, tickers):
    moneyPosition = 100000
    i=10
    # deal in the stock market until moneyPosition is above 5,00,000 and i>0
    # by keeping a stop value on moneyPosition, I prevent from excessive loss
    while moneyPosition > 500000 and i>0:
        i=i-1
        changeList = {key : [] for key in tickers}
        for key in pricesList:
            for i in range(1, numberOfPrices):
                changeList[key].append(float(pricesList[key][i]) - float(pricesList[key][i-1]))

        # calculate percentage change for each ticker price
        for key in changeList:
            for i in range(len(changeList[key])):
                changeList[key][i] = changeList[key][i]/float(pricesList[key][i])
        
        combinedChangeList = []
        for key in changeList:
            combinedChangeList += changeList[key]

        # get 90th percentile
        combinedChangeList.sort()
        percentile90 = combinedChangeList[int(len(combinedChangeList)*0.90)]
        tickerList = []
        for key in changeList:
            for i in range(len(changeList[key])):
                if changeList[key][i] >= percentile90:
                    tickerList.append(key) 
    
        tickerList = list(set(tickerList))

        # get current prices
        currentPricesList = getCurrentPrice(tickers)
        buyingPriceList = currentPricesList
        # append current price to pricesList
        for key in tickers:
            pricesList[key].append(currentPricesList[key][0])
        # buy stock in tickerList at current price
        for key in tickerList:
            moneyPosition -= currentPricesList[key][0]
            buyingPriceList[key] = [currentPricesList[key][0]]
            buy_stocks(key, currentPricesList)
        
        import time
        # wait for 1 minute
        time.sleep(1*60)

        # get current prices
        currentPricesList = getCurrentPrice(tickerList)
        # append current price to pricesList
        for key in tickerList:
            pricesList[key].append(currentPricesList[key][0])

        # use moving average to determine sell price, giving higher weightage to recent prices
        sellingPricesList = calculateMovingAverage(pricesList, numberOfPrices)  
            
        for key in tickerList:
            if sellingPricesList[key][0] > currentPricesList[key][0]:
                moneyPosition += sellingPricesList[key][0]
                sell_stocks(key, currentPricesList)

# load tickers from file ind_nifty50list.csv
tickers = ["ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL"]
    
payload = create_payload(tickers)
print("1. Subscribing to tickers")
ws.send(json.dumps(payload))
print("2. Subscribed to tickers")

pricesList = {key : [] for key in tickers}
numberOfPrices = 300
while True:
  data = json.loads(ws.recv())
  print(data)
  p = data['payload']
  price = p[2]
  symbol = p[0]['symbol']
  # ensure only 300 prices are stored for each ticker
  if len(pricesList[symbol]) < numberOfPrices:
      pricesList[symbol].append(price)
  # check if all tickers have 300 prices, then break
  if all(len(pricesList[key]) >= numberOfPrices for key in tickers):
      break
  
# write to json file
with open('prices1.json', 'w') as f:
    json.dump(pricesList, f)
# write prices to file

executeStrategy(pricesList, tickers)
