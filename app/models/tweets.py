from pydantic import BaseModel
from datetime import datetime
from typing import List
# Pydantic models
class Tweet(BaseModel):
    tweet_id: str
    content: str
    author: dict
    timestamp: datetime
    metadata: dict

class ProcessedTweet(BaseModel):
    tweet_id: str
    content: str
    summary: str
    hashtags: List[str]
    tone: List[str]
    categories: List[str]
    timestamp: datetime
    
