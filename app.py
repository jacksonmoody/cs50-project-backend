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

API_REFRESH_TOKEN = "1//04ZqF2jVjRIvoCgYIARAAGAQSNwF-L9IrzyS1RQsfsxbkX_05N_7aS3r14QzVRkugCJLQ463Q-IpMEFpgUx3AXKYp3B-M8HElS6I"

temporary_token = None

@app.before_first_request
def init():

    global creds
    global flow
    global temporary_token

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='nytapi', func=nytapi, trigger='interval', seconds=30)
    scheduler.add_job(id='youtubeapi', func=youtubeapi, trigger='interval', seconds=30)

    endpoint = "https://www.googleapis.com/oauth2/v4/token"
    
    data = {
        "client_id": "403342113138-jem2g3abeedtastc3vnc91kfd8bppl71.apps.googleusercontent.com",
        "client_secret": "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",
        "refresh_token": API_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    temporary_token = requests.post(endpoint, data=data).json()["access_token"]
   
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

nyt_result = []

wiki_result = []

youtube_result = {}

def nytapi():
    sports = ["Adventure Sports", "Sports"]

    art = ["Arts & Leisure", "Arts", "Books", "Fashion & Style", "Fashion", "Home & Garden", "Style", "Sunday Styles", "The Arts"]

    technology = ["Automobiles", "Cars", "Circuits", "Flight", "Museums", "Personal Tech", "Wireless Living"]

    business = ["Business Day", "Business", "DealBook", "Entrepreneurs", "Financial", "Jobs", "Personal Investing", "Retail", "Small Business", "Sunday Business", "The Business of Green", "Wealth", "Working", "Workplace", "Your Money"]

    entertainment = ["Culture", "Dining", "Escapes", "Food", "Global Home", "Home", "Magazine", "Media", "Movies", "T Magazine", "T Style", "Technology", "Television", "The Upshot", "The Weekend", "The Year in Pictures", "Theater", "Travel"]

    science = ["Education", "Energy", "Environment", "Science", "The Natural World", "Upshot", "Vacation", "Weather"]

    health = ["Health & Fitness", "Health", "Men's Health", "Women's Health"]

    politics = ["Metro", "Metropolitan", "National", "Politics", "U.S.", "Washington", "World"]

    master_list = [sports, art, technology, business, entertainment, science, health, politics]

    print("Updating NYT Database")

    global nyt_result 

    category = random.choice(random.choice(master_list))

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

    global youtube_result

    print("Updating Youtube Database")

    endpoint = "https://www.googleapis.com/youtube/v3/search"

    headers = {'Authorization': 'Bearer ' + temporary_token}

    response = requests.get(endpoint, headers=headers).json()

    print(response)

    youtube_result = response

def wikiapi():
    session = requests.Session()

    sportsW = ["Sports", "Recreation", "Air sports", "American football", "Auto racing", "Baseball terminology", "Basketball", "Horse racing", "Ice hockey", "Olympic Games", "Whitewater sports"]

    politicsW = ["Lists of politicians", "Politics", "Political activism", "Clothing in politics", "Political communication", "Comparative politics", "Cultural politics", "Election campaigning", "Political philosophy", "Political theories"]

    businessW = ["Chief executive officers", "Billionaires", "Real estate", "Finance", "Business", "Paradoxes in economics", "Money", "Industries (economics)", "Financial markets", "Investment", "Business economics", "Business ethics", "Business economics", "Business terms", "Sports business"]

    entertainmentW = ["Entertainment", "Lists of games", "Toys", "Film", "Internet", "Television", "Mass media franchises", "Humour", "Entertainment occupations", "Amusement parks", "Gaming", "Film characters", "History of film", "Cinemas and movie theaters", "Celebrity reality television series", "Comedy", "Unofficial observances", "Satire"]

    technologyW = ["Explorers", "Sports inventors and innovators", "Inventors", "Artificial intelligence", "Computer architecture", "Embedded systems", "Semiconductors", "Telecommunications", "Civil engineering", "Aerospace engineering", "History of the automobile", "Cycling", "Public transport", "Road transport"]

    scienceW = ["Climate change", "Nature conservation", "Pollution", "Biology", "Zoology", "Neuroscience", "Humans", "Plants", "Space", "Astronomy", "Chemistry", "Climate", "Physics-related lists", "Space", "Energy", "Lists of things named after scientists"]

    healthW = ["Nutrition", "Hygiene", "Positive psychology", "Public health", "Medicine", "Dentistry", "Veterinary medicine"]

    artsW = ["Classical studies", "Critical theory", "Culture", "Humanities", "Folklore", "Performing arts", "Visual arts", "Economics of the arts and literature", "Arts occupations", "Fiction", "Fiction anthologies", "Clowning", "Storytelling", "Variety shows", "Theatre"]

    masterlistW = [sportsW, politicsW, businessW, entertainmentW, technologyW, scienceW, healthW, artsW]
    var = random.choice(random.choice(masterlistW))

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Category:" + var,
        "cmlimit": "500"
    }

    response = session.get(url=url, params=params)
    data = response.json()
    listdic = data['query']['categorymembers']
    global wiki_result
    for dict in listdic:
        title = dict['title']
        if not 'Category' in title:
            wiki_result.append(title)

@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result,
        "youtube_api": youtube_result, 
        'wiki_api': wiki_result
        })   