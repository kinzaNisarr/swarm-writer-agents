import json
from typing import Dict, Any
from .base_agent import BaseAgent
import os
from datetime import datetime
import requests
import serpapi


class FlightAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FlightAgent",
            instructions="""Search and analyze flight options.
            Consider: price, duration, airline reputation, and convenience.
            Provide detailed flight information with airline logos and booking links.
            Return results in HTML format with pricing, schedules, and airline details.""",
        )
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")

    async def run(self, messages: list) -> Dict[str, Any]:
        """Search and analyze flight options"""
        print("✈️ FlightAgent: Searching for flights")

        search_params = eval(messages[-1]["content"])
        flights = self.search_flights(search_params)
        # flights.data['best_flights']

        # Directly return the parsed flight data
        return self._parse_flight_data(flights)

    def search_flights(self, params: Dict[str, Any]) -> Dict[str, Any]:
        print("Searching for flights with parameters", params)
        search_params = {
            "api_key": self.serpapi_key,
            "engine": "google_flights",
            "hl": "en",
            "gl": "us",
            "departure_id": params.get("origin", ""),
            "arrival_id": params.get("destination", ""),
            "outbound_date": params.get("departure_date", ""),
            "return_date": params.get("return_date", ""),
            "currency": "USD",
            "adults": params.get("adults", 1),
            "infants_in_seat": params.get("infants_in_seat", 0),
            "stops": "1",
            "infants_on_lap": params.get("infants_on_lap", 0),
            "children": params.get("children", 0),
        }
        try:
            #         try:
            #     search = serpapi.search(params)
            #     results = search.data['best_flights']
            # except Exception as e:
            #     results = str(e)
            # return results
            search = serpapi.search(search_params)
            print("===> Search response:", search)  # Print JSON response
            results = search.data
            # response = requests.get("https://serpapi.com/search", params=search_params)
            # print("===> Response status code:", response.status_code)
            # print("===> Response content:", response.json())  # Print JSON response
            # response.raise_for_status()  # Raise an exception for HTTP errors
            # return results
        except Exception as err:
            results = str(err)
        # except requests.exceptions.HTTPError as http_err:
        #     print(f"HTTP error occurred: {http_err}")
        #     print(f"Response content: {response.content}")

        return results

    def _parse_flight_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse flight data from the API response"""
        # Ensure data is a dictionary and not a string
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
                return {
                    "recommended_flights": [],
                    "search_timestamp": datetime.now().strftime("%Y-%m-%d"),
                    "number_of_options": 0,
                }

        recommended_flights = []

        # Extract flights from 'other_flights' if available
        for flight_option in data.get("other_flights", []):
            for flight in flight_option.get("flights", []):
                recommended_flights.append(
                    {
                        "airline": flight.get("airline"),
                        "flight_number": flight.get("flight_number"),
                        "departure": flight.get("departure_airport", {}).get("time"),
                        "arrival": flight.get("arrival_airport", {}).get("time"),
                        "price": f"${flight_option.get('price')}",
                        "duration": f"{flight.get('duration', 0) // 60}h {flight.get('duration', 0) % 60}m",
                        "logo_url": flight.get("airline_logo"),
                        "booking_url": data.get("search_metadata", {}).get(
                            "google_flights_url"
                        ),
                    }
                )

        # Extract flights from 'flights' if available
        for flight in data.get("flights", []):
            recommended_flights.append(
                {
                    "airline": flight.get("airline"),
                    "flight_number": flight.get("flight_number"),
                    "departure": flight.get("departure_airport", {}).get("time"),
                    "arrival": flight.get("arrival_airport", {}).get("time"),
                    "price": f"${flight.get('price')}",
                    "duration": f"{flight.get('duration', 0) // 60}h {flight.get('duration', 0) % 60}m",
                    "logo_url": flight.get("airline_logo"),
                    "booking_url": data.get("search_metadata", {}).get(
                        "google_flights_url"
                    ),
                }
            )

        return {
            "recommended_flights": recommended_flights,
            "search_timestamp": datetime.now().strftime("%Y-%m-%d"),
            "number_of_options": len(recommended_flights),
        }
