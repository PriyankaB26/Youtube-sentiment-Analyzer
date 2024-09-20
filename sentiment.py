import os
import re
import string
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from datasets import load_dataset

app = Flask(__name__)

# Load and prepare dataset for training
def load_and_prepare_dataset():
    # Load the dataset from Hugging Face
    dataset = load_dataset("prasadsawant7/sentiment_analysis_preprocessed_dataset", split='train')
    # Convert the dataset to a pandas DataFrame
    df = pd.DataFrame(dataset)

    # Print the column names to inspect them
    print(df.columns)

    return df

# Text cleaning function
def clean_text(text):
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    else:
        return ''  # Return empty string for None or NaN values

# Fetch comments from YouTube API
def video_comments(video_id):
    youtube = build('youtube', 'v3', developerKey='AIzaSyCcBrt-UsC9soIxO-y5wu3z8xGzyuu2rIE')
    comments = []
    next_page_token = None
    while True:
        try:
            response = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                textFormat='plainText',
                pageToken=next_page_token
            ).execute()

            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return comments

# Sentiment analysis
def analyze_youtube_video_sentiment(video_id, model, tfidf):
    comments = video_comments(video_id)

    if not comments:
        print("No comments found.")
        return []

    cleaned_comments = [clean_text(comment) for comment in comments]
    X_comments = tfidf.transform(cleaned_comments).toarray()
    predicted_sentiments = model.predict(X_comments)

    positive_percentage, negative_percentage, neutral_percentage = calculate_sentiment_percentages(predicted_sentiments)
    
    results = {
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'neutral_percentage': neutral_percentage,
        'positive_comments': [comments[i] for i, s in enumerate(predicted_sentiments) if s == 2][:10],
        'negative_comments': [comments[i] for i, s in enumerate(predicted_sentiments) if s == 0][:10],
        'neutral_comments': [comments[i] for i, s in enumerate(predicted_sentiments) if s == 1][:10]
    }

    return results

# Calculate sentiment percentages
def calculate_sentiment_percentages(sentiments):
    total_comments = len(sentiments)
    sentiments = np.array(sentiments)

    positive = np.sum(sentiments == 2)
    negative = np.sum(sentiments == 0)
    neutral = np.sum(sentiments == 1)

    if total_comments > 0:
        positive_percentage = (positive / total_comments) * 100
        negative_percentage = (negative / total_comments) * 100
        neutral_percentage = (neutral / total_comments) * 100
    else:
        positive_percentage = 0
        negative_percentage = 0
        neutral_percentage = 0

    return positive_percentage, negative_percentage, neutral_percentage

# Plot sentiment pie chart
def plot_sentiment_pie_chart(positive_percentage, negative_percentage, neutral_percentage, save_path):
    labels = 'Positive', 'Negative', 'Neutral'
    sizes = [positive_percentage, negative_percentage, neutral_percentage]
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    explode = (0.1, 0, 0)  # explode the 1st slice (positive)

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=140)
    plt.title('Sentiment Distribution of YouTube Comments')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save the pie chart to a file
    plt.savefig(save_path)
    plt.close()

# Prepare dataset and train the model
df = load_and_prepare_dataset()
df['cleaned_text'] = df['text'].apply(clean_text)

tfidf = TfidfVectorizer(max_features=5000)
X = tfidf.fit_transform(df['cleaned_text']).toarray()
y = df['labels']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = MultinomialNB()
model.fit(X_train, y_train)

# Routes
@app.route('/')
def index():
    return render_template('sentiment.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    video_id = request.form['video_id']
    if not video_id:
        return redirect(url_for('index'))

    # Perform sentiment analysis and generate pie chart
    results = analyze_youtube_video_sentiment(video_id, model, tfidf)

    # Save the pie chart
    pie_chart_path = os.path.join('static', 'sentiment_pie_chart.png')
    plot_sentiment_pie_chart(results['positive_percentage'], 
                             results['negative_percentage'], 
                             results['neutral_percentage'], 
                             pie_chart_path)

    return render_template('senti_result.html', video_id=video_id, results=results, pie_chart_url=pie_chart_path)

if __name__ == "__main__":
    app.run(debug=True)
