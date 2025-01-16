from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import langchain
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


load_dotenv()
# Api credentials
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Initialize the  API client
llm = ChatGoogleGenerativeAI(model="gemini-pro" , api_key=GOOGLE_API_KEY)

summarization_prompt = PromptTemplate(
    input_variables=["content"],
    template="Summarize the following tweet content: {content}"
)
sentiment_prompt = PromptTemplate(
    input_variables=["content"],
    template="Analyze the sentiment of this tweet: {content}"
)
categorization_prompt = PromptTemplate(
    input_variables=["content"],
    template="Categorize this tweet into predefined tags (e.g., airdrop, project update, news): {content}"
)
summarization_chain = LLMChain(llm=llm, prompt=summarization_prompt)
sentiment_chain = LLMChain(llm=llm, prompt=sentiment_prompt)
categorization_chain = LLMChain(llm=llm, prompt=categorization_prompt)


# Utility function for hashtag extraction
def extract_hashtags(content):
    return [word for word in content.split() if word.startswith("#")]

# Advanced processing
def process_tweet_content(content):
    try:
        summary = summarization_chain.run({"content": content})
        sentiment = sentiment_chain.run({"content": content})
        categories = categorization_chain.run({"content": content})
        return summary.strip(), sentiment.strip().split(", "), categories.strip().split(", ")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during LLM processing: {str(e)}")
