import asyncio
from dotenv import load_dotenv
from agents.orchestrator_agent import OrchestratorAgent
import json


async def main():
    # Load environment variables
    load_dotenv()

    # Create orchestrator instance
    orchestrator = OrchestratorAgent()

    # Example travel request
    travel_request = {
        "origin": "MAD",
        "destination": "AMS",
        "departure_date": "2024-11-15",
        "return_date": "2024-12-01",
        "email": "pdichone@gmail.com",
        "adults": 1,
        "children": 0,
        "rooms": 1,
        # "sort_by": "rating",
        # "hotel_class": "4",
    }

    # Ensure return_date is later than departure_date
    if travel_request["return_date"] <= travel_request["departure_date"]:
        raise ValueError("Return date must be later than the departure date.")

    # Process travel request
    results = await orchestrator.run([{"role": "user", "content": str(travel_request)}])

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
