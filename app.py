from flask import Flask, jsonify, request, send_file
from flask_apscheduler import APScheduler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import os.path
import time

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

@app.before_first_request
def init_scheduler():
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='nytapi', func=nytapi, trigger='interval', seconds=30)

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}

nyt_result = {}
youtube_result = {}

def nytapi():
    global nyt_result
    response = requests.get("https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD")
    response = response.json()
    nyt_result = response

def youtubeapi():
    global youtube_result
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google-credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('youtube', 'v3', credentials=creds)
        request = service.search().list(
            part="snippet",
            maxResults=1,
            q="Test",
            regionCode="US"
        )
        response = request.execute()
        title = response['items'][0]['snippet']['title']
        description = response['items'][0]['snippet']['description']
        thumbnail = response['items'][0]['snippet']['thumbnails']['high']['url']
        youtube_result = {'title': title, 'description': description, 'thumbnail': thumbnail}

    except:
        print("Request failed")

@app.route("/nytapi")
def nytapi():
    return jsonify({
        "nyt_api": nyt_result
        })   

@app.route("/youtubeapi")
def youtubeapi():
    return jsonify({
        "youtube_api": youtube_result
        })   