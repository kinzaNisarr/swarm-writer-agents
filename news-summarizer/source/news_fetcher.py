import json
from typing import List, Dict
from datetime import datetime
from dateutil import parser
import requests
import re
import os
from time import sleep
from random import uniform
import pytz
from duckduckgo_search import DDGS


class NewsFetcher:
    def __init__(self, feeds_file: str = "config/news_sources.json"):
        # Ensure config directory exists
        os.makedirs("config", exist_ok=True)

        # Create default config if it doesn't exist
        if not os.path.exists(feeds_file):
            default_feeds = self._get_default_feeds()
            with open(feeds_file, "w") as f:
                json.dump(default_feeds, f, indent=4)

        self.timezone = pytz.UTC

    def _fetch_duckduckgo_news(self, query: str) -> List[Dict]:
        """Fetch news using DuckDuckGo search"""
        articles = []
        try:
            # Initialize DuckDuckGo search API
            ddg_api = DDGS()

            # Perform the search with DuckDuckGo
            print(f"===>Query: {query}")
            results = ddg_api.text(keywords="AI", max_results=5)
            # print(f"===>Results: {results}")
            # Loop through the search results
            for result in results:
                print(f"===>Result: {result.get('title', '')}")
                title = result.get("title", "")
                link = result.get("href", "")
                snippet = result.get("body", "")

                # Check if title and link are present before appending
                if title and link:
                    articles.append(
                        {
                            "title": title,
                            "summary": snippet,
                            "link": link,
                            "published": datetime.now(self.timezone),
                            "source": "DuckDuckGo",
                            "category": "general",
                        }
                    )

            # Return a formatted list of articles or a message if no results
            if articles:
                return articles
            else:
                print(f"No news results found for '{query}'.")
                return []

        except Exception as e:
            print(f"Error fetching news from DuckDuckGo: {str(e)}")
            return []

    def _get_default_feeds(self) -> Dict:
        """Get default search queries for general news topics"""
        return {
            "default": [
                {"name": "General News", "query": "latest news", "category": "general"},
                {
                    "name": "Technology News",
                    "query": "latest technology news",
                    "category": "technology",
                },
                {
                    "name": "Business News",
                    "query": "latest business news",
                    "category": "business",
                },
                {
                    "name": "Sports News",
                    "query": "latest sports news",
                    "category": "sports",
                },
                {
                    "name": "Health News",
                    "query": "latest health news",
                    "category": "health",
                },
            ]
        }

    def _get_location_query(self, location: Dict) -> str:
        """Generate a search query based on location"""
        city = location["city"].replace(" ", "+")
        state = location["state"]
        return f"{city} {state} local news"

    def fetch_news(self, location: Dict) -> List[Dict]:
        """Fetch news using DuckDuckGo search queries"""
        articles = []

        # 1. Use location-specific search query
        try:
            location_query = self._get_location_query(location)
            articles.extend(self._fetch_duckduckgo_news(location_query))
            sleep(uniform(1, 2))  # Adding a delay to avoid hitting rate limits
        except Exception as e:
            print(f"Error fetching location-specific news: {str(e)}")

        # 2. Use default search queries if not enough articles
        if len(articles) < 10:
            try:
                default_feeds = self._get_default_feeds()["default"]
                for feed in default_feeds:
                    query = feed["query"]
                    articles.extend(self._fetch_duckduckgo_news(query))
                    sleep(uniform(1, 2))  # Adding a delay between queries
            except Exception as e:
                print(f"Error fetching default news: {str(e)}")

        # 3. Sort by date and remove duplicates
        unique_articles = self._remove_duplicates(articles)
        sorted_articles = sorted(
            unique_articles, key=lambda x: x["published"], reverse=True
        )

        return sorted_articles

    def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            title_key = article["title"].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)

        return unique_articles


# import feedparser
# import json
# from typing import List, Dict
# from datetime import datetime
# from dateutil import parser
# import requests
# import re
# import os
# from time import sleep
# from random import uniform
# import pytz


# class NewsFetcher:
#     def __init__(self, feeds_file: str = "config/news_sources.json"):
#         # Ensure config directory exists
#         os.makedirs("config", exist_ok=True)

#         # Create default config if it doesn't exist
#         if not os.path.exists(feeds_file):
#             default_feeds = self._get_default_feeds()
#             with open(feeds_file, "w") as f:
#                 json.dump(default_feeds, f, indent=4)

#         # Load the feeds
#         with open(feeds_file, "r") as f:
#             self.feeds = json.load(f)

#         # Common headers for requests
#         self.headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#         }

