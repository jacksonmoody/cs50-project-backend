from flask import Flask, jsonify, request, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os.path

app = Flask(__name__)

sched = BackgroundScheduler(daemon=True)

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}

nyt_result = {}

def nytapi():
    response = requests.get("https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD")
    response = response.json()
    nyt_result = response
    return nyt_result
    
def timed_job():
    nyt_result = nytapi()

sched.add_job(timed_job, 'interval', seconds=5)

sched.start()

@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result
        })