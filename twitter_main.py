import tweepy
from tweepy import OAuthHandler
from tweepy.parsers import JSONParser
import time
import json
import pandas
import matplotlib
import pymongo
import pprint
from pymongo import MongoClient


def save_to_mongo(collection_name, custom_object):
    try:
        client = MongoClient('localhost:27017')
        db = client['TwitterData']
        collection = db[collection_name]

        result = collection.insert_one(custom_object).inserted_id
        print("Saved successfully.")
    except pymongo.errors.ConnectionFailure as e:
        print("Could not connect to MongoDB: %s" % e)


def get_user_tweets(user_id, api):
    statuses_as_json = []
    progress = 0

    for status in tweepy.Cursor(api.user_timeline, id=user_id).items(20):
        #print("Status: " + str(status._json))
        statuses_as_json.append(status._json)
        progress += 1
        print("Fetched " + str(progress) + " out of all timeline items")

    return statuses_as_json


def sort_by_key(status_obj):
    try:
        #print("Retweet_count: " + str(status_obj["retweet_count"]))
        return int(status_obj["retweet_count"])
    except KeyError:
        return 0


def extract_three_most_rt_tweets(tweets):
    return sorted(tweets, key=sort_by_key, reverse=False)[:3]

    # max1 = max2 = max3 = tweets.pop(0)
    # count  = 0
    # for tw in tweets:
    #     count += 1
    #     if (tw._json["retweet_count"] >= max1._json["retweet_count"]):
    #         max3 = max2
    #         max2 = max1
    #         max1 = tw
    #     elif (tw._json['retweet_count'] >= max2._json["retweet_count"]):
    #         max3 = max2
    #         max2 = tw
    #     elif (tw._json["retweet_count"] >= max3._json["retweet_count"]):
    #         max3 = tw
    #
    # print("Count: "+ str(count))
    #
    # most_rt_tweets = []
    # most_rt_tweets.append(max1._json)
    # most_rt_tweets.append(max2._json)
    # most_rt_tweets.append(max3._json)
    #
    # print("Max1: %s" % max1._json["retweet_count"])
    # print("Max2: %s" % max2._json["retweet_count"])
    # print("Max3: %s" % max3._json["retweet_count"])
    #
    # return most_rt_tweets


def initialize():
    # connect with twitter
    consumer_key = 'YDIYvIRyQH9wJIotPr861TDHE'
    consumer_secret = 'xiZNutAgVVkWPxzPUGXFj4RpINd4bWb3YksWNX53cBnDPNCELi'
    access_token = '1511979295-2pnC4Fvm7VmiBY5VhPfBshdUUsCV1nFmWXML9lp'
    access_secret = 'pnCJFBPbNvoovY7w8duqmWOSh1FyiBl43LGe7CxFHRVRc'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    api = tweepy.API(auth,
                     # parser=tweepy.parsers.JSONParser(),
                     wait_on_rate_limit=True,
                     wait_on_rate_limit_notify=True)

    return api


def main():
    api = initialize()

    # user[0] -> Fake news,  user[1] -> Real news
    user_id = ["525815006", "335455570"]
    user_name = ["FolksRtalking", "ReutersWorld"]

    most_rt_statuses = []

    most_rt_statuses.append(extract_three_most_rt_tweets(get_user_tweets(user_id[0], api)))
    most_rt_statuses.append(extract_three_most_rt_tweets(get_user_tweets(user_id[1], api)))

    pprint.pprint("Printing lenghts: " + str(len(most_rt_statuses[0])) + "|" + str(len(most_rt_statuses[1])))

    for tweet in most_rt_statuses[0]:
        #save_to_mongo("RetweetedFake", tweet)
        for tweets in api.retweets(tweet['id'], count=100):
            save_to_mongo("Fake_" + str(tweet['id']), tweets._json)

    for tweet in most_rt_statuses[1]:
        #save_to_mongo("RetweetedReal", tweet)
        for tweets in api.retweets(tweet['id'], count=100):
            save_to_mongo("Real_" + str(tweet['id']), tweets._json)

    # collection = db['RetweetedFake']
    # for document in collection.find():

    # collection = db['RetweetedReal']
    # for document in collection.find():


main()
