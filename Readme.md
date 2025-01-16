# TWITTER BOT 

## HOW TO SETUP LOCALLY


### Step 1: Clone the Repository

First, you need to clone the FastAPI app repository from GitHub (or another source). Open your terminal or command prompt and run the following command:

```
git clone <repository_url>
```

Replace `<repository_url>` with the actual URL of the FastAPI repository you want to clone.

### Step 2: Navigate to the Project Directory

Once the repository is cloned, navigate to the project folder:

```
cd <project_directory>
```

Replace `<project_directory>` with the folder where the project was cloned.


### Step 3: Set Up a Virtual Environment (Optional but Recommended)

It's a good practice to use a virtual environment to manage dependencies and avoid conflicts with other projects. To set up a virtual environment, run:

```
python -m venv venv
```

This will create a venv directory in your project folder containing the virtual environment.

### Activate the virtual environment:

On Windows:

```
venv\Scripts\activate
```

On macOS/Linux:

```
source venv/bin/activate
```

### Step 4: Install Dependencies

After activating the virtual environment, install the dependencies defined in the requirements.txt file (if it exists) using pip:

```
pip install -r requirements.txt
```


### Step 5: Run the FastAPI App

Once the dependencies are installed, you can run the FastAPI app. If the app uses uvicorn as the ASGI server (which is common with FastAPI), you can start it with the following command:

```
uvicorn app.main:app --reload
```

Open your browser and navigate to `http://127.0.0.1:8000/docs` to access the FastAPI app.



## Design Decisions

### FastAPI Framework:

The application uses FastAPI as the web framework. FastAPI is chosen for its performance (due to asynchronous support), automatic generation of API documentation (Swagger and ReDoc), and type hinting support for faster development.

### Twitter API Integration:

The application integrates with the Twitter API using Tweepy to fetch recent tweets about "India." This allows the app to automatically collect tweets that match a given search term, providing dynamic and up-to-date content for ingestion.

### Tweet Ingestion:

Tweet ingestion is handled by the ingest_tweets function. The data is ingested into a database or a processing pipeline. 

### Tweet Processing:

Each tweet fetched is processed and formatted into a structured dictionary containing:
tweet_id: A unique identifier for the tweet.
content: The content of the tweet. (Currently hardcoded, but should ideally come from status.text).
author: A dictionary with the username and user ID of the tweet author.
timestamp: The time the tweet was created.
metadata: Retweet and favorite counts.

### Scalability:

The application currently fetches a maximum of 10 tweets at a time (max_results=10), which is a simple starting point for API integration. In a production environment, this would likely need to be adjusted based on expected traffic, with options for pagination or batching for scalability.



A single GET endpoint (/fetch-and-ingest) is used to trigger the tweet-fetching and ingestion process. This design is simple, but it might not scale well with high-frequency requests. A more complex design could involve job queues or scheduling to handle tweet ingestion asynchronously in the background.



PROBLEMS FACED
1. RATE LIMITS of twitter and gemini if you see empty summary in proceesed items it is due to these reasons . which can be solved with paid api subs.