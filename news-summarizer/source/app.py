import streamlit as st
import json
from news_fetcher import NewsFetcher
from summarizer import NewsSummarizer
from filter_engine import ArticleFilter
from location_service import LocationService
from datetime import datetime
from typing import List
import os


def load_config():
    config_file = "config/user_preferences.json"
    os.makedirs("config", exist_ok=True)

    if not os.path.exists(config_file):
        default_config = {"interests": ["politics", "technology", "sports", "weather"]}
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)

    with open(config_file, "r") as f:
        return json.load(f)


def save_preferences(interests: List[str]):
    os.makedirs("config", exist_ok=True)
    preferences = {"interests": interests}
    with open("config/user_preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)


def main():
    st.set_page_config(page_title="Local News Summarizer", layout="wide")
    st.title("🗞️ AI-Powered Local News Summarizer")

    # Initialize components
    location_service = LocationService()
    fetcher = NewsFetcher()
    summarizer = NewsSummarizer()
    filter_engine = ArticleFilter()

    # Get user's location
    location = location_service.get_location()

    # Load current preferences
    preferences = load_config()

    # Sidebar for preferences
    with st.sidebar:
        st.header("📋 Preferences")

        # Display detected location
        st.subheader("📍 Your Location")
        st.write(f"City: {location['city']}")
        st.write(f"State: {location['state']}")
        st.write(f"Country: {location['country']}")

        # Interests selector
        available_interests = [
            "politics",
            "technology",
            "sports",
            "weather",
            "education",
            "health",
            "business",
            "entertainment",
        ]
        interests = st.multiselect(
            "Select your interests",
            available_interests,
            default=preferences["interests"],
        )

        # Time range selector
        time_range = st.radio("Time range", ["today", "week", "month"], index=1)

        if st.button("Save Preferences"):
            save_preferences(interests)
            st.success("Preferences saved!")

    # Main content
    if not interests:
        st.warning("Please select at least one interest in the sidebar.")
        return

    with st.spinner("Fetching local news..."):
        articles = fetcher.fetch_news(location)
        filtered_articles = filter_engine.filter_articles(
            articles, interests, time_range
        )

    if not filtered_articles:
        st.info(
            "No articles found matching your interests. Try adjusting your filters."
        )
        return

    # Display articles
    for article in filtered_articles:
        with st.expander(f"📰 {article['title']}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Source:** {article['source']}")
                st.markdown(
                    f"**Published:** {article['published'].strftime('%Y-%m-%d %H:%M')}"
                )

                with st.spinner("Generating summary..."):
                    summary = summarizer.generate_summary(article)
                st.markdown("### Summary")
                st.write(summary)

            with col2:
                st.markdown("### Original Article")
                st.link_button("Read Full Article", article["link"])


if __name__ == "__main__":
    main()
