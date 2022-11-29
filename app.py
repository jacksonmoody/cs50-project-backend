from flask import Flask, jsonify, request, send_file
from flask_apscheduler import APScheduler
import requests
import os.path
import time

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

@app.before_first_request
def init_scheduler():
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='nytapi', func=nytapi, trigger='interval', seconds=30)

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}

nyt_result = {}

def nytapi():
    global nyt_result
    response = requests.get("https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD")
    response = response.json()
    nyt_result = response
    print(nyt_result)

@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result
        })   