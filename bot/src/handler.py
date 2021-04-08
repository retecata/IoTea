import json
import os
import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../vendored"))

import requests

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)
SEND_MESSAGE_URL = "/sendMessage"

START_COMMAND = "/start"
STATUS_COMMAND = "/status"
PHOTO_COMMAND = "/photo"

DEVICE_ID = ""  # Enter your plantId here e.g. "yoshi"
WHITELIST = []  # Enter the list of Telegram IDs to whitelist here as comma separated strings e.g. ["123", "456"]


def handle_message(event, _):
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])
        chat_id = data["message"]["chat"]["id"]
        user_id = str(data["message"]["from"]["id"])

        if is_user_verified(user_id):
            if message == START_COMMAND:
                handle_start(chat_id)

            if message == STATUS_COMMAND:
                handle_status(chat_id)

            if message == PHOTO_COMMAND:
                handle_photo(chat_id)
        else:
            handle_invalid_user(chat_id)

    except Exception as e:
        print(e)

    return {"statusCode": 200}


def handle_start(chat_id):
    response = "Hello"
    data = {"text": response.encode("utf8"), "chat_id": chat_id}
    url = BASE_URL + SEND_MESSAGE_URL
    requests.post(url, data)


def handle_status(chat_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('iotea_last_vitals')

    res = table.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key('plantID').eq(DEVICE_ID)
    )

    item = res['Items'][0]
    humidity = item['humidity']
    temp = item['temperature']
    moisture = item['moisturePer']
    time = datetime.utcfromtimestamp(timestamp_to_seconds(item['ts']))

    response = "Hello!\n" \
               "My last checkup was at {time}\n" \
               "Moisture Level: {moisture}%\n" \
               "Temperature: {temp}\N{DEGREE SIGN}C\n" \
               "Humidity: {humidity}%".format(
                    time=time,
                    moisture=moisture,
                    temp=temp,
                    humidity=humidity
                )

    data = {"text": response.encode("utf8"), "chat_id": chat_id}
    url = BASE_URL + SEND_MESSAGE_URL
    requests.post(url, data)


def handle_photo(chat_id):
    response = "Sending photo of plant..."
    data = {"text": response.encode("utf8"), "chat_id": chat_id}
    url = BASE_URL + SEND_MESSAGE_URL
    requests.post(url, data)


def handle_invalid_user(chat_id):
    response = "Sorry, you are not a verified user!"
    data = {"text": response.encode("utf8"), "chat_id": chat_id}
    url = BASE_URL + SEND_MESSAGE_URL
    requests.post(url, data)


def is_user_verified(user_id):
    return user_id in WHITELIST


def timestamp_to_seconds(ts):
    return ts / 1000