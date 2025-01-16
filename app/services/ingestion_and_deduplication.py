# Ingest a batch of tweets
def ingest_tweets(tweets):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        for tweet in tweets:
            vector = embeddings.generate(tweet["content"])
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