import geocoder
from typing import Tuple, Dict
import json
import os


class LocationService:
    def __init__(self):
        self.cache_file = "config/location_cache.json"
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def _save_cache(self):
        os.makedirs("config", exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)

    def get_location(self) -> Dict:
        """Get location info using IP geolocation"""
        try:
            # g = geocoder.ip("me")
            # if g.ok:
            #     location = {
            #         "city": g.city,
            #         "state": g.state,
            #         "country": g.country,
            #         "lat": g.lat,
            #         "lng": g.lng,
            #     }
            #     self.cache["last_location"] = location
            #     self._save_cache()

            location = {
                "city": "Los Angeles",
                "state": "CA",
                "country": "US",
                "lat": 34.0522,
                "lng": -118.2437,
            }
            return location
        except Exception as e:
            print(f"Error getting location: {str(e)}")

        # Return cached location if available, otherwise default
        return self.cache.get(
            "last_location",
            {
                "city": "New York",
                "state": "NY",
                "country": "US",
                "lat": 40.7128,
                "lng": -74.0060,
            },
        )
