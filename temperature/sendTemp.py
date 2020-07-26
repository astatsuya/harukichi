# coding: UTF-8
import RPi.GPIO as GPIO
import time
import datetime
import requests
import os
import sys
sys.path.append("../")
import environment
sys.path.append("../DHT11_Python")
import dht11

# gitignoreしたファイルで環境変数（webhooksのURL）を生成
environment.writeSlackIncomingUrl()

# initialize GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

# read data using pin 14
instance = dht11.DHT11(pin=14)

# slack-incoming-hookds url
url = os.environ["SLACK_INCOMING_URL"]
userId = "UTWME81C6"
count = 0

try:
    while True:
        result = instance.read()
        if result.is_valid():
            now = datetime.datetime.now()
            convertedNow = now.strftime("%Y/%m/%d %H:%M")
            
            print("Last valid input: " + str(convertedNow))

            print("Temperature: %-3.1f C" % result.temperature)
            print("Humidity: %-3.1f %%" % result.humidity)
            count += 1
            
            tempAndHumidMessage = "{time}\n気温：{temp}度\n湿度：{humid}%".format(time = convertedNow,temp = result.temperature, humid = result.humidity)
            
            payload = 0
            print(count)
            if count >= 2:                        
                # 定時投稿
                payload = {"text": "<@{0}> 30分に一度の定時投稿。現在のはるきちのおうち\n\n{1}".format(userId, tempAndHumidMessage)}
                response = requests.post(url, json=payload)
                count = 0
                print(response.status_code, response.text)
            else:
                # 温度変化検知
                if result.temperature <= 25.0:
                    payload = {"text": "<@{0}> はるきちのおうちが寒い！エアコンをオフにしてください！！\n\n{1}".format(userId, tempAndHumidMessage)}
                
                if result.temperature >= 30:
                    payload = {"text": "<@{0}> はるきちのおうちが暑い！エアコンを入れてください！！\n\n{1}".format(userId, tempAndHumidMessage)}
                    
                if result.humidity <= 60:
                    payload = {"text": "<@{0}> はるきちのおうちが乾燥してる！お水を上げてください！！\n\n{1}".format(userId, tempAndHumidMessage)}
                    
                if result.humidity >= 80:
                    payload = {"text": "<@{0}> はるきちのおうちが湿気てる！！飼い主が不快な思いをしているかもしれません。\n\n{1}".format(userId, tempAndHumidMessage)}
                
                if payload != 0:
                    response = requests.post(url, json=payload)
                    print(response.status_code, response.text)
        
        time.sleep(1 * 6)

except KeyboardInterrupt:
    print("Cleanup")
    GPIO.cleanup()