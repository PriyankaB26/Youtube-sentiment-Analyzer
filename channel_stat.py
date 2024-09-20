from flask import Flask, render_template, request, redirect, flash, url_for
from googleapiclient.discovery import build
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# YouTube API key
api_key = 'AIzaSyBqUeaTyMK3LsGYklFRK0VNnG7NvFabhPc'
youtube = build('youtube', 'v3', developerKey=api_key)

# Helper functions
def extract_channel_id(url):
    patterns = {
        'channel': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
        'custom': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)',
        'playlist': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=([a-zA-Z0-9_-]+)',
        'video': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            if key == 'channel':
                return match.group(1)
            elif key == 'custom':
                return get_channel_id_from_custom_url(match.group(1))
            elif key == 'playlist':
                return get_channel_id_from_playlist(match.group(1))
            elif key == 'video':
                return get_channel_id_from_video(match.group(1))
    return None

def get_channel_id_from_custom_url(username):
    try:
        response = requests.get(f"https://www.youtube.com/@{username}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            channel_id_meta = soup.find('meta', {'itemprop': 'channelId'})
            if channel_id_meta and channel_id_meta['content']:
                return channel_id_meta['content']
    except Exception as e:
        print(f"Error scraping custom URL {username}: {e}")
    return None

def get_channel_id_from_playlist(playlist_id):
    try:
        response = youtube.playlists().list(part="snippet", id=playlist_id).execute()
        return response['items'][0]['snippet']['channelId'] if 'items' in response else None
    except Exception as e:
        print(f"Error fetching channel from playlist: {e}")
    return None

def get_channel_id_from_video(video_id):
    try:
        response = youtube.videos().list(part="snippet", id=video_id).execute()
        return response['items'][0]['snippet']['channelId'] if 'items' in response else None
    except Exception as e:
        print(f"Error fetching channel from video: {e}")
    return None

def get_channel_stats(channel_id):
    try:
        response = youtube.channels().list(
            part="snippet,contentDetails,statistics", id=channel_id
        ).execute()
        data = response['items'][0] if 'items' in response else None
        if data:
            return {
                'Channel_name': data['snippet']['title'],
                'Subscribers': data['statistics'].get('subscriberCount', 0),
                'Views': data['statistics'].get('viewCount', 0),
                'Total_videos': data['statistics'].get('videoCount', 0),
                'playlist_id': data['contentDetails']['relatedPlaylists'].get('uploads', None),
                'Created_date': data['snippet']['publishedAt'][:10]
            }
    except Exception as e:
        print(f"Error fetching channel stats: {e}")
    return None

def get_profile_picture(channel_id):
    try:
        response = youtube.channels().list(part="snippet", id=channel_id).execute()
        return response['items'][0]['snippet']['thumbnails']['high']['url'] if 'items' in response else None
    except Exception as e:
        print(f"Error fetching profile picture: {e}")
    return None

def get_banner_image(channel_id):
    try:
        response = youtube.channels().list(part="brandingSettings", id=channel_id).execute()
        return response['items'][0]['brandingSettings']['image']['bannerExternalUrl'] if 'items' in response else None
    except Exception as e:
        print(f"Error fetching banner image: {e}")
    return None

def get_video_ids(playlist_id):
    if not playlist_id:
        return []
    video_ids = []
    try:
        request = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50).execute()
        video_ids.extend([item['contentDetails']['videoId'] for item in request['items']])
        while 'nextPageToken' in request:
            request = youtube.playlistItems().list(
                part="contentDetails", playlistId=playlist_id, maxResults=50, pageToken=request['nextPageToken']
            ).execute()
            video_ids.extend([item['contentDetails']['videoId'] for item in request['items']])
    except Exception as e:
        print(f"Error fetching video IDs: {e}")
    return video_ids

