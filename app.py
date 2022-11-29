from flask import Flask, jsonify, request, send_file
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import os.path

app = Flask(__name__)

sched = BlockingScheduler()

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}

nyt_result = {}

def nytapi():
    response = requests.get("https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD")
    response = response.json()
    nyt_result = response
    return nyt_result

@sched.scheduled_job('interval', minutes=1)
def timed_job():
    nyt_result = nytapi()

sched.start()

@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result
        })