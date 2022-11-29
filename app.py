from flask import Flask, jsonify, request, send_file
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os.path
import time

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

nyt_result = {}

def nytapi():
    response = requests.get("https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD")
    response = response.json()
    nyt_result = response
    return nyt_result

@scheduler.task('interval', id='do_job_1', seconds=30, misfire_grace_time=900)
def timed_job():
    print("im running whoooo")
    nyt_result = nytapi()

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}