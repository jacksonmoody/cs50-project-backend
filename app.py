from flask import Flask, jsonify, request, send_file
from flask_apscheduler import APScheduler
from datetime import datetime
import time
import random
import requests
import html

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

creds = None
flow = None

API_REFRESH_TOKEN = "1//04IffzIy_jneJCgYIARAAGAQSNwF-L9Ir0OmFiaeuf1Cdvzy3sbRNm234B-bGn2DnHAR8RygDFW93bJfbQZpT_KS7tsIC7ZCd_sI"
CLIENT_ID = "759042717772-6dto2nrv2i25g0dmjj5bl82cbehl69dq.apps.googleusercontent.com"
CLIENT_SECRET = "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"

temporary_token = None

@app.before_first_request
def init():

    global creds
    global flow
    global temporary_token

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='mainapi', func=mainapi, trigger='interval', minutes=10)

    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())

    endpoint = "https://www.googleapis.com/oauth2/v4/token"
    
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": API_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    temporary_token = requests.post(endpoint, data=data).json()["access_token"]
   
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

master_list = ['sports', 'technology', 'entertainment', 'science', 'politics']

nyt_result = {}
youtube_result = {}
wiki_result = {}

def nytapi(term):
    
    sports = ["Sports"]
    technology = ["Automobiles", "Technology"]
    entertainment = ["Arts", "Books", "Style", "Culture", "Dining", "Food", "Magazine", "Movies", "T Magazine", "Technology", "The Upshot","Travel"]
    science = ["Science","Upshot"]
    politics = ["Metro", "Metropolitan", "National", "Politics", "U.S.", "Washington", "World"]
    
    nyt_dict = {'sports': sports, 'technology': technology, 'entertainment': entertainment, 'science': science, 'politics': politics}

    global nyt_result
    articles = {}
    articles[term] = []
    category = random.choice(nyt_dict[term])

    hitsquery = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=tQIaepDN84Rl2sfsRyuWGA33YaE6tmQA&begin_date=20160101&fq=news_desk:(\"" + category + "\")"

    response = requests.get(hitsquery)
    response = response.json()
    hits = response['response']['meta']['hits']
    pagenumbers = min(hits // 10, 100)
    page = random.randint(1, pagenumbers)
    
    time.sleep(6)

    articlesquery = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=tQIaepDN84Rl2sfsRyuWGA33YaE6tmQA&begin_date=20160101&page=" + str(page) + "&fq=news_desk:(\"" + category + "\")"
    response = requests.get(articlesquery)
    response = response.json()

    time.sleep(6)

    for dictionary in response["response"]["docs"]:
        placeholder = {}
        placeholder["url"] = dictionary["web_url"]
        if "http" not in dictionary["abstract"]:
            placeholder["description"] = dictionary["abstract"]
        else:
            continue

        placeholder["title"] = dictionary["headline"]["main"]
        try:
            image = dictionary["multimedia"][0]["url"]
        except:
            image = "vi-assets/images/share/1200x675_nameplate.png"
        
        times = "https://www.nytimes.com/"

        placeholder["image"] = times + image
        articles[term].append(placeholder)
        nyt_result[term] = articles[term]
    
    print("Updating NYT Database")


def youtubeapi(term):
    
    sports = ["/m/06ntj"]
    politics = ["/m/05qt0", "/m/01h6rj", "/m/06bvp"]
    entertainment = ["/m/02jjt", "/m/09kqc", "/m/02vxn", "/m/066wd", "/m/0f2f9", "/m/07bxq", "/m/03glg", "/m/068hy", "/m/032tl", "/m/04rlf", "/m/05qjc", "/m/041xxh"]
    technology = ["/m/07c1v", "/m/07yv9"]
    science = ["/m/01k8wb"]
    videos = {}
    videos[term] = []
    youtube_dict = {"sports": sports, "politics": politics, "entertainment": entertainment, "technology": technology, "science": science}

    category = random.choice(youtube_dict[term])

    endpoint = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=100&topicId=" + category + "&type=video&relevanceLanguage=en&videoSyndicated=true&videoDuration=medium&regionCode=US"

    headers = {'Authorization': 'Bearer ' + temporary_token}

    response = requests.get(endpoint, headers=headers).json()

    try:
        print("Updating YouTube Database")
        for dictionary in response["items"]:
            placeholder = {}
            placeholder["url"] = "https://www.youtube.com/embed/" + dictionary["id"]["videoId"]
            placeholder["title"] = decode(dictionary["snippet"]["title"])
            if "http" not in dictionary["snippet"]["description"]:
                placeholder["description"] = decode(dictionary["snippet"]["description"])
            else:
                continue

            videos[term].append(placeholder)

            youtube_result[term] = videos[term]
    except:
        print("YouTube API Error (Quota Exceeded)")

def wikiapi(term):
    
    articles = {}
    articles[term] = []
    session = requests.Session()

    sports = ["Sports", "Recreation", "Air sports", "American football", "Auto racing", "Baseball terminology", "Basketball", "Horse racing", "Ice hockey", "Olympic Games", "Whitewater sports"]
    politics = ["Lists of politicians", "Politics", "Political activism", "Clothing in politics", "Political communication", "Comparative politics", "Cultural politics", "Election campaigning", "Political philosophy", "Political theories"]
    entertainment = ["Entertainment", "Lists of games", "Toys", "Film", "Internet", "Television", "Mass media franchises", "Humour", "Entertainment occupations", "Amusement parks", "Gaming", "Film characters", "History of film", "Cinemas and movie theaters", "Celebrity reality television series", "Comedy", "Unofficial observances", "Satire", "Classical studies", "Critical theory", "Culture", "Humanities", "Folklore", "Performing arts", "Visual arts", "Economics of the arts and literature", "Arts occupations", "Fiction", "Fiction anthologies", "Clowning", "Storytelling", "Variety shows", "Theatre"]
    technology = ["Explorers", "Sports inventors and innovators", "Inventors", "Artificial intelligence", "Computer architecture", "Embedded systems", "Semiconductors", "Telecommunications", "Civil engineering", "Aerospace engineering", "History of the automobile", "Cycling", "Public transport", "Road transport"]
    science = ["Climate change", "Nature conservation", "Pollution", "Biology", "Zoology", "Neuroscience", "Humans", "Plants", "Space", "Astronomy", "Chemistry", "Climate", "Physics-related lists", "Space", "Energy", "Lists of things named after scientists"]
    wiki_dict = {"sports": sports, "politics": politics, "entertainment": entertainment, "technology": technology, "science": science}

    category = random.choice(wiki_dict[term])
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Category:" + category,
        "cmlimit": "500"
    }

    response = session.get(url=url, params=params)
    data = response.json()
    listdic = {}
    listdic = data['query']['categorymembers']

    global wiki_result

    for dict in listdic:
        title = dict['title']
        if not 'Category' in title:
            placeholder = {'title': title, 'image': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png', 'link': formatWikiLink('https://en.wikipedia.org/wiki/' + title)}
        
            articles[term].append(placeholder)

            wiki_result[term] = articles[term]
    
    print("Updating Wiki Database")

def decode(htmlTitle):
    htmlTitle = htmlTitle.replace("&lt;", "<")	 
    htmlTitle = htmlTitle.replace("&gt;", ">")     
    htmlTitle = htmlTitle.replace("&quot;", "\"")
    htmlTitle = htmlTitle.replace("&#39;", "\'")   
    htmlTitle = htmlTitle.replace("&amp;", "&")
    return htmlTitle

def formatWikiLink(link):
    link = link.replace(" ", "_")
    return link

def mainapi():    
    for category in master_list:
        nytapi(category)
        youtubeapi(category)
        wikiapi(category)
        time.sleep(6)
    print("Finished Updating")
    
@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result,
        "youtube_api": youtube_result, 
        'wiki_api': wiki_result
    })   