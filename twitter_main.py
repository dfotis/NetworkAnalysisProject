from twitter import *
import tweepy
from tweepy import OAuthHandler
import time
import collections
import pandas as pd
import matplotlib.pyplot as plt
import pymongo
from pymongo import MongoClient
import networkx as nx

def save_to_mongo(collection_name, custom_object):
    try:
        client = MongoClient('localhost:27017')
        db = client['TwitterDB']
        collection = db[collection_name]

        result = collection.insert_one(custom_object).inserted_id
        # print("Saved successfully.")
    except pymongo.errors.ConnectionFailure as e:
        print("Could not connect to MongoDB: %s" % e)


def collect_retweets(timeline_tweets, api, type):
    for tweet in timeline_tweets:
        save_to_mongo("Retweeted_" + type, tweet._json)

        count = 0
        page = 1
        while True:
            retweets = api.retweets(id=tweet._json['id'], page=page, count=100)
            if retweets:
                for retweet in retweets:
                    count += 1
                    save_to_mongo(type+"_" + str(tweet._json['id']), retweet._json)
            else:
                # All done
                break
            page += 1
        print(count)
        print(type + "_" + str(tweet._json['id_str']) + " retweets: " + str(count))


def sort_by_key(status_obj):
    try:
        # print("Retweet_count: " + str(status_obj["retweet_count"]))
        return int(status_obj._json["retweet_count"])
    except KeyError:
        return 0


def extract_three_most_rt_tweets(tweets, type):
    if(type == 'real'):
        sorted_lst = sorted(tweets, key=sort_by_key, reverse=True)[:3]
        for item in sorted_lst:
            print("Retweet_count: " + str(item._json["retweet_count"]))

        return sorted_lst
    else:
        #To solve a problem with the fake account

        sorted_lst = sorted(tweets, key=sort_by_key, reverse=True)[5:15]

        #Fake_572439843332100097 retweets: 1860
        #Fake_571481175627329536 retweets: 967
        #Fake_575387925992570881 retweets: 970

        list = []
        ids = [572439843332100097, 571481175627329536, 575387925992570881]
        for item in sorted_lst:
            if item._json['id'] in ids:
                list.append(item)
                print("Retweet_count: " + str(item._json["retweet_count"]))

        return list


def get_user_tweets(user_id, api):
    progress = 0
    statuses = []
    for status in tweepy.Cursor(api.user_timeline, id=user_id).items():
        if (status._json['id'] != 996578019606134784):
            statuses.append(status)
            progress += 1
    print("Fetched " + str(progress) + " out of all timeline items")

    return statuses


def get_user(user_id, api):
    print("Searching full information for user with id " + str(user_id))
    try:
        user_json = api.get_user(user_id)
    except tweepy.TweepError as tweep_error:
        print("Error with code : " + str(tweep_error.response.text))
        return 0
    return user_json


def get_user_network(api, user_id):
    print("Searching network for user with id " + str(user_id))

    followers = []
    #friends = []
    max_followers = 10000
    #max_friends = 100000
    try:
        for page in tweepy.Cursor(api.followers_ids, id=user_id).pages():
            followers.extend(page)
            if len(followers) >= max_followers:
                break
            print("Followers so far : " + str(len(followers)))
        print("finished followers")
        #print("finished friends")
    except tweepy.TweepError as tweep_error:
        #print("Error with code : " + str(tweep_error.response.text))
        #if ('"code":34,"message":"Sorry, that page does not exist."' in str(tweep_error.response.text)):
        print("Find error")

    print("User with ID: " + str(user_id) + " has " + str(len(followers)) + " followers")
    custom_object = {
        "id": user_id,
        "followers": followers
    }
    return custom_object


def fisrt_step(user_id, api):
    print("Collecting tweets from the fake user's timelime...")
    fake_timeline_tweets = get_user_tweets(user_id[0], api)
    print("Calculating the three most retweeted...")
    most_rted_fake_tweets = extract_three_most_rt_tweets(fake_timeline_tweets, 'fake')

    print("\nCollecting tweets from the real user's timelime...")
    real_timeline_tweets = get_user_tweets(user_id[1], api)
    print("Calculating the three most retweeted...")
    most_rted_real_tweets = extract_three_most_rt_tweets(real_timeline_tweets, 'real')

    print("Collecting fake retweets...")
    collect_retweets(most_rted_fake_tweets, api, "Fake")

    print("\nCollecting real retweets...")
    collect_retweets(most_rted_real_tweets, api, "Real")


