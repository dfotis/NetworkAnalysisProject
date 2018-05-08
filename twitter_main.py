import tweepy
from tweepy import OAuthHandler
import json
import pandas
import matplotlib
import pymongo


def save_to_txt(custom_object, filename):
    file = filename
    with open(file, "a+") as f:
        line = ""
        for value in custom_object.items():
            line+= (str(value[1].encode("utf-8"))[2:])[:-1]
            line+= "\t"
        f.write(line+"\n")


def get_user_tweets(user_id, api):
    timeline = []
    progress = 0

    for status in tweepy.Cursor(api.user_timeline, id = user_id).items():
        timeline.append(status)
        progress+=1
        #print(status._json)
        print("Fetched "+str(progress)+" out of all timeline items")

    return timeline



def extract_three_most_rt_tweets(tweets):
    max1 = max2 = max3 = tweets.pop(0)
    count  = 0
    for tw in tweets:
        count += 1
        if (tw._json["retweet_count"] >= max1._json["retweet_count"]):
            max3 = max2
            max2 = max1
            max1 = tw
        elif (tw._json['retweet_count'] >= max2._json["retweet_count"]):
            max3 = max2
            max2 = tw
        elif (tw._json["retweet_count"] >= max3._json["retweet_count"]):
            max3 = tw

    print("Count: "+ str(count))

    most_rt_tweets = [max1, max2, max3]
    print("Max1: %s" % max1._json["retweet_count"])
    print("Max2: %s" % max2._json["retweet_count"])
    print("Max3: %s" % max3._json["retweet_count"])

    return most_rt_tweets


def collecting_and_storing_tweets(user_id, user_name, api):
    print("Collecting tweets...")
    fake_tweets = get_user_tweets(user_id[0], api)
    real_tweets = get_user_tweets(user_id[1], api)

    print("Extracting three most retweeted tweets of %s ..." % user_name[0])
    most_rt_fake_tweets = extract_three_most_rt_tweets(fake_tweets)

    print("Extracting three most retweeted tweets of %s ..." % user_name[1])
    most_rt_real_tweets = extract_three_most_rt_tweets(real_tweets)

    print("Extraction of tweets completed!")

    print("Writing to files the most retweeted tweets...")
    for tweet in most_rt_fake_tweets:
        custom_object = {
            "id": tweet._json["id_str"],
            "created_at": tweet._json["created_at"],
            "text": tweet._json["text"],
            "by_user": tweet._json["user"]["id_str"]
        }
        # save_to_json(custom_object, 'most_rt_fake_tweets_file.json')
        save_to_txt(custom_object, 'most_rt_fake_tweets_file.txt')

    for tweet in most_rt_real_tweets:
        custom_object = {
            "id": tweet._json["id_str"],
            "created_at": tweet._json["created_at"],
            "text": tweet._json["text"],
            "by_user": tweet._json["user"]["id_str"]
        }
        # save_to_json(custom_object, 'most_rt_real_tweets_file.json')
        save_to_txt(custom_object, 'most_rt_real_tweets_file.txt')
    print("Writing Completed!")



def initialize():
    # connect with twitter
    consumer_key = 'YDIYvIRyQH9wJIotPr861TDHE'
    consumer_secret = 'xiZNutAgVVkWPxzPUGXFj4RpINd4bWb3YksWNX53cBnDPNCELi'
    access_token = '1511979295-2pnC4Fvm7VmiBY5VhPfBshdUUsCV1nFmWXML9lp'
    access_secret = 'pnCJFBPbNvoovY7w8duqmWOSh1FyiBl43LGe7CxFHRVRc'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True,
                     wait_on_rate_limit_notify=True,
                     )

    return api


def main():
    api = initialize()

    # user[0] -> Fake news,  user[1] -> Real news
    user_id = ["525815006", "335455570"]
    user_name = ["FolksRtalking", "ReutersWorld"]

    collecting_and_storing_tweets(user_id, user_name, api)

main()
