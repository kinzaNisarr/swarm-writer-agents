import streamlit as st
import pandas as pd
import ollama
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Dummy repair cost data source
dummy_repair_costs = {
    "scratches": {"minor": 100, "moderate": 300, "severe": 500},
    "dented_and_crumpled": {"minor": 200, "moderate": 600, "severe": 1000},
    "broken_headlights": {"minor": 150, "moderate": 400, "severe": 800},
    "shattered_windshield": {"minor": 300, "moderate": 800, "severe": 1200},
    "damaged_bumper": {"minor": 250, "moderate": 700, "severe": 1100},
}


# Function to perform analysis using Llama 3.2 Vision
def analyze_vehicle_image(image):
    try:
        # Use Llama 3.2 Vision for damage detection
        response = ollama.chat(
            model="llama3.2-vision",
            messages=[
                {
                    "role": "user",
                    "content": "Identify visible vehicle damage only. Dont be verbose.",
                    "images": [image],
                }
            ],
        )
        # Ensure response contains the 'message' and 'content' fields
        if "message" in response and "content" in response["message"]:
            analysis_result = response["message"]["content"]
            return analysis_result
        else:
            logging.error("Response does not contain 'message' or 'content' field.")
            return "No damage analysis available."
    except Exception as e:
        logging.error(f"Llama 3.2 Vision analysis failed: {e}")
        return "No damage analysis available."


# Function to estimate repair cost based on analysis using Llama 3.2 and dummy costs
def estimate_repair_cost(analysis_result):
    try:
        total_cost = 0
        detailed_cost = []

        # Process each damage type found in the analysis result
        for damage_type in dummy_repair_costs.keys():
            if damage_type in analysis_result.lower():
                severity = "moderate"  # Assuming severity as "moderate" for each damage type as it's not specified in the response
                cost = dummy_repair_costs[damage_type][severity]
                total_cost += cost
                detailed_cost.append(
                    f"{damage_type.replace('_', ' ').capitalize()} ({severity}): ${cost}"
                )

        # Use Llama 3.2 to generate a comprehensive repair summary
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": f"Based on the following damages, provide a detailed repair cost breakdown and suggestions: {analysis_result}",
                }
            ],
        )
        if "message" in response and "content" in response["message"]:
            ai_repair_analysis = response["message"]["content"]
        else:
            logging.error("Response does not contain 'message' or 'content' field.")
            ai_repair_analysis = "No detailed analysis available."

        # Combine dummy cost analysis with Llama 3.2 summary
        detailed_cost.append(f"Total Estimated Repair Cost: ${total_cost}")
        detailed_cost.append("\nAI Repair Analysis:")
        detailed_cost.append(ai_repair_analysis)

        return "\n".join(detailed_cost)
    except Exception as e:
        logging.error(f"Repair cost estimation using Llama 3.2 failed: {e}")
        return "Unable to estimate repair cost."


# Streamlit UI
def main():
    st.title("Vehicle Damage Analyzer for Insurance Claims")
    st.write(
        "Upload images of damaged vehicles to get an automated damage assessment and extract vehicle information."
    )

    uploaded_file = st.file_uploader(
        "Upload a JPEG or PNG image", type=["jpeg", "jpg", "png"]
    )

    if uploaded_file is not None:
        # Analyze the vehicle image
        st.write("Analyzing the image for damage...")
        analysis_result = analyze_vehicle_image(uploaded_file)
        st.markdown(analysis_result, unsafe_allow_html=True)

        # Estimate repair cost based on analysis
        st.write("Estimating repair costs...")
        repair_cost_estimate = estimate_repair_cost(analysis_result)
        st.markdown(repair_cost_estimate, unsafe_allow_html=True)

        # Generate a downloadable report
        if st.button("Download Report as CSV"):
            report_data = {
                "Damage Analysis": [analysis_result],
                "Repair Cost Estimate": [repair_cost_estimate],
            }
            df = pd.DataFrame(report_data)
            df.to_csv("damage_report.csv", index=False)
            st.success("Report saved to damage_report.csv")

    # Display error handling tips
    st.sidebar.title("Troubleshooting")
    st.sidebar.write("If you encounter issues, consider the following:")
    st.sidebar.write("- Ensure the image is clear and well-lit.")
    st.sidebar.write("- Make sure the vehicle is fully visible in the image.")
    st.sidebar.write("- Check that the image format is supported.")


if __name__ == "__main__":
    main()