'''
    Plotting the number of retweets in time
'''
def retweets_time_plot(collection_name):
    client = MongoClient('localhost:27017')
    db = client['TwitterDB']
    collection = db[collection_name]

    dates = {}
    for date in collection.distinct("created_at"):
        time_stamp = time.strftime('%Y-%m-%d %H', time.strptime(date, '%a %b %d %H:%M:%S +0000 %Y'))
        dates[time_stamp] = date[:-17]
    ordered_dates = collections.OrderedDict(sorted(dates.items(), key=lambda t: t[0]))
    # print(ordered_dates)

    dict = {}
    for date in ordered_dates.keys():
        dict[date] = collection.find({'created_at': {'$regex': '^' + dates[date]}}).count()
    print(dict)

    values = []
    for i in dict.values():
        values.append(i)
    keys = []
    for i in dict.keys():
        keys.append(i)

    df = pd.DataFrame(values)
    df.plot()

    plt.xticks(range(len(dates)), keys)
    plt.xticks(rotation=45)
    plt.show()


'''
    Calculating the first hop from the initial user
    Using show_friendship method
'''
def first_hop(api, source, tweet_id, type):
    client = MongoClient('localhost:27017')
    db = client['TwitterDB']
    # collection = db['Real_993924956424736769']
    collection = db[type+'_' + str(tweet_id)]

    # True False-> is not following you, False True->you are being followed by him, False False = there is no connection between you two
    all_users = []
    first_hop = []

    retweet_limit = 0
    count = 0
    for user in collection.find({}, {'user': 1}):
        all_users.append(user['user']['id'])
        a = api.show_friendship(source_id=source, target_id=user['user']['id'])

        # retweet_limit -= 1
        # if(retweet_limit == 0):
        #    print("---> Reached 180 retweets!")
        #    break
        # else:
        #    print("Checked: "+str(180-retweet_limit) +"("+str(user['user']['id'])+")")
        retweet_limit += 1
        print("Checked: " + str(retweet_limit) + "  (" + str(user['user']['id']) + ")")

        if(a[1].following):
            count += 1
            print("Follower: "+str(count))
            first_hop.append(user['user']['id'])
            save_to_mongo('FirstHop_'+str(tweet_id), get_user(user['user']['id'], api)._json)


    collection = db['FirstHop_' + str(tweet_id)]
    # source = '335455570'
    for target in collection.find({}, {'id': 1}):
        custom_object = {
            "hop": "fisrt_hop",
            "source": source,
            "target": target['id']}
        # print(custom_object)
        save_to_mongo('All_hops_' + str(tweet_id), custom_object)
    print("First Hop Completed")


'''
    Calculating the rest hops by getting the whole network of a user
'''
def other_hops(api, tweet_id, type):
    client = MongoClient('localhost:27017')
    db = client['TwitterDB']
    collection = db[type+'_' + str(tweet_id)]

    # Create a list with the ids of ALL the retweeters that have retweeted the current tweet
    all_retweeters = []
    for source in collection.find({}, {'user': 1}):
        all_retweeters.append(source['user']['id'])
    print(len(all_retweeters))

    # Create a list with all ids of the first hopers
    collection = db['FirstHop_' + str(tweet_id)]
    first_hop_retweeters = []
    for source in collection.find({}, {'id': 1}):
        first_hop_retweeters.append(source['id'])
    print(len(first_hop_retweeters))

    # Create a list with all ids of the remaining retweeters that they have not participate in the first hop
    remaining_retweeters = [n for n in all_retweeters if n not in first_hop_retweeters]
    print(len(remaining_retweeters))

    current_hop_retweeters = first_hop_retweeters
    next_hop_retweeters = []
    hop = 2

    retweeter_counter = 0
    while (len(remaining_retweeters) >= 0 and hop<=12):
        for current_retweeter in current_hop_retweeters:
            retweeter_counter += 1
            print("Hop: "+str(hop)+", Total: "+str(len(current_hop_retweeters))+", Checked: "+str(retweeter_counter))
            try:
                current_retweeter_network = get_user_network(api, current_retweeter)
                temp = (list(set(current_retweeter_network['followers']).intersection(remaining_retweeters)))
                if (len(temp) != 0):
                    for target in temp:
                        next_hop_retweeters.append(target)
                        custom_object = {
                            "hop": str(hop) + "_hop",
                            "source": current_retweeter,
                            "target": target}
                        # print(custom_object)
                        save_to_mongo('All_hops_' + str(tweet_id), custom_object)
                        save_to_mongo(str(hop)+'_Hop_'+str(tweet_id), custom_object)
                    remaining_retweeters = [n for n in remaining_retweeters if n not in temp]
            except tweepy.TweepError as e:
                if('Failed to send request:' in e.reason):
                    print("Time out error caught.")
                    time.sleep(180)
                    continue

        print(str(hop) + " Hop Completed")
        hop += 1
        current_hop_retweeters = next_hop_retweeters
        next_hop_retweeters = []
        retweeter_counter = 0


