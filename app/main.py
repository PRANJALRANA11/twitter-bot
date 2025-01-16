from fastapi import FastAPI, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from scipy.spatial.distance import cosine
import tweepy  
import os
from app.utils.db import get_db_connection 
from app.utils.process_tweet import extract_hashtags,process_tweet_content
from app.models.tweets import Tweet, ProcessedTweet
from psycopg2.extras import Json
from typing import List




app = FastAPI()


# Twitter API credentials
TWITTER_API_KEY = "soqMa6H9JNE4zRukGwpv9OJE4"
TWITTER_API_SECRET ="eEqN6tnvuM5v1REOprksX8PRoyIvXy9SBMu8t7qmplAHM0sEFH"
TWITTER_ACCESS_TOKEN = "1680085162456150016-ZJ5rV3fXdSH7H4qPKWBS0IAfA6Jfch"
TWITTER_ACCESS_SECRET = "cpOAZg4ihXxw57XkfpTmToL47m9Au6wcleduvqD2RYttS"
# TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
# TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
# TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
# TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")



# Gemini API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize the  API client
llm = ChatGoogleGenerativeAI(model="gemini-pro" , api_key="AIzaSyA5gagkPMgMMYNLYQx0Mt6dVEsN8EQasjw")
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
)
twitter_api = tweepy.API(auth)


# Ingest a batch of tweets
def ingest_tweets(tweets):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        for tweet in tweets:
            vector = genai.embed_content(model="models/text-embedding-004" , content = tweet["content"])
            cursor.execute("SELECT id, embedding, hashtags FROM tweets")
            rows = cursor.fetchall()

            for row in rows:
                existing_id, existing_vector, existing_hashtags = row
                similarity = 1 - cosine(vector, existing_vector)

                if similarity >= 0.85:
                    new_hashtags = list(set(existing_hashtags + extract_hashtags(tweet["content"])))
                    summary, sentiment, categories = process_tweet_content(tweet["content"])
                    cursor.execute(
                        """
                        UPDATE tweets
                        SET content = %s, embedding = %s, hashtags = %s, summary = %s, tone = %s, categories = %s, last_updated = %s
                        WHERE id = %s
                        """,
                        (tweet["content"], vector.tolist(), new_hashtags, summary, sentiment, categories, datetime.utcnow(), existing_id),
                    )
                    connection.commit()
                    break
            else:
                hashtags = extract_hashtags(tweet["content"])
                summary, sentiment, categories = process_tweet_content(tweet["content"])
                cursor.execute(
                    """
                    INSERT INTO tweets (tweet_id, content, embedding, author_username, author_id, hashtags, summary, tone, categories, timestamp, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        tweet["tweet_id"],
                        tweet["content"],
                        vector.tolist(),
                        tweet["author"].get("username"),
                        tweet["author"].get("id"),
                        hashtags,
                        summary,
                        sentiment,
                        categories,
                        tweet["timestamp"],
                        Json(tweet["metadata"]),
                    ),
                )
                connection.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()
            
            
# Route to fetch tweets from Twitter API and ingest them
@app.get("/fetch-and-ingest")
def fetch_and_ingest():
    try:
        tweets = []
        api = tweepy.Client(bearer_token="AAAAAAAAAAAAAAAAAAAAAE3jyAEAAAAAcxLG3%2BgeylcetpHkZcrO%2FfxjYT4%3DpIqpOc1Oh5B6pvMCMpAY2jWM3IJI0TwFVHDeGqNrIKUrXJKm57")
        public_tweets = api.search_recent_tweets( query="python",
                max_results=10,
                tweet_fields=['created_at', 'public_metrics'],
                user_fields=['username', 'id'],  # Request user information
 )
        # users = {user.id: user for user in public_tweets.includes['users']}
        print("tweets",public_tweets)
        for status in public_tweets.data:
            # author = users[status.author_id]
            tweets.append({
                "tweet_id": status.id,
                "content": status.text,
                "author": {
                    "username":  "pranjal",
                    "id": "123",
                },
                "timestamp": status.created_at,
                "metadata": {
                    "retweet_count": status.public_metrics['retweet_count'],
                    "favorite_count":  status.public_metrics['like_count'],
                },
            })
            print("successfuly fetch")

        ingest_tweets(tweets)
        return {"message": "Tweets fetched and ingested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tweets: {str(e)}")
    

# Route to fetch processed tweets (for validation and logging)
@app.get("/processed-tweets", response_model=List[ProcessedTweet])
def get_processed_tweets():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT tweet_id, content, summary, hashtags, tone, categories, timestamp FROM tweets")
        rows = cursor.fetchall()
        return [
            ProcessedTweet(
                tweet_id=row[0],
                content=row[1],
                summary=row[2],
                hashtags=row[3],
                tone=row[4],
                categories=row[5],
                timestamp=row[6],
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()



