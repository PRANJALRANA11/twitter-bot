from fastapi import FastAPI, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from scipy.spatial.distance import cosine
import tweepy  
import os
from app.utils.db import get_db_connection 
from app.utils.process_tweet import extract_hashtags,process_tweet_content
from app.models.tweets import Tweet, ProcessedTweet
from psycopg2.extras import Json
from typing import List
from datetime import datetime

app = FastAPI()

# Twitter API credentials
TWITTER_API_KEY = "soqMa6H9JNE4zRukGwpv9OJE4"
TWITTER_API_SECRET ="eEqN6tnvuM5v1REOprksX8PRoyIvXy9SBMu8t7qmplAHM0sEFH"
TWITTER_ACCESS_TOKEN = "1680085162456150016-ZJ5rV3fXdSH7H4qPKWBS0IAfA6Jfch"
TWITTER_ACCESS_SECRET = "cpOAZg4ihXxw57XkfpTmToL47m9Au6wcleduvqD2RYttS"

# Gemini API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GOOGLE_API_KEY = "AIzaSyA5gagkPMgMMYNLYQx0Mt6dVEsN8EQasjw"
print("Configuring Google API")
# genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the API client
llm = ChatGoogleGenerativeAI(model="gemini-pro" , api_key=GOOGLE_API_KEY )
genai.configure(api_key=GOOGLE_API_KEY)
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
)
twitter_api = tweepy.API(auth)

print("API clients initialized successfully")

def ingest_tweets(tweets):
    connection = None
    try:
        print(f"Starting tweet ingestion for {len(tweets)} tweets")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tweets (
            id SERIAL PRIMARY KEY,
            tweet_id BIGINT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            embedding FLOAT8[] NOT NULL,
            author_username VARCHAR(255),
            author_id VARCHAR(255),
            hashtags TEXT[],
            summary TEXT,
            tone TEXT,
            categories TEXT[],
            timestamp TIMESTAMP NOT NULL,
            metadata JSONB,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(create_table_query)
        connection.commit()
        print("Table 'tweets' created or already exists.")
        
        for index, tweet in enumerate(tweets):
            print(f"Processing tweet {index + 1}/{len(tweets)}")
            print(f"Tweet content: {tweet['content'][:100]}...")  # Print first 100 chars
            
            vector = genai.embed_content(model="models/text-embedding-004", content=tweet["content"])
    
            print(f"Generated embedding vector of length {len(vector)}")
            
            cursor.execute("SELECT id, tweet_id, embedding, hashtags FROM tweets")
            rows = cursor.fetchall()
            print(f"Found {len(rows)} existing tweets to compare against")

            for row in rows:
                existing_id, tweet_id, existing_vector, existing_hashtags = row
                similarity = 1 - cosine(vector["embedding"], existing_vector)
                print(f"Already stored tweet ID {tweet['tweet_id']} is simillar to new tweet ID {tweet_id} with similarity: {similarity}")

                if similarity >= 0.85:
                    print(f"High similarity found ({similarity}) with tweet ID {tweet_id}")
                    new_hashtags = list(set(existing_hashtags + extract_hashtags(tweet["content"])))
                    summary, sentiment, categories = process_tweet_content(tweet["content"])
                    print(f"Generated summary: {summary[:100]}...")
                    print(f"Sentiment: {sentiment}")
                    print(f"Categories: {categories}")
                    
                    cursor.execute(
                        """
                        UPDATE tweets
                        SET content = %s, embedding = %s, hashtags = %s, summary = %s, tone = %s, categories = %s, last_updated = %s
                        WHERE id = %s
                        """,
                        (tweet["content"], vector['embedding'], new_hashtags, summary, sentiment, categories, datetime.utcnow(), existing_id),
                    )
                    connection.commit()
                    print(f"Updated existing tweet ID {existing_id}")
                    break
            else:
                print("No similar tweets found, creating new entry")
                hashtags = extract_hashtags(tweet["content"])
                summary, sentiment, categories = process_tweet_content(tweet["content"])
                print(f"New tweet processing results:")
                print(f"- Hashtags: {hashtags}")
                print(f"- Summary: {summary[:100]}...")
                print(f"- Sentiment: {sentiment}")
                print(f"- Categories: {categories}")
                
                cursor.execute(
                    """
                    INSERT INTO tweets (tweet_id, content, embedding, author_username, author_id, hashtags, summary, tone, categories, timestamp, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        tweet["tweet_id"],
                        tweet["content"],
                        vector['embedding'],
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
                print(f"Successfully inserted new tweet ID {tweet['tweet_id']}")

    except Exception as e:
        print(f"Error in ingest_tweets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed")
            
@app.get("/fetch-and-ingest")
def fetch_and_ingest():
    try:
        print("Starting fetch-and-ingest process")
        tweets = []
        api = tweepy.Client(bearer_token="AAAAAAAAAAAAAAAAAAAAADrlyAEAAAAARM%2B0AmTRy%2BTLlmr%2FimxgwvozrIU%3DnNBo1qO1ZE3oE26jMRrPms6xWEBFO4qLz1M1uaPZmhmVuoaODl")
        
        print("Fetching tweets from Twitter API")
        public_tweets = api.search_recent_tweets(
            query="python",
            max_results=10,
            tweet_fields=['created_at', 'public_metrics'],
            user_fields=['username', 'id']
        )
        
        print(f"Retrieved {len(public_tweets.data) if public_tweets.data else 0} tweets")
        
        for status in public_tweets.data:
            print(f"Processing tweet ID: {status.id}")
            tweets.append({
                "tweet_id": status.id,
                "content": status.text,
                "author": {
                    "username": "pranjal",
                    "id": "123",
                },
                "timestamp": status.created_at,
                "metadata": {
                    "retweet_count": status.public_metrics['retweet_count'],
                    "favorite_count": status.public_metrics['like_count'],
                },
            })
            print(f"Tweet ID: {status.id}, Tweet Content {status.text} processed")

        print(f"Starting ingestion of {len(tweets)} tweets")
        ingest_tweets(tweets)
        print("Tweet ingestion completed successfully")
        return {"message": "Tweets fetched and ingested successfully."}
    except Exception as e:
        print(f"Error in fetch-and-ingest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tweets: {str(e)}")

@app.get("/processed-tweets", response_model=List[ProcessedTweet])
def get_processed_tweets():
    try:
        print("Fetching processed tweets from database")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT tweet_id, content, summary, hashtags, tone, categories, timestamp FROM tweets")
        rows = cursor.fetchall()
        print(f"Retrieved {len(rows)} processed tweets")
        
        processed_tweets = [
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
        print("Successfully processed tweet data")
        return processed_tweets

    except Exception as e:
        print(f"Error in get_processed_tweets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed")