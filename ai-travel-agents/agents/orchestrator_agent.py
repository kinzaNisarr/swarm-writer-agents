from typing import Dict, Any
from .base_agent import BaseAgent
from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent
from .email_agent import EmailAgent
import asyncio


class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TravelOrchestrator",
            instructions="""Coordinate the complete travel planning workflow.
            Responsibilities:
            1. Manage flight searches for both outbound and return trips
            2. Handle hotel searches based on destination and dates
            3. Ensure proper email delivery of travel recommendations
            4. Analyze and combine results for optimal travel suggestions
            5. Track workflow progress and handle any errors
            Consider: pricing optimization, scheduling efficiency, and user preferences.
            Provide comprehensive travel recommendations with detailed pricing and booking information.""",
        )
        self._setup_agents()

    def _setup_agents(self):
        """Initialize all specialized travel agents"""
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.email_agent = EmailAgent()

    async def run(self, messages: list) -> Dict[str, Any]:
        """Process a travel planning request"""
        print("🎯 Orchestrator: Starting travel planning process")

        travel_request = eval(messages[-1]["content"])
        workflow_context = {
            "travel_request": travel_request,
            "status": "initiated",
            "current_stage": "flight_search",
        }

        try:
            # Ensure return_date is later than departure_date
            if travel_request["return_date"] <= travel_request["departure_date"]:
                raise ValueError("Return date must be later than the departure date.")

            # Search flights (both outbound and inbound)
            flights = await self.flight_agent.run(
                [
                    {
                        "role": "user",
                        "content": str(
                            {
                                "origin": travel_request["origin"],
                                "destination": travel_request["destination"],
                                "departure_date": travel_request["departure_date"],
                                "return_date": travel_request["return_date"],
                                "adults": travel_request.get("adults", 1),
                                "infants_in_seat": travel_request.get(
                                    "infants_in_seat", 0
                                ),
                                "infants_on_lap": travel_request.get(
                                    "infants_on_lap", 0
                                ),
                                "children": travel_request.get("children", 0),
                            }
                        ),
                    }
                ]
            )
            workflow_context.update(
                {
                    "flights": flights,
                    "current_stage": "hotel_search",
                }
            )

            # Search hotels
            hotels = await self.hotel_agent.run(
                [
                    {
                        "role": "user",
                        "content": str(
                            {
                                "location": travel_request["destination"],
                                # "location": travel_request.get(
                                #     "destination", "amsterdam"
                                # ),
                                "check_in": travel_request["departure_date"],
                                "check_out": travel_request["return_date"],
                                "adults": travel_request.get("adults", 1),
                                "children": travel_request.get("children", 0),
                                "rooms": travel_request.get("rooms", 1),
                                "sort_by": travel_request.get("sort_by", ""),
                                "hotel_class": travel_request.get("hotel_class", ""),
                            }
                        ),
                    }
                ]
            )
            print(f"\n \n==> Hotels: {hotels} \n \n")
            workflow_context.update(
                {"hotels": hotels, "current_stage": "email_preparation"}
            )

            # Prepare and send email
            email_result = await self.email_agent.run(
                [
                    {
                        "role": "user",
                        "content": str(
                            {
                                "to_email": travel_request["email"],
                                "flights": flights,
                                "hotels": hotels,
                            }
                        ),
                    }
                ]
            )
            workflow_context.update(
                {"email_result": email_result, "status": "completed"}
            )

            # Generate final recommendations using Ollama
            final_analysis = self._query_ollama(
                f"""Analyze the travel options and create a summary:
                Flights: {flights}
                Hotels: {hotels}
                
                Provide:
                1. Best flight combination based on price and schedule
                2. Top hotel recommendation with reasoning
                3. Total estimated trip cost
                """
            )

            workflow_context["final_recommendations"] = self._parse_json_safely(
                final_analysis
            )
            return workflow_context

        except Exception as e:
            workflow_context.update(
                {
                    "status": "failed",
                    "error": str(e),
                    "current_stage": workflow_context.get("current_stage", "unknown"),
                }
            )
            raise
