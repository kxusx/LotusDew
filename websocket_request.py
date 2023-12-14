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
# with open('prices.csv', 'w') as f:
#     for key in pricesList:
#         # convert prices to string
#         pricesList[key] = [str(i) for i in pricesList[key]]
#         # f.write(key + ',' + ','.join(string(pricesList[key])) + '\n')

# calculate the change in price for each ticker
changeList = {key : [] for key in tickers}
for key in pricesList:
    for i in range(1, numberOfPrices):
        changeList[key].append(float(pricesList[key][i]) - float(pricesList[key][i-1]))

# calculate percentage change for each ticker
for key in changeList:
    for i in range(len(changeList[key])):
        changeList[key][i] = changeList[key][i]/float(pricesList[key][i])
# select tickers who are above 95th percentile in percentage change
        
combinedChangeList = []
for key in changeList:
    combinedChangeList += changeList[key]

# get 95th percentile
combinedChangeList.sort()
percentile95 = combinedChangeList[int(len(combinedChangeList)*0.90)]
# get tickers above 95th percentile
tickerList = []
for key in changeList:
    for i in range(len(changeList[key])):
      if changeList[key][i] >= percentile95:
        tickerList.append(key) 
# remove duplicates
tickerList = list(set(tickerList))

print(tickerList)



moneyPosition = 100000
# deal in the stock market until moneyPosition is 0

while moneyPosition > 0:
  # get current prices
  currentPricesList = getCurrentPrice(tickerList)
  buyingPriceList = currentPricesList
  # append current price to pricesList
  for key in tickerList:
      pricesList[key].append(currentPricesList[key][0])
      moneyPosition -= currentPricesList[key][0]
  # buy stock at current price
  for key in tickerList:
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

  import time
  # wait for 1 minute
  time.sleep(1*60)

  # get current prices
  currentPricesList = getCurrentPrice(tickerList)
  # append current price to pricesList
  for key in tickerList:
      pricesList[key].append(currentPricesList[key][0])

  # use moving average along with current price to determine sell price
  movingAverageList = {key : [] for key in tickerList}
  for key in tickerList:
      for i in range(1, numberOfPrices):
          movingAverageList[key].append(float(pricesList[key][i]) - float(pricesList[key][i-1]))
  # calculate sell price
  sellingPricesList = {key : [] for key in tickerList}
  for key in movingAverageList:
      temp = sum(movingAverageList[key])/len(movingAverageList[key])
      sellingPricesList[key] = [temp]

      
  for key in tickerList:
      if sellingPricesList[key][0] > currentPricesList[key][0]:
        moneyPosition += sellingPricesList[key][0]
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



  