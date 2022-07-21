# this file creates initializes twitter_post_log.csv
# with 200 anime quotes and 200 Bible quotes
# the anime quotes were manually extracted from three websites
# the bible quotes were filtered and sampled from a GitHub repo

import itertools
import string
import sys

import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option('display.max_colwidth', None)

from pathlib import Path

FILE_PATH = 'twitter_post_log.csv'
RANDOM_STATE=123

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

def parse_bible_quote(quote):
    source, quote = quote.split(' ', 1)
    return (source.strip(), quote.strip())

def get_bible_quotes():
    bible_quotes = []
    
    # grabbed on July 16, 2022
    # https://github.com/jihongeek/BibleRecommendation/commit/18666e86192c6f45c0218b714a2ed1d268548c3e
    for path in Path('KJV').iterdir():
        with open(path, 'r', encoding='utf8') as f:
            for line in f.readlines():
                source, quote = parse_bible_quote(line)
                
                bible_quotes.append({
                    'bible_or_anime': 'bible',
                    'quote_source': f"{path.stem} {source}",
                    'quote': quote,
                })

    return bible_quotes
 
def filter_bible_quotes(bible_quotes):
    punctuation = set(string.punctuation)
    block_list = [
        'fourth', 'fifth', 'sixth', 'seventh', 'eigth', 'ninth', 'tenth',
        'son', 'sons', 'duke', 'and when', 'begat',
        'wife', 'mother', 'father', 'suburbs', 
    ]

    filters = [
        # not too short
        lambda x: len(x['quote']) > 50,
        
        # not too long
        lambda x: len(x['quote']) < 200,
        
        # doesn't start with a numeral
        lambda x: not x['quote'][0].isnumeric(),
        
        # doesn't start with punctuation (tricky to clean)
        lambda x: x['quote'][0] not in punctuation,
        
        # not too much punctuation
        lambda x: sum(1 for c in x['quote'] if c in punctuation) < 10,
        
        # ends in an incomplete sentence
        lambda x: not x['quote'][-1] in [',', ':', ';'],
        
        # doesn't look like a list of names
        lambda x: x['quote'].lower().count('and') < 2,
        # lambda x: x['quote'].lower().count('son') < 2,
        # lambda x: x['quote'].lower().count('sons') < 2,
        
        # remove non-ASCII characters (probably bad encoding)
        lambda x: all(ord(c) < 128 for c in x['quote']),
        
        # block list
        lambda x: all(y not in x['quote'].lower() for y in block_list),
    ]

    for f in filters:
        bible_quotes = filter(f, bible_quotes)
    
    return list(bible_quotes)

def get_and_filter_bible_quotes():
    bible_quotes = get_bible_quotes()
    filtered_bible_quotes = filter_bible_quotes(bible_quotes)
    return filtered_bible_quotes

# grabbed on July 16, 2022
# https://fictionhorizon.com/best-anime-quotes/
# https://www.scarymommy.com/anime-quotes
# https://www.buzzfeed.com/joshcorrea/best-anime-quotes
# each file was manually formatted into 2-line pairs of (quote, source)
def get_anime_quotes():
    anime_quotes = []

    for file in Path('anime').iterdir():
        with open(file, 'r', encoding='utf8') as f:
            # pair-wise iteration on the file handle, i.e. sequential next(), next()
            # https://stackoverflow.com/a/1657385
            for quote, source in itertools.zip_longest(f, f):
                anime_quotes.append({
                    'bible_or_anime': 'anime',
                    'quote_source': source.replace('–', '').strip(),
                    'quote': quote.strip(),
                })

    return anime_quotes

if __name__ == "__main__":
    if Path(FILE_PATH).is_file():
        sys.exit("aborting initialization because file already exists!")
        pass

    # create anime dataframe
    anime_df = pd.DataFrame(get_anime_quotes(), columns=COLUMNS)

    # anime_df.quote.str.len().describe()
    # Out[210]: 
    # count    200.000000
    # mean     111.610000
    # std       60.352964
    # min       40.000000
    # 25%       68.000000
    # 50%       95.000000
    # 75%      138.000000
    # max      327.000000
    # Name: quote, dtype: float64
    
    # create bible dataframe
    # need sample number as for anime_df, i.e. 200
    # target similar quote length
    bible_df = pd.DataFrame(get_and_filter_bible_quotes(), columns=COLUMNS)
    bible_df = bible_df.sample(200, random_state=RANDOM_STATE)

    print(f"{len(get_bible_quotes())=}")
    print(f"{len(get_and_filter_bible_quotes())=}")

    combined_df = pd.concat([bible_df, anime_df])
    combined_df = combined_df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True) # shuffle in-place
    combined_df.to_csv(FILE_PATH, index=False, encoding='utf-8')

    print(42*'-' + '\nScript succeeded!')
