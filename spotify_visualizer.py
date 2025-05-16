import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Get secrets or env variables
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "user-top-read"

# Spotify Auth
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache",
    show_dialog=True
)

query_params = st.query_params
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

    # Time range selector
    time_range = st.selectbox("Select time range:", {
        "Last 4 weeks": "short_term",
        "Last 6 months": "medium_term",
        "All time": "long_term"
    })

    top_tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)["items"]
    if not top_tracks:
        st.warning("No tracks found. Try selecting a different time range.")
        st.stop()

    # Process track info
    track_names = [track["name"] for track in top_tracks]
    artist_names = [track["artists"][0]["name"] for track in top_tracks]
    popularity = [track["popularity"] for track in top_tracks]
    track_ids = [track["id"] for track in top_tracks]

    df = pd.DataFrame({
        "Track": track_names,
        "Artist": artist_names,
        "Popularity": popularity
    })

    st.subheader("📊 Top Tracks by Popularity")
    fig1 = px.bar(df, x="Track", y="Popularity", color="Artist", title="Top 10 Tracks")
    st.plotly_chart(fig1, use_container_width=True)

    # 🎵 Radar chart: average audio features
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

    # 📈 Popularity line trend
    st.subheader("📈 Popularity Trend")
    line_fig = px.line(df, x="Track", y="Popularity", markers=True)
    st.plotly_chart(line_fig, use_container_width=True)

    # 🧬 Genre Pie Chart
    st.subheader("🥧 Genre Breakdown of Top Artists")
    top_artists = sp.current_user_top_artists(limit=10, time_range=time_range)["items"]
    genre_list = []
    for artist in top_artists:
        genre_list.extend(artist["genres"])

    genre_counts = pd.Series(genre_list).value_counts().head(6)
    pie_fig = px.pie(names=genre_counts.index, values=genre_counts.values, title="Top Artist Genres")
    st.plotly_chart(pie_fig, use_container_width=True)

    # 📝 Raw data download
    with st.expander("📋 View Raw Track Data"):
        st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Track Data CSV", csv, "top_tracks.csv", "text/csv")
