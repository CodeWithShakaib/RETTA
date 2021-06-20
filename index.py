import string
from flask import Flask, redirect, url_for, request
from flask import render_template
from flask_cors import CORS, cross_origin
from nltk.corpus.reader import api
import db_connection as db
from flask import jsonify
from bson.objectid import ObjectId
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import json
import datetime
import re
import string


# methods for preprocessing
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer

import pandas as pd
import numpy as np
import warnings 
warnings.filterwarnings('ignore')

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('vader_lexicon')

# -*- coding: utf-8 -*-
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
#driver = webdriver.Chrome("./chromedriver", options=options)

users = db.mydb["users"]
tweets_mongo = db.mydb["tweets"]

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def to_json(data):
    output = []
    for d in list(data):
            d["_id"] = str(d["_id"])
            output.append(d)

    return jsonify(output)

def for_url(trend):
    if '#' in trend:
        trend = trend.replace('#','%23')
    if ' ' in trend:
        trend.replace(' ', '%20')
    return trend

def seprate_tweet_text(tweet):
    date_list = list(range(1,32))
    gol = False
    starting_index = 0
    ending_index = 0
    
    for i in date_list:
        if '·'+str(i)+'h' in tweet:
            starting_index = tweet.index('·'+str(i)+'h') + len('.'+str(i)+'h')
            gol = True

    if gol == False:
        for i in date_list:
            if ' '+str(i) in tweet:
                print("in2")
                starting_index = tweet.index(' '+str(i)) + len(' '+str(i))
                break
       
    tweet = tweet[::-1]
    for j in tweet:
        if j.isdigit():
            tweet = tweet[1:]
        else:
            tweet = tweet[::-1]
            print(tweet)
            break
    tweet = tweet[starting_index:]
    
    # try:
    #     if tweet[0] in ['0','1','2','3','4','5','6','7','8','9']:
    #         tweet = tweet[1:]
    # except:
    #     print("in expect")

    return tweet.replace('\n', '')




def preprocess_tweet_text(tweet):
    '''
    Run a set of transformational steps to preprocess text
    of the tweet.
    '''

    # remove digits from tweet
    tweet = re.sub(" \d+", " ", tweet)
    
    #convert all the text to lowercase
    tweet = tweet.lower()
    
    #remove any urls
    tweet = re.sub(r"http\S+|www\S+\|https\S+", " ", tweet, flags=re.MULTILINE)

    #remove puncuation 
    tweet = tweet.translate(str.maketrans(" "," ", string.punctuation))

    #remove user @ references and # from tweets
    tweet = re.sub(r'\@\w+|\#'," ",tweet)

    #remove stopwords
    stop_words = set(stopwords.words('english')) 
    tweet_tokens = word_tokenize(tweet)
    filtered_words = [word for word in tweet_tokens if word not in stop_words]

    # stemming
    '''
    Stemming is a technique used to extract the base form of the words by removing affixes from them. It is just like cutting down the branches of a tree to its stems. For example, the stem of the words eating, eats, eaten is eat. Search engines use stemming for indexing the words.
    '''
    ps = PorterStemmer()
    stemmed_words = [ps.stem(w) for w in filtered_words]

    # lematizing
    lemmatizer = WordNetLemmatizer()
    lemma_words = [ lemmatizer.lemmatize(w, pos='a') for w in stemmed_words ]

    return ' '.join(lemma_words)



def api_response(error, data, status):
    return



@app.route('/users/<id>')
def get(id):
    try:
        return to_json(users.find({ "_id": ObjectId(id)}))
    except Exception as err:
        print(err)
        return "error", 400


@app.route('/users')
def getAll():
    try:
        return to_json(users.find())
    except Exception as err:
        print(err)
        return "error"

@app.route('/users/history/<id>', methods=['GET', 'POST'])
def history(id):
    try:
        if request.method == 'POST':
            body = request.json
            users.update_one(
                { '_id': ObjectId(id)},
                { '$push': {"history": {
                'date': str(datetime.datetime.now()),
                'trend': body['trend'],
                'positive' : body['positive'],
                'negitive': body['negitive'],
                'neutral': body['neutral']
            }}})
                
            return to_json(users.find({ "_id": ObjectId(id)}))
        else:
            return "Invalid method", 400
    except Exception as err:
        print(err)
        return "error"

