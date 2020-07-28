# coding: UTF-8
import RPi.GPIO as GPIO
import time
import datetime
import requests
import os
import sys
sys.path.append("..")
import environment
sys.path.append("../DHT11_Python")
import dht11
import schedule

# gitignoreしたファイルで環境変数（slack webhooksのURLとID）を生成
environment.writeSlackIncomingUrl()
environment.writeSlackUserId()

# initialize GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

# read data using pin 14
instance = dht11.DHT11(pin=14)

# slack-incoming-hookds url
url = os.environ["SLACK_INCOMING_URL"]
userId = os.environ["SLACK_USER_ID"]
maxTemp = 30
minTemp = 25
maxHumid = 85
minHumid = 60

lastValidMessage = "no record"
lastPostTime = None

def getTemperatureAndHumidity(event):
    result = instance.read()
    now = datetime.datetime.now()
    convertedNow = now.strftime("%Y/%m/%d %H:%M")
    print(event)
    if result.is_valid():
        print("Last valid input: " + str(convertedNow))
        print("Temperature: %-3.1f C" % result.temperature)
        print("Humidity: %-3.1f %%" % result.humidity)
        global lastValidMessage
        lastValidMessage = "{time}\n気温：{temp}度\n湿度：{humid}%".format(time = convertedNow,temp = result.temperature, humid = result.humidity)
        return result, lastValidMessage
    else:
        print("invalid input: " + str(convertedNow))

def periodicalRequest(tempAndHumidMessage):
    payload = {"text": "30分に一度の定時投稿。現在のはるきちのおうち\n\n{1}".format(userId, tempAndHumidMessage)}
    response = requests.post(url, json=payload)
    print(response.status_code, response.text)
    
def anomalyDetectRequest(result, tempAndHumidMessage):
    if result.temperature <= minTemp:
        payload = {"text": "<@{0}> はるきちのおうちが寒い！エアコンをオフにしてください！！\n\n{1}".format(userId, tempAndHumidMessage)}

    if result.temperature >= maxTemp:
        payload = {"text": "<@{0}> はるきちのおうちが暑い！エアコンを入れてください！！\n\n{1}".format(userId, tempAndHumidMessage)}
    
    if result.humidity <= minHumid:
        payload = {"text": "<@{0}> はるきちのおうちが乾燥してる！お水を上げてください！！\n\n{1}".format(userId, tempAndHumidMessage)}

    if result.humidity >= maxHumid:
        payload = {"text": "<@{0}> はるきちのおうちが湿気てる！！飼い主が不快な思いをしているかもしれません。\n\n{1}".format(userId, tempAndHumidMessage)}
    
    if "payload" in locals():

        #def elapsedTimeFromLastPost():
        now = datetime.datetime.now()
        global lastPostTime
        
        if lastPostTime != None:
            elapsedTime = now - lastPostTime
            print(elapsedTime)

            if elapsedTime < datetime.timedelta(minutes=15):
                return
    
        response = requests.post(url, json=payload)
        print(response.status_code, response.text)
        
        # 連続投稿を避けるために最後のpostを記録する
        lastPostTime = datetime.datetime.now()

def periodicalLogging():
    result = getTemperatureAndHumidity("定時実行")
    periodicalRequest(lastValidMessage)
        
def anormalLogging():
    result = getTemperatureAndHumidity("")
    if result != None:
        anomalyDetectRequest(result[0], result[1])
            
schedule.every(1).minutes.do(anormalLogging)
schedule.every().hour.at("00:00").do(periodicalLogging)
schedule.every().hour.at("30:00").do(periodicalLogging)


while True:
    schedule.run_pending()
    time.sleep(1)
