from flask import Flask, jsonify, request, send_file
from flask_apscheduler import APScheduler
from datetime import datetime
import random
import requests

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

creds = None
flow = None

API_REFRESH_TOKEN = "1//04YmRU7hieeP6CgYIARAAGAQSNwF-L9IrELl9AYMaRUsJpQUppUYF_GUTTK-3E116sW9lldGLthggNzCHFB13YmSAvxNciVkdReE"

temporary_token = None

@app.before_first_request
def init():

    global creds
    global flow
    global temporary_token

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='mainapi', func=mainapi, trigger='interval', minutes=5)

    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())

    endpoint = "https://www.googleapis.com/oauth2/v4/token"
    
    data = {
        "client_id": "403342113138-jem2g3abeedtastc3vnc91kfd8bppl71.apps.googleusercontent.com",
        "client_secret": "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",
        "refresh_token": API_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    temporary_token = requests.post(endpoint, data=data).json()["access_token"]
   
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

master_list = ['sports', 'art', 'technology', 'business', 'entertainment', 'science', 'politics']

nyt_result = {}
youtube_result = {}
wiki_result = {}

def nytapi(term):
    
    sports = ["Sports"]
    art = ["Arts", "Books", "Style"]
    technology = ["Automobiles", "Technology"]
    business = ["Business Day", "Business"]
    entertainment = ["Culture", "Dining", "Food", "Magazine", "Movies", "T Magazine", "Technology", "The Upshot","Travel"]
    science = ["Science","Upshot"]
    politics = ["Metro", "Metropolitan", "National", "Politics", "U.S.", "Washington", "World"]
    
    nyt_dict = {'sports': sports, 'art': art, 'technology': technology, 'business': business, 'entertainment': entertainment, 'science': science, 'politics': politics}

    global nyt_result
    articles = {}
    articles[term] = []
    category = random.choice(nyt_dict[term])

    hitsquery = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD&begin_date=20160101&fq=news_desk:(\"Sports\")"

    response = requests.get(hitsquery)
    print(response)
    if response != None or response != {}:
        response = response.json()
        hits = response['response']['meta']['hits']
        pagenumbers = min(hits // 10, 100)
        page = random.randint(1, pagenumbers)

    articlesquery = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=FgKjzYiiamFAfUJMbpPnqkn7u3ManknD&begin_date=20160101&page=" + str(page) + "&fq=news_desk:(\"Sports\")"
    response = requests.get(articlesquery)
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
        articles[term].append(placeholder)
        nyt_result[term] = articles[term]
    
    print("Updating NYT Database")


def youtubeapi(term):
    
    sports = ["/m/06ntj", "/m/0jm_", "/m/018jz", "/m/018w8", "/m/01cgz", "/m/09xp_", "/m/02vx4", "/m/037hz", "/m/03tmr", "/m/01h7lh", "/m/0410tth", "/m/07bs0", "m/07_53"]
    politics = ["/m/05qt0", "/m/01h6rj", "/m/06bvp"]
    business = ["/m/09s1f"]
    entertainment = ["/m/02jjt", "/m/09kqc", "/m/02vxn", "/m/066wd", "/m/0f2f9", "/m/07bxq", "/m/03glg", "/m/068hy"]
    technology = ["/m/07c1v", "/m/07yv9"]
    science = ["/m/01k8wb"]
    art = ["/m/032tl", "/m/04rlf", "/m/05qjc", "/m/041xxh"]
    videos = {}
    videos[term] = []
    youtube_dict = {"sports": sports, "politics": politics, "business": business, "entertainment": entertainment, "technology": technology, "science": science, "art": art}

    category = random.choice(youtube_dict[term])

    endpoint = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=100&topicId=" + category + "&type=video&relevanceLanguage=en&videoSyndicated=true&videoDuration=medium"

    headers = {'Authorization': 'Bearer ' + temporary_token}

    response = requests.get(endpoint, headers=headers).json()

    for dictionary in response["items"]:
        placeholder = {}
        placeholder["url"] = "https://www.youtube.com/embed/" + dictionary["id"]["videoId"]
        placeholder["title"] = dictionary["snippet"]["title"]
        placeholder["description"] = dictionary["snippet"]["description"]

        videos[term].append(placeholder)

        youtube_result[term] = videos[term]

def wikiapi(term):
    
    articles = {}
    articles[term] = []
    session = requests.Session()

    sports = ["Sports", "Recreation", "Air sports", "American football", "Auto racing", "Baseball terminology", "Basketball", "Horse racing", "Ice hockey", "Olympic Games", "Whitewater sports"]
    politics = ["Lists of politicians", "Politics", "Political activism", "Clothing in politics", "Political communication", "Comparative politics", "Cultural politics", "Election campaigning", "Political philosophy", "Political theories"]
    business = ["Chief executive officers", "Billionaires", "Real estate", "Finance", "Business", "Paradoxes in economics", "Money", "Industries (economics)", "Financial markets", "Investment", "Business economics", "Business ethics", "Business economics", "Business terms", "Sports business"]
    entertainment = ["Entertainment", "Lists of games", "Toys", "Film", "Internet", "Television", "Mass media franchises", "Humour", "Entertainment occupations", "Amusement parks", "Gaming", "Film characters", "History of film", "Cinemas and movie theaters", "Celebrity reality television series", "Comedy", "Unofficial observances", "Satire"]
    technology = ["Explorers", "Sports inventors and innovators", "Inventors", "Artificial intelligence", "Computer architecture", "Embedded systems", "Semiconductors", "Telecommunications", "Civil engineering", "Aerospace engineering", "History of the automobile", "Cycling", "Public transport", "Road transport"]
    science = ["Climate change", "Nature conservation", "Pollution", "Biology", "Zoology", "Neuroscience", "Humans", "Plants", "Space", "Astronomy", "Chemistry", "Climate", "Physics-related lists", "Space", "Energy", "Lists of things named after scientists"]
    art = ["Classical studies", "Critical theory", "Culture", "Humanities", "Folklore", "Performing arts", "Visual arts", "Economics of the arts and literature", "Arts occupations", "Fiction", "Fiction anthologies", "Clowning", "Storytelling", "Variety shows", "Theatre"]
    wiki_dict = {"sports": sports, "politics": politics, "business": business, "entertainment": entertainment, "technology": technology, "science": science, "art": art}

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
            placeholder = {'title': title, 'image': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png', 'link': 'https://en.wikipedia.org/wiki/' + title}
        
            articles[term].append(placeholder)

            wiki_result[term] = articles[term]

def mainapi():    
    for category in master_list:
        nytapi(category)
        youtubeapi(category)
        wikiapi(category)
    
@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result,
        "youtube_api": youtube_result, 
        'wiki_api': wiki_result
    })   