#         self.timezone = pytz.UTC

#     def _get_default_feeds(self) -> Dict:
#         """Get default RSS feeds for major news sources"""
#         return {
#             "default": [
#                 {
#                     "name": "Reuters US News",
#                     "url": "https://www.reutersagency.com/feed/?best-topics=all&post_type=best",
#                     "category": "general",
#                 },
#                 {
#                     "name": "Associated Press",
#                     "url": "https://feeds.apnews.com/apnews",
#                     "category": "general",
#                 },
#             ],
#             "new_york": [
#                 {
#                     "name": "NY Times Local",
#                     "url": "https://rss.nytimes.com/services/xml/rss/nyt/NYRegion.xml",
#                     "category": "local",
#                 }
#             ],
#         }

#     def _parse_date(self, date_str: str) -> datetime:
#         """Parse date string to UTC timezone-aware datetime"""
#         try:
#             dt = parser.parse(date_str)
#             if dt.tzinfo is None:
#                 dt = self.timezone.localize(dt)
#             return dt.astimezone(self.timezone)
#         except:
#             return datetime.now(self.timezone)

#     def _fetch_rss_feed(self, feed: Dict) -> List[Dict]:
#         """Fetch and parse a single RSS feed with error handling"""
#         articles = []
#         try:
#             news_feed = feedparser.parse(feed["url"])
#             for entry in news_feed.entries[:10]:  # Limit to 10 articles per feed
#                 articles.append(
#                     {
#                         "title": entry.title,
#                         "summary": entry.get("summary", ""),
#                         "link": entry.link,
#                         "published": self._parse_date(entry.get("published", "")),
#                         "source": feed["name"],
#                         "category": feed.get("category", "general"),
#                     }
#                 )
#         except Exception as e:
#             print(f"Error fetching from {feed['name']}: {str(e)}")
#         return articles

#     def _fetch_google_news(self, location: Dict) -> List[Dict]:
#         """Fetch news from Google News RSS feed"""
#         articles = []
#         city = location["city"].replace(" ", "+")
#         city = "Spokane"  # Remove special characters
#         state = location["state"]

#         # Google News RSS feed URL for local news
#         url = f"https://news.google.com/rss/search?q={city}+{state}+local+news&hl=en-US&gl=US&ceid=US:en"

#         try:
#             feed = feedparser.parse(url)
#             for entry in feed.entries[:10]:
#                 articles.append(
#                     {
#                         "title": entry.title,
#                         "summary": entry.description,
#                         "link": entry.link,
#                         "published": self._parse_date(entry.published),
#                         "source": "Google News",
#                         "category": "local",
#                     }
#                 )
#         except Exception as e:
#             print(f"Error fetching from Google News: {str(e)}")

#         return articles

#     def _get_location_feeds(self, location: Dict) -> List[Dict]:
#         """Get RSS feeds for a specific location"""
#         # Convert state to lowercase for matching
#         state_lower = location["state"].lower().replace(" ", "_")
#         city_lower = location["city"].lower().replace(" ", "_")

#         # Try to find feeds for the specific location
#         feeds = self.feeds.get(f"{city_lower}_{state_lower}", [])
#         if not feeds:
#             feeds = self.feeds.get(city_lower, [])
#         if not feeds:
#             feeds = self.feeds.get("default", [])

#         return feeds

#     def fetch_news(self, location: Dict) -> List[Dict]:
#         """Fetch news from multiple sources with fallback options"""
#         articles = []

#         # 1. Try location-specific RSS feeds
#         location_feeds = self._get_location_feeds(location)
#         for feed in location_feeds:
#             articles.extend(self._fetch_rss_feed(feed))
#             sleep(uniform(1, 2))  # Random delay between requests

#         # 2. Try Google News as a fallback
#         if len(articles) < 10:
#             articles.extend(self._fetch_google_news(location))

#         # 3. If still no articles, use default feeds
#         if len(articles) < 5:
#             default_feeds = self._get_default_feeds()["default"]
#             for feed in default_feeds:
#                 articles.extend(self._fetch_rss_feed(feed))
#                 sleep(uniform(1, 2))

#         # Sort by date and remove duplicates
#         unique_articles = self._remove_duplicates(articles)
#         return sorted(unique_articles, key=lambda x: x["published"], reverse=True)

#     def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
#         """Remove duplicate articles based on title similarity"""
#         seen_titles = set()
#         unique_articles = []

#         for article in articles:
#             title_key = article["title"].lower()
#             if title_key not in seen_titles:
#                 seen_titles.add(title_key)
#                 unique_articles.append(article)

#         return unique_articles
