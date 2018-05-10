import tweepy
from tweepy import OAuthHandler
import time
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

def save_to_json(custom_object, filename):
    file = filename
    try:
        with open(file) as f:
            data = json.load(f)
            for ob in custom_object:
                data.append(ob)
            f.close()

        with open(file, 'w') as f:
            json.dump(data, f, indent=2)
            f.close()
    except (Exception):
        print("failed to save an entry!")


def get_user_tweets(user_id, api, filename):
    data = {}
    data['tweets'] = []
    progress = 0

    for tweet in tweepy.Cursor(api.user_timeline, id=user_id).items():
        data['tweets'].append(tweet)
        progress += 1
        print("Fetched "+str(progress)+" out of all timeline items")

    print("Storing tweets...")
    storing_tweets(data['tweets'], filename)
    print("Downloaded {0} tweets".format(progress))

    return data['tweets']



def extract_three_most_rt_tweets(tweets, filename):
    max1 = max2 = max3 = tweets.pop(0)
    count  = 0
    for tw in tweets:
        count += 1
        if (tw["retweet_count"] >= max1["retweet_count"]):
            max3 = max2
            max2 = max1
            max1 = tw
        elif (tw['retweet_count'] >= max2["retweet_count"]):
            max3 = max2
            max2 = tw
        elif (tw["retweet_count"] >= max3["retweet_count"]):
            max3 = tw

    print("Count: "+ str(count))

    most_rt_tweets = []
    most_rt_tweets.append(max1)
    most_rt_tweets.append(max2)
    most_rt_tweets.append(max3)

    with open(filename, 'w+') as f:
        json.dump(most_rt_tweets, f, indent=2)
        f.close()

    print("Max1: %s" % max1["retweet_count"])
    print("Max2: %s" % max2["retweet_count"])
    print("Max3: %s" % max3["retweet_count"])

    return most_rt_tweets


def storing_tweets(tweets, filename):
    print("Writing to files the tweets...")
    tweet_list = []
    for tweet in tweets:
        custom_object = {
            "id": tweet._json["id"],
            "id_str": tweet._json["id_str"],
            "created_at": tweet._json["created_at"],
            "text": tweet._json["text"],
            "by_user": tweet._json["user"],
            "retweeted": tweet._json["retweeted"],
            "retweet_count": tweet._json["retweet_count"]
        }
        tweet_list.append(custom_object)
    save_to_json(tweet_list, filename)
    #save_to_txt(custom_object, filename)



def collecting_tweets(user_id, user_name, api, filename):
    tweetCount = 0
    maxTweets = 1000000
    data = {}
    data['tweets'] = []

    while tweetCount < maxTweets:
        print(api.rate_limit_status()['resources']['search'])
        try:
            # Write the JSON format to the text file, and add one to the number of tweets we've collected
            for tweet in tweepy.Cursor(api.user_timeline, id=user_id).items(10):
                data['tweets'].append(tweet)
                tweetCount += 1

            print("Storing tweets...")
            storing_tweets(data['tweets'], filename)
            data['tweets'] = []

            # Display how many tweets we have collected
            print("Downloaded {0} tweets".format(tweetCount))
        except tweepy.TweepError as e:
            print("some error : " + str(e))

    print("Downloaded {0} tweets, Saved to {1}".format(tweetCount, filename))





def initialize():
    # connect with twitter
    consumer_key = 'YDIYvIRyQH9wJIotPr861TDHE'
    consumer_secret = 'xiZNutAgVVkWPxzPUGXFj4RpINd4bWb3YksWNX53cBnDPNCELi'
    access_token = '1511979295-2pnC4Fvm7VmiBY5VhPfBshdUUsCV1nFmWXML9lp'
    access_secret = 'pnCJFBPbNvoovY7w8duqmWOSh1FyiBl43LGe7CxFHRVRc'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True,
                     wait_on_rate_limit_notify=True)

    return api


def main():
    api = initialize()

    # user[0] -> Fake news,  user[1] -> Real news
    user_id = ["525815006", "335455570"]
    user_name = ["FolksRtalking", "ReutersWorld"]

    with open('fake.json', mode='w', encoding='utf-8') as f:
        json.dump([], f)
    with open('real.json', mode='w', encoding='utf-8') as f:
        json.dump([], f)

    #collecting_tweets(user_id[0], user_name[0], api, 'fake.json')
    #collecting_tweets(user_id[1], user_name[1], api, 'real.json')


    get_user_tweets(user_id[0], api, 'fake.json')
    get_user_tweets(user_id[1], api, 'real.json')

    print("Extracting three most retweeted tweets of %s ..." % user_name[0])
    with open('fake.json', mode='r', encoding='utf-8') as f:
        fake_tweets = json.load(f)
    most_rt_fake_tweets = extract_three_most_rt_tweets(fake_tweets, 'most_rt_fake_tweets.json')


    print("Extracting three most retweeted tweets of %s ..." % user_name[1])
    with open('real.json', mode='r', encoding='utf-8') as f:
        real_tweets = json.load(f)
    most_rt_real_tweets = extract_three_most_rt_tweets(real_tweets, 'most_rt_real_tweets.json')


    print("Extraction of tweets completed!")



main()
