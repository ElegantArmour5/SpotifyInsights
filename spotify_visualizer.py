import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Spotify credentials from environment
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Define scope
SCOPE = "user-top-read"

# Set up OAuth
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    show_dialog=True,
    cache_path=".cache"  # optional: stores the token
)

# Check for cached token
token_info = sp_oauth.get_cached_token()

if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[🔐 Click here to authenticate with Spotify]({auth_url})")

    code_url = st.text_input("Paste the full URL you were redirected to after logging in:")
    if code_url:
        code = code_url.split("?code=")[-1]
        token_info = sp_oauth.get_access_token(code)

if token_info:
    sp = spotipy.Spotify(auth=token_info["access_token"])

    st.title("🎧 Spotify Listening Habits Visualizer")
    st.subheader("Your Top Tracks (Last 6 Months)")

    # Fetch top tracks
    results = sp.current_user_top_tracks(limit=10, time_range="medium_term")
    top_tracks = results["items"]

    track_names = [track["name"] for track in top_tracks]
    artist_names = [track["artists"][0]["name"] for track in top_tracks]
    popularity_scores = [track["popularity"] for track in top_tracks]

    df = pd.DataFrame({
        "Track": track_names,
        "Artist": artist_names,
        "Popularity": popularity_scores
    })

    fig = px.bar(df, x="Track", y="Popularity", color="Artist",
                 title="🎶 Your Top 10 Tracks by Popularity",
                 labels={"Popularity": "Spotify Popularity Score"})

    st.plotly_chart(fig, use_container_width=True)