@app.route('/users/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            body = request.json
            if users.find_one({"email": body['email']}) == None:
                object_id = users.insert_one({"email" : body['email'], "name": body['name'], "password": body['password']})

                return to_json(users.find({ "_id": ObjectId(object_id.inserted_id)}))
            else:
                return "Email is already pressent", 404
        else:
            return "Invalid method", 400
    except Exception as err:
        print(err)
        return "error"

@app.route('/users/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            body = request.json
            if users.find_one({"email": body['email'], "password": body['password']}) != None:

                return to_json(users.find({"email": body['email'], "password": body['password']}))
            else:
                return "Invalid email or password", 404
        else:
            return "Invalid method", 400
    except Exception as err:
        print(err)
        return "error", 400

@app.route('/users/histories', methods=['GET', 'POST'])
def histories():

    return render_template('histories.html')

@app.route('/getTwitterTrends')
def getTwitterTrends():
    try:


        # getting twitter trends using run time scrapping
        # driver.get("https://twitter.com/i/trends")
        # time.sleep(3)

        # soup = BeautifulSoup(driver.page_source,"html.parser")


        # trends_data = []
        # trend_type = []
        # trend_text = []
        # tweets_count = []

        # dummy_list = []
        # for trend in soup.find_all('div', {"data-testid":"trend"}):
        #     a = list(set([str(i.text) for i in trend.find_all('span')]))
    
        #     for i in a:
        #         if 'Trending' in i:
        #             dummy_list.append(i)
        #             trend_type.append(i)
        #         elif 'Tweets' in i:
        #             dummy_list.append(i)
        #             tweets_count.append(i)
        #         else:
        #             dummy_list.append(i)
        #             trend_text.append(i)

        #         if len(dummy_list) != 3:
        #             tweets_count.append(0) 


        #         dummy_list.clear()
        #-------------------------------
        
        trend_text = []
        for data in list(tweets_mongo.find({})):
            trend_text.append(data['trend'])

        trend_text = trend_text[-20:]
        return jsonify(trend_text)
    except Exception as err:
        print(err)
        return "error"


@app.route('/scrapeTweets', methods=['GET', 'POST'])
def scrapeTweets():
    try:
        if request.method == 'POST':
            body = request.json
            tweets_data = []
            tweets = []
            dummy = []
            trends = body['trends']
            before = []
            for_human = [] 
            for_ml = []

            # Scrapping tweets from twitter
            # --------------------------
            # driver.get(f'https://twitter.com/search?q={for_url(trends[0])}&src=trend_click&vertical=trends')
            # time.sleep(3)
            # for i in range(30):
            #     a = BeautifulSoup(driver.page_source,"html.parser")
                
            #     dummy.clear()
            #     for j in a.find_all('article'):
            #         dummy.append(j.text)
                 
            #     driver.execute_script("window.scrollTo(0, 100*document.body.scrollHeight)")
            #     time.sleep(3)
            #     tweets_data += dummy

            

            # tweets_data = filter(None, list(set(tweets_data)))
            
           # =============== end region ==================
            

            
            finalized_tweets = []
            tweets_data = list(tweets_mongo.find({"trend": trends[0]}))[0]['tweets']
               
            for i in tweets_data[:10]:
                before.append(i)
            
            for i in before:
                for_human.append(seprate_tweet_text(i))
                
            for i in for_human:
                for_ml.append(preprocess_tweet_text(i))
                

            
            for i in tweets_data:
                tweet = seprate_tweet_text(i)
                
                finalized_tweets.append(tweet)

            result = []
            body = request.json
            
            tweets = finalized_tweets
            sia = SentimentIntensityAnalyzer()
            for tweet in tweets:
                tweet = preprocess_tweet_text(tweet)
                resp = sia.polarity_scores(tweet)
                result.append(resp)
            
            apiRes = []
            sentiment = ''
            positive_tweets = 0
            negitive_tweets = 0
            neutral_tweets = 0
            for i in range(len(tweets)):
                if result[i]['compound'] > 0:
                    sentiment = 'POSITIVE'
                    positive_tweets +=1
                elif result[i]['compound'] < 0:
                    sentiment = 'NEGATIVE'
                    negitive_tweets +=1
                else:
                    sentiment = 'NEUTRAL'
                    neutral_tweets +=1

                
                apiRes.append({"tweet": tweets[i], "sentiment": sentiment, "polarity" : result[i]['compound']})

            
                
            
            return jsonify({"before": before,"for_human":for_human,"for_ml_model":for_ml,"finalized_tweets": finalized_tweets,"report": apiRes, "positive_per": (positive_tweets/len(tweets))*100, "negitive_per": (negitive_tweets/len(tweets))*100, "neutral_per": (neutral_tweets/len(tweets))*100 })
    except Exception as err:
        print(err)
        return "error"

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    return render_template('login_page.html')

@app.route('/sentimentAnalyzer', methods=['GET', 'POST'])
def sentimentAnalyzer():
    try:
        if request.method == 'POST':
            result = []
            body = request.json
            tweets = body['tweets']
            sia = SentimentIntensityAnalyzer()
            for tweet in tweets:
                tweet = preprocess_tweet_text(tweet)
                resp = sia.polarity_scores(tweet)
                result.append(resp)
            
            apiRes = []
            sentiment = ''
            positive_tweets = 0
            negitive_tweets = 0
            neutral_tweets = 0
            for i in range(len(tweets)):
                if result[i]['compound'] > 0:
                    sentiment = 'POSITIVE'
                    positive_tweets +=1
                elif result[i]['compound'] < 0:
                    sentiment = 'NEGATIVE'
                    negitive_tweets +=1
                else:
                    sentiment = 'NEUTRAL'
                    neutral_tweets +=1

                
                apiRes.append({"tweet": tweets[i], "Sentiment": sentiment, "Polarity/ compound" : result[i]['compound']})
            
            return jsonify({"report": apiRes, "positive_per": (positive_tweets/len(tweets))*100, "negitive_per": (negitive_tweets/len(tweets))*100, "neutral_per": (neutral_tweets/len(tweets))*100 })
    except Exception as err:
        print(err)
        return "error"

@app.route('/register_page', methods=['GET', 'POST'])
def register_page():
    return render_template('register_page.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000)
