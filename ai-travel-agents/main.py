import asyncio
import streamlit as st
from dotenv import load_dotenv
from agents.orchestrator_agent import OrchestratorAgent
import json


async def process_travel_request(travel_request):
    # Load environment variables
    load_dotenv()

    # Create orchestrator instance
    orchestrator = OrchestratorAgent()

    # Ensure return_date is later than departure_date
    if travel_request["return_date"] <= travel_request["departure_date"]:
        raise ValueError("Return date must be later than the departure date.")

    # Process travel request
    results = await orchestrator.run([{"role": "user", "content": str(travel_request)}])
    return results


def main():
    st.title("Travel Information Request")

    # New Travel Request Query Form

    # Existing Travel Request Form Fields
    st.subheader("Or fill out the following details:")
    origin = st.text_input("Origin Airport Code (e.g., MAD)")
    destination = st.text_input("Destination Airport Code (e.g., AMS)")
    departure_date = st.date_input("Departure Date")
    return_date = st.date_input("Return Date")
    email = st.text_input("Your Email Address")
    adults = st.number_input("Number of Adults", min_value=1, step=1)
    children = st.number_input("Number of Children", min_value=0, step=1)
    rooms = st.number_input("Number of Rooms", min_value=1, step=1)

    # Email sending option
    send_email = st.radio(
        "Do you want to send this information via email?", ("No", "Yes")
    )

    # Send Request Button
    if st.button("Get Travel Information"):
        # Display summary of flight request at the top
        departure_summary = f"Flights from {origin} to {destination} from {departure_date} to {return_date}"
        st.markdown(f"## {departure_summary}")
        # Construct travel request dictionary from the form
        travel_request = {
            "origin": origin,
            "destination": destination,
            "departure_date": str(departure_date),
            "return_date": str(return_date),
            "email": email,
            "adults": adults,
            "children": children,
            "rooms": rooms,
        }

        # Run the orchestrator asynchronously
        try:
            results = asyncio.run(process_travel_request(travel_request))
            st.success("Travel information processed successfully!")

            # Display flight and hotel information in tabs
            if "flights" in results and "hotels" in results:
                tab1, tab2 = st.tabs(["Flight Options", "Hotel Options"])

                st.markdown(f"## {departure_summary}")
                for idx, flight in enumerate(
                    results["flights"]["recommended_flights"], start=1
                ):
                    st.markdown(f"### Option {idx}: {flight['airline']}")
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(flight["logo_url"], width=100)
                    with col2:
                        st.markdown(f"- **Airline:** {flight['airline']}")
                        st.markdown(f"- **Flight Number:** {flight['flight_number']}")
                        st.markdown(f"- **Departure:** {flight['departure']}")
                        st.markdown(f"- **Arrival:** {flight['arrival']}")
                        st.markdown(f"- **Duration:** {flight['duration']}")
                        st.markdown(f"- **Price:** {flight['price']}")
                        st.markdown(f"[Book Now]({flight['booking_url']})")

                with tab2:
                    for idx, hotel in enumerate(
                        results["hotels"]["recommended_hotels"], start=1
                    ):
                        st.markdown(f"### Option {idx}: {hotel['name']}")
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.image(hotel["image_url"], width=200)
                        with col2:
                            # Safely round rating if it's not None, otherwise default to 0
                            rating = (
                                hotel["rating"] if hotel["rating"] is not None else 0
                            )
                            st.markdown(f"- **Rating:** {round(rating, 1)}")
                            st.markdown(
                                f"- **Price per Night:** {hotel['price_per_night']}"
                            )
                            st.markdown(f"- **Total Price:** {hotel['total_price']}")

                            # Fix amenities handling to avoid errors when amenities is None
                            amenities = hotel.get("amenities", [])
                            amenities_str = (
                                ", ".join(amenities)
                                if isinstance(amenities, list)
                                else "No amenities listed"
                            )
                            st.markdown(f"- **Amenities:** {amenities_str}")
                            if hotel["booking_url"]:
                                st.markdown(f"[Book Now]({hotel['booking_url']})")

            # Send email if selected
            if send_email == "Yes":
                sender_email = "paulo@vincimind.com"  # Example sender email
                receiver_email = email
                email_subject = f"Travel to {destination}"
                st.text(f"Sender Email: {sender_email}")
                st.text(f"Receiver Email: {receiver_email}")
                st.text(f"Email Subject: {email_subject}")
                st.success("Email sent successfully!")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()


# import asyncio
# from dotenv import load_dotenv
# from agents.orchestrator_agent import OrchestratorAgent
# import json


# async def main():
#     # Load environment variables
#     load_dotenv()

#     # Create orchestrator instance
#     orchestrator = OrchestratorAgent()

#     # Example travel request
#     travel_request = {
#         "origin": "MAD",
#         "destination": "AMS",
#         "departure_date": "2024-11-24",
#         "return_date": "2024-12-01",
#         "email": "pdichone@gmail.com",
#         "adults": 1,
#         "children": 0,
#         "rooms": 1,
#         # "sort_by": "rating",
#         # "hotel_class": "4",
#     }

#     # Ensure return_date is later than departure_date
#     if travel_request["return_date"] <= travel_request["departure_date"]:
#         raise ValueError("Return date must be later than the departure date.")

#     # Process travel request
#     results = await orchestrator.run([{"role": "user", "content": str(travel_request)}])

#     print(json.dumps(results, indent=2))


# if __name__ == "__main__":
#     asyncio.run(main())
