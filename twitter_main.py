import tweepy
from tweepy import OAuthHandler

def extract_three_most_rt_tweets(tweets):
    max1 = max2 = max3 = tweets.pop(0)
    for tw in tweets:
        #print("count-> ", tw['retweet_count'])
        if (tw['retweet_count'] >= max1['retweet_count']):
            max3 = max2
            max2 = max1
            max1 = tw
        elif (tw['retweet_count'] >= max2['retweet_count']):
            max3 = max2
            max2 = tw
        elif (tw['retweet_count'] >= max3['retweet_count']):
            max3 = tw

    most_rt_tweets = [max1, max2, max3]
    print("Max1: %s" % max1['retweet_count'])
    print("Max2: %s" % max2['retweet_count'])
    print("Max3: %s" % max3['retweet_count'])

    return most_rt_tweets


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
                     parser=tweepy.parsers.JSONParser())

    return api


def main():
    api = initialize()

    # user[0] -> Fake news,  user[1] -> Real news
    user_id = ["525815006", "335455570"]
    user_name = ["FolksRtalking", "ReutersWorld"]

    print("Collecting tweets...")
    fake_tweets = api.user_timeline(id=user_id[0], count=200)
    real_tweets = api.user_timeline(id=user_id[1], count=200)


    print("Extracting three most retweeted tweets of %s ..." % user_name[0])
    most_rt_fake_tweets = extract_three_most_rt_tweets(fake_tweets)

    print("Extracting three most retweeted tweets of %s ..." % user_name[1])
    most_rt_real_tweets = extract_three_most_rt_tweets(real_tweets)

    print("Done!")

main()
