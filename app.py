from flask import Flask, jsonify, request, send_file
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

app = Flask(__name__)

sched = BlockingScheduler()

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}

youtube_result = {}
nyt_result = {}

@sched.scheduled_job('interval', minutes=1)
def timed_job():
    nyt_result = nytapi()
    youtube_result = youtubeapi()

sched.start()

def youtubeapi():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret2.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('youtube', 'v3', credentials=creds)
        request = service.search().list(
            part="snippet",
            maxResults=1,
            q="Jiminy Cricket",
            regionCode="US"
        )
        response = request.execute()
        title = response['items'][0]['snippet']['title']
        description = response['items'][0]['snippet']['description']
        thumbnail = response['items'][0]['snippet']['thumbnails']['high']['url']
        youtube_result = {'title': title, 'description': description, 'thumbnail': thumbnail}
        return youtube_result

    except:
        print("Failed")

def nytapi():
    response = requests.get("https://api.nytimes.com/svc/mostpopular/v2/viewed/7.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD")
    response = response.json()
    nyt_result = response
    return nyt_result

@app.route("/")
def api():
    return jsonify({
        "youtube_api": youtube_result,
        "nyt_api": nyt_result
        })