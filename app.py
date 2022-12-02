from flask import Flask, jsonify, request, send_file
from flask_apscheduler import APScheduler
import random
import requests
import os.path
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

creds = None
flow = None

@app.before_first_request
def init():

    global creds
    global flow

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='nytapi', func=nytapi, trigger='interval', seconds=30)

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

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

categories = {'sports', 'politics', 'business', 'entertainment', 'technology', 'science', 'health'}

sports = ["Adventure Sports", "Sports"]

art = ["Arts & Leisure", "Arts", "Books", "Fashion & Style", "Fashion", "Home & Garden", "Style", "Sunday Styles", "The Arts"]

technology = ["Automobiles", "Cars", "Circuits", "Flight", "Museums", "Personal Tech", "Wireless Living"]

business = ["Business Day", "Business", "DealBook", "Entrepreneurs", "Financial", "Jobs", "Personal Investing", "Retail", "Small Business", "Sunday Business", "The Business of Green", "Wealth", "Working", "Workplace", "Your Money"]

entertainment = ["Culture", "Dining", "Escapes", "Food", "Global Home", "Home", "Magazine", "Media", "Movies", "T Magazine", "T Style", "Technology", "Television", "The Upshot", "The Weekend", "The Year in Pictures", "Theater", "Travel"]

science = ["Education", "Energy", "Environment", "Science", "The Natural World", "Upshot", "Vacation", "Weather"]

health = ["Health & Fitness", "Health", "Men's Health", "Women's Health"]

politics = ["Metro", "Metropolitan", "National", "Politics", "U.S.", "Washington", "World"]

master_list = [sports, art, technology, business, entertainment, science, health, politics]

nyt_result = []

def nytapi():

    print("Updating NYT Database")

    global nyt_result

    num1 = random.randint(0, len(master_list) - 1)

    list1 = master_list[num1]

    num2 = random.randint(0, len(list1) - 1) 

    category = list1[num2]

    query = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD&fq=news_desk:(\"" + category + "\")"

    response = requests.get(query)
    response = response.json()

    for dictionary in response["response"]["docs"]:
        placeholder = {}
        placeholder["url"] = dictionary["web_url"]
        placeholder["description"] = dictionary["abstract"]
        placeholder["title"] = dictionary["headline"]["main"]
        try:
            image = dictionary["multimedia"][0]["url"]
        except: 
            image = "vi-assets/images/share/1200x675_nameplate.png"

        times = "https://www.nytimes.com/"

        placeholder["image"] = times + image
        nyt_result.append(placeholder)

def youtubeapi():
    try:
        service = build('youtube', 'v3', credentials=creds)
        request = service.videos().list(
            part="snippet,contentDetails,statistics",
            chart="mostPopular",
            regionCode="US"
        )
        response = request.execute()
        print(response)
    except:
        print("Request failed")

@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result
        })   