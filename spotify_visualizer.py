import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import plotly.express as px
import os

# Get environment variables from Streamlit Cloud Secrets or local env
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "user-top-read"

# Set up authentication
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache",
    show_dialog=True
)

# Get URL query parameters
query_params = st.query_params()

# Try to get token from cache
token_info = sp_oauth.get_cached_token()

if not token_info and "code" not in query_params:
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[🔐 Click here to authenticate with Spotify]({auth_url})")
    st.stop()

elif not token_info and "code" in query_params:
    code = query_params["code"][0]
    token_info = sp_oauth.get_access_token(code)

if token_info:
    sp = spotipy.Spotify(auth=token_info["access_token"])

    st.title("🎧 Spotify Listening Habits Visualizer")
    st.subheader("Your Top Tracks (Last 6 Months)")

    # Fetch top tracks
    top_tracks = sp.current_user_top_tracks(limit=10, time_range="medium_term")["items"]

    track_names = [track["name"] for track in top_tracks]
    artist_names = [track["artists"][0]["name"] for track in top_tracks]
    popularity = [track["popularity"] for track in top_tracks]

    df_tracks = pd.DataFrame({
        "Track": track_names,
        "Artist": artist_names,
        "Popularity": popularity
    })

    fig = px.bar(df_tracks, x="Track", y="Popularity", color="Artist",
                 title="🎶 Your Top 10 Tracks by Popularity",
                 labels={"Popularity": "Spotify Popularity Score"})

    st.plotly_chart(fig, use_container_width=True)
