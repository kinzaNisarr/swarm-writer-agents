from typing import Dict, Any
from .base_agent import BaseAgent
import os
from datetime import datetime
import requests


class HotelAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="HotelAgent",
            instructions="""Search and analyze hotel options.
            Consider: price, location, amenities, and guest ratings.
            Provide detailed hotel information with images and booking links.
            Return results in HTML format with pricing, amenities, and location details.""",
        )
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")

    async def run(self, messages: list) -> Dict[str, Any]:
        """Search and analyze hotel options"""
        print("🏨 HotelAgent: Searching for hotels")

        search_params = eval(messages[-1]["content"])
        hotels = self.search_hotels(search_params)

        # Directly return the parsed hotel data
        return self._parse_hotel_data(hotels)

    def search_hotels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        search_params = {
            "api_key": self.serpapi_key,
            "engine": "google_hotels",
            "hl": "en",
            "gl": "us",
            "q": params.get("location", ""),
            "check_in_date": params.get("check_in", ""),
            "check_out_date": params.get("check_out", ""),
            "currency": "USD",
            "adults": params.get("adults", 1),
            "children": params.get("children", 0),
            "rooms": params.get("rooms", 1),
            "sort_by": params.get("sort_by", ""),
            "hotel_class": params.get("hotel_class", ""),
        }
        try:
            response = requests.get("https://serpapi.com/search", params=search_params)
            print(
                "\n\n ==>Hotel search response:", response.json()
            )  # Print JSON response
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.content}")
            raise
        except Exception as err:
            print(f"Other error occurred: {err}")
            raise

    def _parse_hotel_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse hotel data from the API response"""
        properties = data.get("properties", [])
        recommended_hotels = []
        for hotel in properties:
            recommended_hotels.append(
                {
                    "name": hotel.get("name"),
                    "rating": hotel.get("overall_rating"),
                    "price_per_night": hotel.get("rate_per_night", {}).get("lowest"),
                    "total_price": hotel.get("total_rate", {}).get("lowest"),
                    "location": hotel.get("description"),
                    "amenities": hotel.get("amenities"),
                    "image_url": hotel.get("images", [{}])[0].get("thumbnail"),
                    "booking_url": hotel.get("link"),
                }
            )
        return {
            "recommended_hotels": recommended_hotels,
            "search_timestamp": datetime.now().strftime("%Y-%m-%d"),
            "number_of_options": len(recommended_hotels),
        }
