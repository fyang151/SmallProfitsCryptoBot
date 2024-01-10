import time 
from datetime import datetime
from colorama import Fore, Back, Style
import math
import requests
import urllib.parse
import hashlib
import hmac
import base64

# terms:
# Beaver: an order to either buy or sell
# Fred: a unit of BTC

# API Key and Secret for Kraken account
apikey = PLACEHOLDER
apisec = PLACEHOLDER
apiurl = "https://api.kraken.com"

# Function to generate Kraken API signature
def get_kraken_signature(urlpath, data, secret):
    # Encode the data for the POST request
    postdata = urllib.parse.urlencode(data)
    
    # Concatenate the nonce and encoded data, then hash the result
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    # Use HMAC-SHA512 for generating signature
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())

    # Convert the signature to a string and return
    return sigdigest.decode()

# Function to make a Kraken API request
def kraken_request(url_path, data, api_key, api_sec):
    # Generate headers with API key and signature
    headers = {"API-KEY": api_key, "API-SIGN": get_kraken_signature(url_path, data, api_sec)}

    # Make a POST request to the Kraken API
    resp = requests.post((apiurl + url_path), headers=headers, data=data)
    return resp

def buy():
    resp = kraken_request('/0/private/AddOrder', {
    "nonce": str(int(1000 * time.time())),
    "ordertype": "market",
    "type": "buy",
    "volume": 0.0001,
    "pair": "BTCCAD"
    }, apikey, apisec)
    
    print(Fore.RED + f"{str(resp.json())}")
    print(Style.RESET_ALL)

def sell():
    resp = kraken_request('/0/private/AddOrder', {
    "nonce": str(int(1000 * time.time())),
    "ordertype": "market",
    "type": "sell",
    "volume": 0.0001,
    "pair": "BTCCAD"
    }, apikey, apisec)

    print(Fore.GREEN + f"{str(resp.json())}")
    print(Style.RESET_ALL)

balance = kraken_request("/0/private/Balance", {
    "nonce": str(int(1000 * time.time()))
}, apikey, apisec)
print(balance.json())

cryptoDict = {}

currentBTC = float(balance.json()['result']['XXBT'])
myMoney = float(balance.json()['result']['ZCAD'])
safety = 0

print(f"my CAD: {myMoney}")

starter_priceBTC = float(requests.get("https://api.kraken.com/0/public/Ticker?pair=BTCCAD").json()['result']['XXBTZCAD']['c'][0])
fredStarter = starter_priceBTC * 0.0001
starter = 1

for singleBeaver in range (int(math.floor(currentBTC * 10000))):
    cryptoDict[f"starter{starter}"] = (fredStarter, "selling", "VIRGIN")
    starter += 1

    #leftover btc is negligible

while True:

    current_priceBTC = float(requests.get("https://api.kraken.com/0/public/Ticker?pair=BTCCAD").json()['result']['XXBTZCAD']['c'][0])
    fred = round(current_priceBTC * 0.0001, 6)
    print(f"1 Fred of BTC: {fred}")

    activity = False
    soldThisStep = []

    expectedValueWithFailSafe = round(myMoney - (2 * fred), 5)
    expectedValue = round(myMoney - fred, 5)
    margin = 0.0100520676/(fred - 1.0026)

    neededBuyMoney = 0
    potentiallyNewBeaver = [fred, "selling", "VIRGIN"]

    if cryptoDict:

        lowest = float(next(iter(cryptoDict.values()))[0])
        
        for beaver in cryptoDict.copy():

            thisBeaver = cryptoDict[beaver]

            if thisBeaver[0] < lowest:
                lowest = thisBeaver[0]

            if (fred / (1.0026 + margin)) > float(thisBeaver[0]) and thisBeaver[1] == "selling":
                sell()

                if thisBeaver in soldThisStep:
                    del cryptoDict[beaver]
                else:
                    soldThisStep.append(thisBeaver)
                    cryptoDict[beaver] = [fred, "buying", "promiscuous"]
            
                activity = True
                myMoney += float(thisBeaver[0])
                safety += ((fred / (1.0026 + margin)) - float(thisBeaver[0]))
            
            elif thisBeaver[1] == "buying":

                neededBuyMoney += thisBeaver[0]

                #i will choose to be pretty lax with the buy orders (not including margins) because i want to buy and sell as quick as possible and the profits lie within the sells

                if (fred * 1.0026) < float(thisBeaver[0]) and expectedValueWithFailSafe > 0:
                    buy()

                    cryptoDict[beaver] = [fred, "selling", "promiscuous"]

                    activity = True
                    myMoney -= (fred * 1.0026)
        
        #emergency buy: different from the new beaver buy below because this happens when the price of crypto goes REAL LOW and we HAVENT BOUGHT YET!!!!!.... i should think of another solution to this.
        #can only do this once though; if this happens again we are doomed.
        if fred < (lowest / 1.0026) and activity == False and expectedValue > 0:
            buy()

            now = str(datetime.now())
            cryptoDict[now] = potentiallyNewBeaver

            activity = True
            myMoney -= fred
    
    leftOverIfBuy = myMoney - neededBuyMoney

    if activity == False and not(potentiallyNewBeaver in cryptoDict.values()) and fred < leftOverIfBuy and expectedValueWithFailSafe > 0:
        buy()
    
        now = str(datetime.now())
        cryptoDict[now] = potentiallyNewBeaver

        activity = True
        myMoney -= fred
    
    myMoney = round(myMoney, 5)
    
    # print(f"Needed Buy: {neededBuyMoney}")
    # print(f"hmm....: {expectedValueWithFailSafe}")
    # print(f"CAD after trade: {expectedValue}")
    print(f"Money We Shall Trade With: {myMoney}")
    print(f"Our Beaver Portfolio: {cryptoDict}")
    print(Fore.BLUE + f"CASH SAVINGS: {safety}")
    print(Style.RESET_ALL)

    time.sleep(1)

#win

