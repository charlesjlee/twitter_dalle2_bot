import os
import random
import string
import tweepy

from dalle2 import Dalle2
from pillow_utils import generate_motivational_meme
from string import Template
from tenacity import retry, wait_exponential, stop_after_attempt

import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option('display.max_colwidth', None)

CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
TOKEN_KEY = os.environ["TOKEN_KEY"]
TOKEN_SECRET = os.environ["TOKEN_SECRET"]
DALLE_BEARER_TOKEN = os.environ["DALLE_BEARER_TOKEN"]

FILE_PATH = 'data/twitter_post_log.csv'

COLUMNS = [
    'timestamp',
    'bible_or_anime',
    'quote',
    'quote_source',
    'image_prompt',
    'image_file',
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
IMAGE_DIR = 'img'

@retry(wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(5))
def upload_media(api, image_path):
    return api.media_upload(image_path)

@retry(wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(5))
def tweet(api, media_ids, status):
    return api.update_status(media_ids=media_ids,status=status)

if __name__ == "__main__":
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(TOKEN_KEY, TOKEN_SECRET)
    api = tweepy.API(auth)

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

    print(f"{flavor=}")
    print(f"{prompt=}")
    print(f"{len(prompt)=}")

    # generate image and save
    dalle = Dalle2(DALLE_BEARER_TOKEN)
    image = dalle.generate_2048_1024(prompt, flavor)
    image_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    image_path = f"{IMAGE_DIR}/{image_name}.png"
    image.save(image_path)
    print(f"Saved stitched image: {image_path}")

    # generate motivational image and save
    motivational_image_path = f"{IMAGE_DIR}/{image_name}_motivational.jpg"
    image = generate_motivational_meme(image_path, df.quote[i], df.quote_source[i])
    image.convert('RGB').save(motivational_image_path)
    print(f"Saved motivational image: {motivational_image_path}")

    # upload media then send tweet
    # todo: media_1's file path is hard-coded in generate_2048_1024()
    media_1 = upload_media(api, f"{os.getcwd()}/root.png")
    media_2 = upload_media(api, image_path)
    media_3 = upload_media(api, motivational_image_path)
    status = tweet(
        api,
        [media_1.media_id_string, media_2.media_id_string, media_3.media_id_string],
        "Bible or anime?",
    )

    # save data file with updated record
    df.at[i, 'timestamp'] = pd.Timestamp.utcnow()
    df.at[i, 'image_prompt'] = prompt
    df.at[i, 'image_file'] = image_path
    df.at[i, 'image_file_motivational'] = motivational_image_path
    df.at[i, 'tweet_id'] = status.id_str
    df.at[i, 'tweet_link'] = f"https://twitter.com/i/web/status/{status.id_str}"
    df.to_csv(FILE_PATH, index=False, encoding='utf-8')

    print(f"\nUpdated row {i} in {FILE_PATH}")
    print(f"{df.iloc[i]}")
    print(42*'-' + '\nScript succeeded!')
