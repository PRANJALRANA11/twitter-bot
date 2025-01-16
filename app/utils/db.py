from fastapi import FastAPI, HTTPException
from typing import List
from gemini import Embeddings  
from scipy.spatial.distance import cosine
import langchain  
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
import tweepy  
import os


app = FastAPI()


@app.get("/fetch-and-ingest")

@app.get("/processed-tweets", response_model=List[ProcessedTweet])


