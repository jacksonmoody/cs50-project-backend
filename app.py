# Import necessary libraries
from flask import Flask, jsonify
from flask_apscheduler import APScheduler
from datetime import datetime
from langdetect import detect, DetectorFactory
import time
import random
import requests

# Credentials for the YouTube and NYT APIs. Replace these as appropriate (and as defined in README.md)
API_REFRESH_TOKEN = "1//04msvb6_5J6QdCgYIARAAGAQSNwF-L9IrXYwN23jABbvRc-3FxhYMkZ0QlTkfU4ChFlb4rHBurwb9idzXA9r3Q9I7IX5fjBUx7U8"
CLIENT_ID = "126533689685-t92uspbhgscsseq3urfipuiibp1c14u0.apps.googleusercontent.com"
CLIENT_SECRET = "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"

NYT_KEY = "tQIaepDN84Rl2sfsRyuWGA33YaE6tmQA"

# Hold temporary token for YouTube API
temporary_token = None

# Configure the scheduler API for Flask
class Config:
    SCHEDULER_API_ENABLED = True


# Define the Flask app
app = Flask(__name__)
app.config.from_object(Config())

# Set the seed for the language detector
DetectorFactory.seed = 0

# Define the categories of information to be retrieved by the APIs
master_list = ['sports', 'technology', 'entertainment', 'science', 'politics']

# Define dictionaries to store the results from each
nyt_result = {}
youtube_result = {}
wiki_result = {}


# The following code is executed when the app is first initiated, before the first run of the scheduler
@app.before_first_request
def init():

    global temporary_token

    # Configure the scheduler to refresh the main api every 10 minutes
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='mainapi', func=mainapi, trigger='interval', minutes=10)

    # On first initialization, run the main api job immmediately
    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())

    # Get a temporary token for the YouTube API using the client ID, client secret, and refresh token defined earlier
    endpoint = "https://www.googleapis.com/oauth2/v4/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": API_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    temporary_token = requests.post(endpoint, data=data).json()["access_token"]


