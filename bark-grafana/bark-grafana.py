from flask import Flask, request, jsonify
from urllib.parse import quote

from dateutil import parser
import pytz

import hashlib
import requests
import json

import os
import sys
from loguru import logger
from cachetools import TTLCache

logger.level("DEBUG")
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webhook-app.log")
logger.add(log_file_path, rotation="10 MB", retention="7 days", compression="zip", encoding="utf-8")
logger.add(sys.stdout)

cache = TTLCache(maxsize=100000, ttl=10)


app = Flask(__name__)

def convert_tz(dt_str):
    dt = parser.parse(dt_str)
    dt_sh = dt.astimezone(pytz.timezone('Asia/Shanghai'))
    return dt_sh.strftime('%Y-%m-%d %H:%M:%S%Z')


def extract_title_body(alert):
    title = f'[{alert["status"].upper()}] {alert["labels"]["alertname"]}'
    start_time = convert_tz(alert["startsAt"])
    end_time = convert_tz(alert["endsAt"])

    if alert["status"].lower() == "resolved":
        body = f'starts at: {start_time}, ends at: {end_time}'
    else:
        body = f'starts at: {start_time}'

    if "summary" in alert["annotations"]:
        title = f'{title}: {alert["annotations"]["summary"]}'
    if "description" in alert["annotations"]:
        body = f'{alert["annotations"]["description"]} {body}'
    return title, body

def call_target(target_host, token, title, body):
    target_url = f"http://{target_host}/{token}/{quote(title)}/{quote(body)}"
    logger.info(f"target url {target_url}")
    response = requests.request(method="GET", url=target_url)
    logger.info(f"response from remote server {response}")
    return response


def mock_response(code=200, message=""):
    response = requests.models.Response()
    response.status_code = code
    response._content = message.encode('utf-8')
    return response


def is_in_cache(title, body):
    key = hashlib.sha256(f"{title} {body}".encode('utf-8')).hexdigest()
    logger.debug(f"cache key {key}")
    if key in cache:
        logger.debug("key in cache")
        return True
    else:
        logger.debug("key not in cache, put it in cache")
        cache[key] = 1
        return False


@app.route("/forward/<target_host>/<token>", methods=["GET", "POST"])
def forward_request(target_host, token):
    logger.info(f"target host {target_host}, token {token}, Full URL: {request.url}, Base URL: {request.base_url}, Path: {request.path}, Hostname: {request.host}, Scheme: {request.scheme}, Method: {request.method}")
    data = request.get_data()
    logger.debug(f"data {data}")
    try:
        data_json = json.loads(data)
        alerts = data_json["alerts"]
        for alert in alerts:
            title, body = extract_title_body(alert)
            if is_in_cache(title, body):
                logger.info(f"title {title} body {body} already in cache, alert will not be sent.")
                response = mock_response(code=200, message="repeat alert detected, alert will not be sent.")
            else:
                logger.info(f"title {title} body {body} not in cache, proceed with alert.")
                response = call_target(target_host, token, title, body)
    except Exception as e:
        logger.error(f"exception occurred: {e}, data in request {data}")
        title = f"gunicorn exception"
        body = f"alert not delivered, gunicorn exception {e}"
        response = call_target(target_host, token, title, body)

    response_data = response.content
    response_status = response.status_code

    return jsonify({
        "status": response_status,
        "data": response_data.decode("utf-8")
    })

# if __name__ == '__main__':
#     # app.run(host='0.0.0.0', port=8088)
#     from waitress import serve
#     serve(app, host="0.0.0.0", port=8088)

