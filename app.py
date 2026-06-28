import streamlit as st
import pickle
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import gdown

load_dotenv()

api_key = os.environ.get('api_key')


# --- Cached data loading (runs once, not on every interaction) ---
@st.cache_data
def load_movies():
    movie_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    return pd.DataFrame(movie_dict)


@st.cache_resource
def load_similarity():
    # Download similarity.pkl if it doesn't exist (first run only, ~176 MB)
    if not os.path.exists('similarity.pkl'):
        with st.spinner("Downloading similarity matrix... (first time only, ~176 MB)"):
            file_id = "1rENQb_PpyxL1ZOO47cdbfIo2tr4SAFd3"
            gdown.download(f'https://drive.google.com/uc?id={file_id}', 'similarity.pkl', quiet=False)
    return pickle.load(open('similarity.pkl', 'rb'))


movies = load_movies()
similarity = load_similarity()


# --- Cached poster fetch (avoids re-hitting TMDB for the same movie) ---
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US',
            timeout=5,
        )
        data = response.json()

        # Check if API returned an error
        if data.get('success') is False:
            return "placeholder.png"

        img_base_url = "https://image.tmdb.org/t/p/w500"
        poster_path = data.get('poster_path')

        if poster_path:
            return img_base_url + poster_path
        return "placeholder.png"
    except Exception:
        return "placeholder.png"


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_poster = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].id
        recommended_movies_poster.append(fetch_poster(movie_id))
        recommended_movies.append(movies.iloc[i[0]].title)

    return recommended_movies, recommended_movies_poster


st.title('Movie Recommendation System')

select_movie_name = st.selectbox(
    'Select a Movie', movies['title'].values
)

if st.button('Recommend'):
    with st.spinner('Finding movies you might like...'):
        names, posters = recommend(select_movie_name)

    # Display in 5 columns (Netflix style)
    cols = st.columns(5)
    for idx, (name, poster_url) in enumerate(zip(names, posters)):
        with cols[idx]:
            st.image(poster_url, width="stretch")
            st.write(name)