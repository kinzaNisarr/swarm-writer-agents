from typing import List, Dict
from datetime import datetime, timedelta
import pytz


class ArticleFilter:
    def __init__(self):
        self.timezone = pytz.UTC
        now = datetime.now(self.timezone)

        self.time_filters = {
            "today": lambda x: self._to_utc(x["published"]).date() == now.date(),
            "week": lambda x: self._to_utc(x["published"]) >= now - timedelta(days=7),
            "month": lambda x: self._to_utc(x["published"]) >= now - timedelta(days=30),
        }

    def _to_utc(self, dt: datetime) -> datetime:
        """Convert datetime to UTC timezone-aware datetime"""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt.astimezone(self.timezone)

    def filter_articles(
        self,
        articles: List[Dict],
        interests: List[str],
        time_range: str = "week",
        max_articles: int = 10,
    ) -> List[Dict]:

        # First filter by time
        time_filter = self.time_filters.get(time_range, self.time_filters["week"])
        time_filtered = [article for article in articles if time_filter(article)]

        # Then filter by interests
        interest_filtered = []
        for article in time_filtered:
            content = f"{article['title']} {article['summary']}".lower()
            if any(interest.lower() in content for interest in interests):
                interest_filtered.append(article)

        # Return the most recent articles up to max_articles
        return sorted(interest_filtered, key=lambda x: x["published"], reverse=True)[
            :max_articles
        ]
