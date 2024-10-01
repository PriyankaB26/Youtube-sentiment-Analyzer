from flask import Flask, render_template, request, redirect, flash, url_for
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib
from matplotlib import font_manager
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

matplotlib.use('Agg')

# Set font for charts
font_path = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')[0]
plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()

app = Flask(__name__)
app.secret_key = 'your_secret_key'
# YouTube API key
api_key = 'AIzaSyAkhdibQTJQCw5LLcPVrd2ZTexri56WeUM'
youtube = build('youtube', 'v3', developerKey=api_key)

class YouTubeAnalyzer:
    def __init__(self, url):
        self.channel_id = self.extract_channel_id(url)

    def extract_channel_id(self, url):
        patterns = {
            'channel': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
            'custom': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)',
            'playlist': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=([a-zA-Z0-9_-]+)',
            'video': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)'
        }
        print(f"Extracting channel ID from URL: {url}")  # For debugging

        for key, pattern in patterns.items():
            match = re.search(pattern, url)
            if match:
                if key == 'channel':
                    return match.group(1)
                elif key == 'custom':
                    return self.get_channel_id_from_custom_url(match.group(1))
                elif key == 'playlist':
                    return self.get_channel_id_from_playlist(match.group(1))
                elif key == 'video':
                    return self.get_channel_id_from_video(match.group(1))

        return None

    def get_channel_id_from_custom_url(self, username):
        try:
            response = requests.get(f"https://www.youtube.com/@{username}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find the channel ID from meta tag
                channel_id_meta = soup.find('meta', {'itemprop': 'channelId'})
                if channel_id_meta and channel_id_meta['content']:
                    return channel_id_meta['content']
                
                # Fallback: Try to find it from the canonical link
                canonical_link = soup.find('link', {'rel': 'canonical'})
                if canonical_link and '/channel/' in canonical_link['href']:
                    return canonical_link['href'].split('/channel/')[1]
            
            # If the channel ID is not found
            print(f"Error: Could not fetch channel ID for custom URL {username}")
            return None
        
        except Exception as e:
            print(f"Error scraping custom URL {username}: {e}")
            return None

    def get_channel_id_from_playlist(self, playlist_id):
        try:
            response = youtube.playlists().list(part="snippet", id=playlist_id).execute()
            return response['items'][0]['snippet']['channelId'] if 'items' in response else None
        except Exception as e:
            print(f"Error fetching channel from playlist: {e}")
        return None

    def get_channel_id_from_video(self, video_id):
        try:
            response = youtube.videos().list(part="snippet", id=video_id).execute()
            return response['items'][0]['snippet']['channelId'] if 'items' in response else None
        except Exception as e:
            print(f"Error fetching channel from video: {e}")
        return None

    def get_channel_stats(self, channel_id):
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

    def get_profile_picture(self, channel_id):
        try:
            response = youtube.channels().list(part="snippet", id=channel_id).execute()
            return response['items'][0]['snippet']['thumbnails']['high']['url'] if 'items' in response else None
        except Exception as e:
            print(f"Error fetching profile picture: {e}")
        return None

    def get_banner_image(self, channel_id):
        try:
            response = youtube.channels().list(part="brandingSettings", id=channel_id).execute()
            return response['items'][0]['brandingSettings']['image']['bannerExternalUrl'] if 'items' in response else None
        except Exception as e:
            print(f"Error fetching banner image: {e}")
        return None

    def get_video_ids(self, playlist_id):
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

    def get_video_details(self, video_ids):
        all_video_stats = []
        try:
            for i in range(0, len(video_ids), 50):
                request = youtube.videos().list(part="snippet,statistics", id=','.join(video_ids[i:i+50])).execute()
                for video in request.get('items', []):
                    all_video_stats.append({
                        'Title': video['snippet']['title'],
                        'Published_date': video['snippet']['publishedAt'],
                        'Views': video['statistics'].get('viewCount', 0),
                        'Comments': video['statistics'].get('commentCount', 0),
                        'Likes': video['statistics'].get('likeCount', 0),
                        'Dislikes': video['statistics'].get('dislikeCount', 0)
                    })
        except Exception as e:
            print(f"Error fetching video details: {e}")
        return all_video_stats

    def get_videos_from_channel(self, channel_id):
        all_videos = []
        try:
            response = youtube.search().list(part="snippet", channelId=channel_id, maxResults=50, order="date", type="video").execute()
            all_videos = [{'Title': video['snippet']['title'], 
                        'Published_date': video['snippet']['publishedAt'], 
                        'Video_ID': video['id']['videoId'],
                        'Thumbnail': video['snippet']['thumbnails']['default']['url']} 
                        for video in response['items']]
            while 'nextPageToken' in response:
                response = youtube.search().list(
                    part="snippet", channelId=channel_id, maxResults=50, order="date", pageToken=response['nextPageToken'], type="video"
                ).execute()
                all_videos.extend([{'Title': video['snippet']['title'], 
                                    'Published_date': video['snippet']['publishedAt'], 
                                    'Video_ID': video['id']['videoId'],
                                    'Thumbnail': video['snippet']['thumbnails']['default']['url']} 
                                for video in response['items']])
        except Exception as e:
            print(f"Error fetching videos from channel: {e}")
        return all_videos

    def plot_to_base64(self, fig):
        img = io.BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()

if __name__ == '__main__':
    app.run(debug=True)