def nytapi(term):
    # Define the categories and subcategories for the NYT API
    sports = ["Sports"]
    technology = ["Automobiles", "Technology"]
    entertainment = ["Arts", "Books", "Style", "Culture", "Dining", "Food", "Magazine", "Movies", "T Magazine", "Technology", "The Upshot", "Travel"]
    science = ["Science", "Upshot"]
    politics = ["Metro", "Metropolitan", "National", "Politics", "U.S.", "Washington", "World"]
    nyt_dict = {'sports': sports, 'technology': technology, 'entertainment': entertainment, 'science': science, 'politics': politics}

    # We'll use articles to store the result of queries and then ultimately add articles to the nyt_result dictionary
    global nyt_result
    articles = []
    # Given a specific category, this will pick a random subcategory of that category
    category = random.choice(nyt_dict[term])

    # We query into the NYT's API to get the number of articles in a subcategory, then generate a random page number to query for randomness
    hitsquery = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=" + NYT_KEY + "&begin_date=20160101&fq=news_desk:(\"" + category + "\")"
    response = requests.get(hitsquery)
    response = response.json()
    hits = response['response']['meta']['hits']
    pagenumbers = min(hits // 10, 100)
    page = random.randint(1, pagenumbers)

    # We sleep for 6 seconds to avoid hitting the NYT API's rate limit
    time.sleep(6)

    # We now query into NYT using the random page number we generated and the category we picked.
    articlesquery = "https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=" + NYT_KEY + "&begin_date=20160101&page=" + str(page) + "&fq=news_desk:(\"" + category + "\")"
    response = requests.get(articlesquery)
    response = response.json()

    # We then iterate through each of the article results from our query and add the URL, description, title, and thumbnail image to a placeholder dictionary and append that to our list of nyt_result.
    # We also ensure that are no links in the description as this messes with our html and that we have a default image if there are no images associated with the article.
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

        # We append the placeholder dictionary to our list and then add the completed list to the result dictionary for that term.
        articles.append(placeholder)

    nyt_result[term] = articles

    print("Updating NYT Database")


def youtubeapi(term):
    # Defining the categories and subcategories for the YouTube API.
    sports = ["/m/06ntj"]
    politics = ["/m/05qt0", "/m/01h6rj", "/m/06bvp"]
    entertainment = ["/m/02jjt", "/m/09kqc", "/m/02vxn", "/m/066wd", "/m/0f2f9", "/m/07bxq", "/m/03glg", "/m/068hy", "/m/032tl", "/m/04rlf", "/m/05qjc", "/m/041xxh"]
    technology = ["/m/07c1v", "/m/07yv9"]
    science = ["/m/01k8wb"]
    youtube_dict = {"sports": sports, "politics": politics, "entertainment": entertainment, "technology": technology, "science": science}

    # We'll use videos as a list to store all of our videos (each a dictionary) to add to our youtube result dictionary.
    videos = []
    global youtube_result

    # With the specific category we are given, we get a random subcategory.
    category = random.choice(youtube_dict[term])

    # Then, we query the YouTube API for videos in that subcategory --> we ensure that we also get videos in English that are of medium length, from the United States, and are able to be played outside youtube.com.
    endpoint = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=100&topicId=" + category + "&type=video&relevanceLanguage=en&videoSyndicated=true&videoEmbeddable=true&videoDuration=medium&regionCode=US"

    # Set the bearer token in the header of the API request
    headers = {'Authorization': 'Bearer ' + temporary_token}

    # Make the API request with the appropriate endpoint and header and convert to a json file.
    response = requests.get(endpoint, headers=headers).json()

    # Then, using the result of the query, we iterate through each video adding the URL, description, and title to a placeholder dictionary which we then add to our result dictionary with the term as the key.
    # We also ensure that the title is in English (due to issues with YouTube's language queries) and ensure there are no links in the description as these links mess with our HTML.
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

            try:
                if (detect(placeholder["title"]) == 'en') and (detect(placeholder["description"]) == 'en'):
                    videos.append(placeholder)
                else:
                    continue
            except:
                # Error with language identification -- Do not use this video
                continue

        youtube_result[term] = videos

    except Exception as e:
        print("YouTube API Error with term: " + term)
        print(e)
        print(youtube_result[term])


def wikiapi(term):

    # We'll use articles as a list to store all of our articles (each a dictionary) to add to our Wikipedia result dictionary.
    articles = []
    global wiki_result

    # Defining each of the categories and subcategories and then taking a random result from the category we passed into the function.
    sports = ["Sports", "Recreation", "Air sports", "American football", "Auto racing", "Baseball terminology", "Basketball", "Horse racing", "Ice hockey", "Olympic Games", "Whitewater sports"]
    politics = ["Lists of politicians", "Politics", "Political activism", "Clothing in politics", "Political communication", "Comparative politics", "Cultural politics", "Election campaigning", "Political philosophy", "Political theories"]
    entertainment = ["Entertainment", "Lists of games", "Toys", "Film", "Internet", "Television", "Mass media franchises", "Humour", "Entertainment occupations", "Amusement parks", "Gaming", "Film characters", "History of film", "Cinemas and movie theaters", "Celebrity reality television series", "Comedy", "Unofficial observances", "Satire", "Classical studies", "Critical theory", "Culture", "Humanities", "Folklore", "Performing arts", "Visual arts", "Economics of the arts and literature", "Arts occupations", "Fiction", "Fiction anthologies", "Clowning", "Storytelling", "Variety shows", "Theatre"]
    technology = ["Explorers", "Sports inventors and innovators", "Inventors", "Artificial intelligence", "Computer architecture", "Embedded systems", "Semiconductors", "Telecommunications", "Civil engineering", "Aerospace engineering", "History of the automobile", "Cycling", "Public transport", "Road transport"]
    science = ["Climate change", "Nature conservation", "Pollution", "Biology", "Zoology", "Neuroscience", "Humans", "Plants", "Space", "Astronomy", "Chemistry", "Climate", "Physics-related lists", "Space", "Energy", "Lists of things named after scientists"]
    wiki_dict = {"sports": sports, "politics": politics, "entertainment": entertainment, "technology": technology, "science": science}

    category = random.choice(wiki_dict[term])

    # We set our API url and our parameters to get articles from a specific category and then request the API with our parameters.
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Category:" + category,
        "cmlimit": "500"
    }

    response = requests.get(url=url, params=params).json()

    # For each article in the response, we add the title, a default Wiki image, and the link to a placeholder dictionary and append that dictionary to our list of articles which we add to our wiki result.
    for dictionary in response['query']['categorymembers']:
        title = dictionary['title']
        # This if statement ensures we do not get pages that are categories but instead just get actual pages.
        if not 'Category' in title:
            placeholder = {'title': title, 'image': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png', 'link': formatWikiLink('https://en.wikipedia.org/wiki/' + title)}

            articles.append(placeholder)

    wiki_result[term] = articles

    print("Updating Wiki Database")



# Helper function to replace problematic characters in HTML with their ASCII values (for YouTube)
def decode(htmlTitle):
    htmlTitle = htmlTitle.replace("&lt;", "<")
    htmlTitle = htmlTitle.replace("&gt;", ">")
    htmlTitle = htmlTitle.replace("&quot;", "\"")
    htmlTitle = htmlTitle.replace("&#39;", "\'")
    htmlTitle = htmlTitle.replace("&amp;", "&")
    return htmlTitle



# Helper function to format Wikipedia links correctly
def formatWikiLink(link):
    link = link.replace(" ", "_")
    return link



# Function to add new information for each category from each API to the results (this is the main function that gets all of our info and is scheduled)
def mainapi():
    for category in master_list:
        nytapi(category)
        youtubeapi(category)
        wikiapi(category)
        time.sleep(6)
    print("Finished Updating")



# API Functionality: Return JSON object with results from The New York Times, YouTube, and Wikipedia at default route
@app.route("/")
def api():
    return jsonify({
        "nyt_api": nyt_result,
        "youtube_api": youtube_result,
        'wiki_api': wiki_result
    })