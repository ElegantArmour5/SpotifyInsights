import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Load Spotify credentials
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "user-top-read"

# Set up Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache",
    show_dialog=True
)

st.set_page_config(page_title="Spotify Visualizer", layout="wide")
st.title("🎧 Spotify Listening Habits Visualizer")

# Step 1: Get query params from URL
query_params = st.query_params
code = query_params.get("code", [None])[0]

# Step 2: Token handling
token_info = None

try:
    if code:
        token_info = sp_oauth.get_access_token(code)
    else:
        token_info = sp_oauth.get_cached_token()

    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])

except Exception as e:
    st.error("🔐 OAuth error: " + str(e))
    st.stop()

# Step 3: No token? Redirect
if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[🔐 Click here to authenticate with Spotify]({auth_url})")
    st.stop()

# Step 4: Use token to create Spotify client
sp = spotipy.Spotify(auth=token_info["access_token"])

# 👤 Display basic user info
user = sp.current_user()
st.sidebar.image(user["images"][0]["url"], width=150) if user.get("images") else None
st.sidebar.write(f"**{user['display_name']}**")
st.sidebar.caption(f"ID: {user['id']}")

# 🎚 Time range selector
time_range_label = st.selectbox("📅 Select time range:", ["Last 4 weeks", "Last 6 months", "All time"])
time_range_map = {
    "Last 4 weeks": "short_term",
    "Last 6 months": "medium_term",
    "All time": "long_term"
}
time_range = time_range_map[time_range_label]

# 🎵 Fetch top tracks
try:
    top_tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)["items"]
except Exception as e:
    st.error("Error fetching top tracks: " + str(e))
    st.stop()

if not top_tracks:
    st.warning("No tracks found. Try a different time range.")
    st.stop()

track_names = [track["name"] for track in top_tracks]
artist_names = [track["artists"][0]["name"] for track in top_tracks]
popularity = [track["popularity"] for track in top_tracks]
track_ids = [track["id"] for track in top_tracks]

df = pd.DataFrame({
    "Track": track_names,
    "Artist": artist_names,
    "Popularity": popularity
})

# 📊 Bar Chart
st.subheader("🎶 Top 10 Tracks")
fig1 = px.bar(df, x="Track", y="Popularity", color="Artist", title="Top Tracks by Popularity")
st.plotly_chart(fig1, use_container_width=True)

# 🧭 Radar Chart: Audio Features
features = sp.audio_features(track_ids)
audio_df = pd.DataFrame(features).dropna()
radar_metrics = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness", "liveness"]
mean_vals = audio_df[radar_metrics].mean()

radar_fig = go.Figure(data=go.Scatterpolar(
    r=mean_vals.values,
    theta=radar_metrics,
    fill='toself',
    name='Average Audio Features'
))
radar_fig.update_layout(title="🧭 Audio Feature Radar", polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
st.plotly_chart(radar_fig, use_container_width=True)

# 📈 Popularity Trend
st.subheader("📈 Popularity Line Chart")
line_fig = px.line(df, x="Track", y="Popularity", markers=True)
st.plotly_chart(line_fig, use_container_width=True)

# 🥧 Genre Pie Chart
top_artists = sp.current_user_top_artists(limit=10, time_range=time_range)["items"]
genre_list = []
for artist in top_artists:
    genre_list.extend(artist["genres"])
genre_counts = pd.Series(genre_list).value_counts().head(6)
pie_fig = px.pie(names=genre_counts.index, values=genre_counts.values, title="🎤 Genre Breakdown")
st.plotly_chart(pie_fig, use_container_width=True)

# 📋 Data Download
with st.expander("📄 View Raw Data"):
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "top_tracks.csv", "text/csv")