def get_video_details(video_ids):
    all_video_stats = []
    try:
        for i in range(0, len(video_ids), 50):
            request = youtube.videos().list(
                part="snippet,statistics", id=','.join(video_ids[i:i+50])
            ).execute()
            for video in request.get('items', []):
                video_stats = {
                    'Title': video['snippet']['title'],
                    'Published_date': video['snippet']['publishedAt'][:10],
                    'Views': int(video['statistics'].get('viewCount', 0)),
                    'Likes': int(video['statistics'].get('likeCount', 0)),
                    'Comments': int(video['statistics'].get('commentCount', 0)),
                    'Dislikes': 'N/A',  # Dislike count is not available
                    'Video_ID': video['id'],
                    'Thumbnail': video['snippet']['thumbnails']['default']['url']
                }
                all_video_stats.append(video_stats)
    except Exception as e:
        print(f"Error fetching video details: {e}")
    return all_video_stats

def get_videos_from_channel(channel_id):
    all_videos = []
    try:
        response = youtube.search().list(
            part="snippet", channelId=channel_id, maxResults=50, order="date", type="video"
        ).execute()
        for video in response['items']:
            video_stats = {
                'Title': video['snippet']['title'],
                'Published_date': video['snippet']['publishedAt'][:10],
                'Video_ID': video['id']['videoId'],
                'Thumbnail': video['snippet']['thumbnails']['default']['url'],
                'Views': 0,
                'Likes': 0,
                'Comments': 0,
                'Dislikes': 'N/A'
            }
            all_videos.append(video_stats)
        while 'nextPageToken' in response:
            response = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=50,
                order="date",
                pageToken=response['nextPageToken'],
                type="video"
            ).execute()
            for video in response['items']:
                video_stats = {
                    'Title': video['snippet']['title'],
                    'Published_date': video['snippet']['publishedAt'][:10],
                    'Video_ID': video['id']['videoId'],
                    'Thumbnail': video['snippet']['thumbnails']['default']['url'],
                    'Views': 0,
                    'Likes': 0,
                    'Comments': 0,
                    'Dislikes': 'N/A'
                }
                all_videos.append(video_stats)
    except Exception as e:
        print(f"Error fetching videos from channel: {e}")
    return all_videos

@app.route('/')
def link_page():
    return render_template('link.html')

@app.route('/search', methods=['POST'])
def search():
    channel_url = request.form['channel_url']
    channel_id = extract_channel_id(channel_url)

    if not channel_id:
        flash('Invalid YouTube URL or unable to fetch channel ID. Please try a different URL.', 'danger')
        return redirect(url_for('link_page'))

    profile_pic = get_profile_picture(channel_id)
    banner_image = get_banner_image(channel_id)
    channel_data = get_channel_stats(channel_id)
    
    if not channel_data:
        flash('Failed to retrieve channel information. Please check the URL.', 'danger')
        return redirect(url_for('link_page'))

    video_ids = get_video_ids(channel_data.get('playlist_id')) if channel_data else []
    if not video_ids:
        videos = get_videos_from_channel(channel_id)
    else:
        videos = get_video_details(video_ids)

    # Get detailed stats for all videos if needed
    if not video_ids:
        video_ids = [video['Video_ID'] for video in videos]
        videos = get_video_details(video_ids)

    # Get top 10 videos by views
    top_videos = sorted(videos, key=lambda x: x.get('Views', 0), reverse=True)[:10]

    # Prepare data for charts
    top10_videos_data = {
        'labels': [video['Title'] for video in top_videos],
        'data': [video['Views'] for video in top_videos]
    }

    # Prepare data for number of videos per month chart
    if videos:
        video_df = pd.DataFrame(videos)
        video_df['Published_date'] = pd.to_datetime(video_df['Published_date'])
        monthly_video_counts = video_df.groupby(video_df['Published_date'].dt.to_period('M')).size()
        monthly_videos_data = {
            'labels': monthly_video_counts.index.astype(str).tolist(),
            'data': monthly_video_counts.tolist()
        }
    else:
        monthly_videos_data = {'labels': [], 'data': []}

    return render_template(
        'res.html', 
        profile_pic=profile_pic, 
        banner_image=banner_image, 
        channel_data=channel_data, 
        top10_videos_data=top10_videos_data, 
        monthly_videos_data=monthly_videos_data,
        recent_videos=videos[:5],
        top_videos=top_videos  # Pass top_videos to template
    )

if __name__ == '__main__':
    app.run(debug=True)
