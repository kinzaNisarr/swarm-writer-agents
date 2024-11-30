# from typing import Dict, Any
# from pydantic import BaseModel, Field
# from typing import Optional

# import os
# from datetime import datetime
# import requests
# import json
# from .base_agent import BaseAgent


# class HotelsInput(BaseModel):
#     q: str = Field(..., description="Location of the hotel (City/Country)")
#     check_in_date: str = Field(..., description="Check-in date in YYYY-MM-DD format")
#     check_out_date: str = Field(..., description="Check-out date in YYYY-MM-DD format")
#     sort_by: Optional[str] = Field(
#         "rating", description="Sorting criteria, e.g., rating, price"
#     )
#     adults: Optional[int] = Field(1, description="Number of adults. Default is 1.")
#     children: Optional[int] = Field(0, description="Number of children. Default is 0.")
#     rooms: Optional[int] = Field(1, description="Number of rooms. Default is 1.")
#     hotel_class: Optional[str] = Field(None, description="Hotel class, e.g., 2, 3, 4")


# class HotelAgent(BaseAgent):
#     def __init__(self):
#         super().__init__(
#             name="HotelAgent",
#             instructions="""Search and analyze hotel options.
#             Consider: price, location, amenities, and guest ratings.
#             Provide detailed hotel information with images and booking links.
#             Return results in HTML format with pricing, amenities, and location details.""",
#         )
#         self.serpapi_key = os.getenv("SERPAPI_API_KEY")

#     async def run(self, messages: list) -> Dict[str, Any]:
#         """Search and analyze hotel options"""
#         print("🏨 HotelAgent: Searching for hotels")

#         # Convert the content to JSON using json.loads()
#         try:
#             search_params_json = json.loads(messages[-1]["content"])
#             search_params = HotelsInput(
#                 **search_params_json
#             )  # Validate and parse using Pydantic model
#         except json.JSONDecodeError as e:
#             raise ValueError(f"Invalid JSON format: {str(e)}")

#         # Perform the hotel search
#         hotels = self.search_hotels(search_params)

#         # Directly return the parsed hotel data
#         return self._parse_hotel_data(hotels)

#     def search_hotels(self, params: HotelsInput) -> Dict[str, Any]:
#         search_params = {
#             "api_key": self.serpapi_key,
#             "engine": "google_hotels",
#             "hl": "en",
#             "gl": "us",
#             "q": params.q,
#             "check_in_date": params.check_in_date,
#             "check_out_date": params.check_out_date,
#             "currency": "USD",
#             "adults": params.adults,
#             "children": params.children,
#             "rooms": params.rooms,
#             "sort_by": params.sort_by,
#             "hotel_class": params.hotel_class,
#         }
#         print(f"\n ===>>> Searching for hotels with parameters {search_params} \n ====")
#         try:
#             response = requests.get("https://serpapi.com/search", params=search_params)
#             response.raise_for_status()  # Raise an exception for HTTP errors
#             print(
#                 "\n\n ==>Hotel search response:", response.json()
#             )  # Print JSON response
#             return response.json()
#         except requests.exceptions.HTTPError as http_err:
#             print(f"HTTP error occurred: {http_err}")
#             print(f"Response content: {response.content}")
#             raise
#         except Exception as err:
#             print(f"Other error occurred: {err}")
#             raise

#     def _parse_hotel_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
#         """Parse hotel data from the API response"""
#         properties = data.get("properties", [])
#         recommended_hotels = []
#         for hotel in properties:
#             recommended_hotels.append(
#                 {
#                     "name": hotel.get("name"),
#                     "rating": hotel.get("overall_rating"),
#                     "price_per_night": hotel.get("rate_per_night", {}).get("lowest"),
#                     "total_price": hotel.get("total_rate", {}).get("lowest"),
#                     "location": hotel.get("description"),
#                     "amenities": hotel.get("amenities"),
#                     "image_url": hotel.get("images", [{}])[0].get("thumbnail"),
#                     "booking_url": hotel.get("link"),
#                 }
#             )
#         return {
#             "recommended_hotels": recommended_hotels,
#             "search_timestamp": datetime.now().strftime("%Y-%m-%d"),
#             "number_of_options": len(recommended_hotels),
#         }


from typing import Dict, Any
from .base_agent import BaseAgent
import os
from datetime import datetime
import requests


class CityResolverAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CityResolverAgent",
            instructions="You are a helpful assistant that identifies cities based on airport codes.",
        )

    def get_city_from_airport_code(self, airport_code: str) -> str:
        """Query Ollama model to get city from airport code"""
        prompt = f"What city is represented by the airport code {airport_code}?"
        try:
            response = self._query_ollama(prompt)
            return response.strip()
        except Exception as e:
            print(f"Error resolving city from airport code: {str(e)}")
            return "Unknown City"


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
        self.city_resolver_agent = (
            CityResolverAgent()
        )  # Instance of the CityResolverAgent

    async def run(self, messages: list) -> Dict[str, Any]:
        """Search and analyze hotel options"""
        print("🏨 HotelAgent: Searching for hotels")

        search_params = eval(messages[-1]["content"])
        print(f"\n\n ===> Hotel search parameters: {messages}")
        # Get the actual city name from the airport code
        destination_airport_code = search_params.get("location", "")
        if destination_airport_code:
            search_params["location"] = (
                self.city_resolver_agent.get_city_from_airport_code(
                    destination_airport_code
                )
            )

        hotels = self.search_hotels(search_params)

        # Directly return the parsed hotel data
        return self._parse_hotel_data(hotels)

    def search_hotels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        search_params = {
            "api_key": self.serpapi_key,
            "engine": "google_hotels",
            "hl": "en",
            "gl": "us",
            # "q": params.get("location", ""),
            "q": "hotels in" + params.get("location", ""),
            # "q": params.q,
            "check_in_date": params.get("check_in", ""),
            "check_out_date": params.get("check_out", ""),
            "currency": "USD",
            "adults": params.get("adults", 1),
            "children": params.get("children", 0),
            "rooms": params.get("rooms", 1),
            "sort_by": params.get("sort_by", ""),
            "hotel_class": params.get("hotel_class", ""),
        }
        print(f"\n ===>>> Searching for hotels with parameters {search_params} \n ====")
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