'''
    Plotting the number of retweets according to hops
'''
def hops_plot(tweet_id):
    hops = ['fisrt_hop', '2_hop', '3_hop', '4_hop', '5_hop', '6_hop', '7_hop', '8_hop', '9_hop']
    client = MongoClient('localhost:27017')
    db = client['TwitterDB']
    collection = db['All_hops_'+str(tweet_id)]

    dict = {}
    for hop in hops:
        dict[hop] = collection.find({'hop': {'$regex': '^' + hop}}).count()
    print(dict)

    values = []
    for i in dict.values():
        values.append(i)
    keys = ['1_hop', '2_hop', '3_hop', '4_hop', '5_hop', '6_hop', '7_hop', '8_hop', '9_hop']

    df = pd.DataFrame(values)
    df.plot()

    plt.xticks(range(len(hops)), keys)
    plt.xticks(rotation=45)
    plt.show()


'''
    Construsction of a user network which represents the diffusion of a tweet
    Using networkx
'''
def graph_making(tweet_id):
    client = MongoClient('localhost:27017')
    db = client['TwitterDB']
    collection = db['All_hops_'+str(tweet_id)]

    G = nx.Graph()

    for node in collection.find():
        if (node['source'] not in G):
            G.add_node(node['source'])

        if (node['target'] not in G):
            G.add_node(node['target'])

        G.add_edge(node['source'], node['target'])
    nx.draw(G)
    plt.show()


'''
    Connecting with twitter API
'''
def initialize():
    # connect with twitter
    consumer_key = 'YDIYvIRyQH9wJIotPr861TDHE'
    consumer_secret = 'xiZNutAgVVkWPxzPUGXFj4RpINd4bWb3YksWNX53cBnDPNCELi'
    access_token = '1511979295-2pnC4Fvm7VmiBY5VhPfBshdUUsCV1nFmWXML9lp'
    access_secret = 'pnCJFBPbNvoovY7w8duqmWOSh1FyiBl43LGe7CxFHRVRc'

    #consumer_key = 'mWaOYWkMOS08r4g9P7BpqNQhs'
    #consumer_secret = '5CIdAZsEb4mwwfZaidrBN8ZuYtr6Kwq3CKzUqBupGnzLqIZIOj'
    #access_token = '1511979295-SSEQBT7J3e8JjPXsBL5p1VxfZF0BhW9WPAbmljb'
    #access_secret = 'Ra2GT7fqjGqnUgsmoL9hhGwlfkbvHB11107x2EuvRD9E2'

    #consumer_key = 'c1KL0lpkitgFDrQ9ABacVc3c5'
    #consumer_secret = 'de6Csu2XGAt8tzO6tI92rsvd8cg8WZ8OMEe6AQ74dPmMoVTCWW'
    #access_token = '1511979295-TRCI3I8qXsM4dxNZ0UO7qXomX5HraVUAc0BvY4I'
    #access_secret = 'ABCqePFhYYJpwDG2EzpBPVuvV2HBu1ZC8HqmnGAFCK1hq'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True,
                     wait_on_rate_limit_notify=True,
                     compression=True)

    twitter = Twitter(
        auth=OAuth(access_token, access_secret, consumer_key, consumer_secret))

    return api, twitter



def main():
    api, twitter = initialize()

    # IDs and Screen_name of fake and real twitter accounts
    user_id = ["525815006", "335455570"]
    user_name = ["FolksRtalking", "ReutersWorld"]

    fisrt_step(user_id, api)

    '''
        For Real account
    '''
    #Time plotting
    # retweets_time_plot('Real_989791897890770944')
    # retweets_time_plot('Real_993889654909947904')
    # retweets_time_plot('Real_993924956424736769')

    # first_hop(api, user_id[1], 989791897890770944, 'Real')
    # first_hop(api, user_id[1], 993889654909947904, 'Real')
    # first_hop(api, user_id[1], 993924956424736769,'Real')

    # other_hops(api, 989791897890770944, 'Real')
    # other_hops(api, 993889654909947904, 'Real')
    # other_hops(api, 993924956424736769, 'Real')

    #Hops plotting
    # hops_plot(989791897890770944)
    # hops_plot(993889654909947904)
    # hops_plot(993924956424736769)

    #Graph making
    # graph_making(989791897890770944)
    # graph_making(993889654909947904)
    # graph_making(993924956424736769)

    '''
        For Fake account
    '''
    #Time plotting
    #retweets_time_plot('Fake_572439843332100097')
    #retweets_time_plot('Fake_571481175627329536')
    #retweets_time_plot('Fake_575387925992570881')

    #first_hop(api, user_id[0], 572439843332100097, 'Fake')
    #first_hop(api, user_id[0], 571481175627329536, 'Fake')
    #first_hop(api, user_id[0], 575387925992570881,'Fake')

    # other_hops(api, 572439843332100097, 'Fake')
    # other_hops(api, 571481175627329536, 'Fake')
    # other_hops(api, 575387925992570881, 'Fake')

    #Hops plotting
    # hops_plot(572439843332100097)
    # hops_plot(571481175627329536)
    # hops_plot(575387925992570881)

    #Graph making
    # graph_making(572439843332100097)
    # graph_making(571481175627329536)
    # graph_making(575387925992570881)

main()



