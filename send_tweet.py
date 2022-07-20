import json
import os
import random
import sys
import time
import time 
import tweepy
import urllib

# from dalle2 import Dalle2
# from pillow_utils import *
from string import Template
from tenacity import retry, wait_exponential, stop_after_attempt

import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option('display.max_colwidth', None)

DALLE_SESSION_BEARER_TOKEN = os.environ["DALLE_SESSION_BEARER_TOKEN"]

FILE_PATH = 'data/twitter_post_log.csv'

COLUMNS = [
    'timestamp',
    'bible_or_anime',
    'quote',
    'quote_source',
    'image_prompt',
    'image_file',
    'image_file_upscaled',
    'image_file_motivational',
    'tweet_link',
    'tweet_id',
]

AESTHETIC = [
    'anime', 'cartoon', 'cyberpunk', 'dieselpunk', 'fantasy', 'gothic',
    'horror', 'indie', 'kawaii', 'memphis', 'post-apocalyptic', 'realistic',
    'sci-fi', 'steampunk', 'urban', 'vaporpunk', 'vaporwave', 
]

MEDIUM = [
    'acrylic', 'charcoal sketch', 'colored pencil', 'crayon',
    'digital painting', 'etching', 'illustration', 'oil painting', 'pastel',
    'scientific diagram', 'screen printing', 'sketch', 'ukiyo-e', 'vector art',
    'watercolor', 'woodcut', 'photograph',
]

STYLE = [
    'surrealism', 'street art', 'street photography', 'art deco', 'cubism',
    'dada', 'expressionism', 'art nouveau', 'impressionism', 'neoclassicism',
    'baroque', 'renaissance painting', 'cave painting', 'portrait',
    'byzantine', 'ancient', 
]

ARTIST = [
    'Beatrix Potter', 'Hayao Miyazaki', 'Normal Rockwell', 'Dr. Seuss',
    'Claude Monet', 'Paul Cezanne', 'Paul Gauguin', 'Edouard Manet',
    'Edgar Degas', 'Pierre-Auguste Renoir', 'J. M. W. Turner', 'Hokusai',
    'Odilon Redon', 'James Abbott McNeill Whistler', 'Winslow Homer',
    'Yoshitoshi', 'Vincent van Gogh', 'Raphael', 'Gustav Klimt', 'Rembrandt',
    'Edvard Munch', 'El Greco', 'John Singer Sargent', 'Amedeo Modigliani',
    'Wassily Kandinsky', 'Georges Seurat', 'Sol LeWitt', 'Henri Rousseau',
    'Edward Hopper', 'Franz Marc', 
]

FLAVOR = Template('$aesthetic $style $medium in the style of $artist')
PROMPT = Template('$quote, $flavor')
PROMPT_MAX_LENGTH = 400

@retry(wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(5))
def get_latest_tweets_by_followers(api, count=10):
    follower_tweets = [
        (tweet.id_str, tweet.full_text)
        for friend_id in api.get_friend_ids()
        for tweet in api.user_timeline(
            tweet_mode='extended',
            user_id=friend_id,
            count=count,
            include_rts=False,
            exclude_replies=True,
        )
    ]
    print(f"follower_tweets\n{follower_tweets}\n\n")
    return follower_tweets

@retry(wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(5))
def tweet_reply(api, follower_tweet_id, tweet):
    return api.update_status(status=tweet,
                             in_reply_to_status_id=follower_tweet_id,
                             auto_populate_reply_metadata=True)

if __name__ == "__main__":
    # auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    # auth.set_access_token(access_token, access_token_secret)
    # api = tweepy.API(auth)
    # follower_tweets = get_latest_tweets_by_followers(api)
    
    # note: must call initialize_twitter_post_log.py before first run
    df = pd.read_csv(FILE_PATH, encoding='utf-8')
    
    # get index of first row without a timestamp
    df_empty_timestamp = df[df.timestamp.isnull()]
    if df_empty_timestamp.empty:
        raise Exception("No more records with empty timestamps! Time to reseed the table!")
    i = df_empty_timestamp.index[0]
    print(f"{i=}")
    
    # generate the prompt
    random.seed(i.item())
    flavor = FLAVOR.substitute(
        aesthetic=random.choice(AESTHETIC),
        style=random.choice(STYLE),
        medium=random.choice(MEDIUM),
        artist=random.choice(ARTIST),
    )
    prompt = PROMPT.substitute(
        quote=df.quote[i],
        flavor=flavor,
    )

    if len(prompt) > PROMPT_MAX_LENGTH:
        print(f"Original prompt had length {len(prompt)} and was truncated to length {PROMPT_MAX_LENGTH}")
        print(f"Original prompt: {prompt}")
        prompt = prompt[:PROMPT_MAX_LENGTH]
        print(f"Truncated prompt: {prompt}")
    
    print(f"{prompt=}")
    print(f"{len(prompt)=}")
    
    # call out to DALLE
    dalle = Dalle2(DALLE_SESSION_BEARER_TOKEN)
    # generations = dalle.generate(prompt)
    # generations = dalle.generate_and_download(prompt, 1, 'img')
    
    sys.exit(1)
    print(f"{generations=}")

    # update record
    df.at[i, 'timestamp'] = pd.Timestamp.utcnow()
    df.at[i, 'image_prompt'] = prompt
    # add flavor!
    # df.at[i, 'image_file'] = prompt
    # df.at[i, 'image_file_upscaled'] = prompt
    # df.at[i, 'image_file_upscaled'] = prompt

    sys.exit(1)
    status = tweet_reply(api, new_follower_tweet[0], new_tweet.text.item())
    df.at[i, 'tweet_id'] = status.id_str
    # df.at[i, 'tweet_link'] = prompt

    # save file with updated record
    df.to_csv(FILE_PATH, index=False, encoding='utf-8')
    
    print(f"\nupdated row {i} in {FILE_PATH}")
    print(f"{df.iloc[i]}")
    print(42*'-' + '\nScript succeeded!')
