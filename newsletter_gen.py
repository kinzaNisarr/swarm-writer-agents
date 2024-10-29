from tavily import TavilyClient

from dotenv import load_dotenv
import os
from swarm import Agent
from swarm.repl import run_demo_loop

load_dotenv()


tavily = TavilyClient(api_key=os.getenv("TVLY_API_KEY"))


def search_news(query: str):
    """Search for news articles on the given query."""
    # Perform the API request and handle any potential errors
    try:
        response = tavily.search(query)
        print(f"Searching for news on the '{query}' query...")
        return response["results"]
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


def write_newsletter(articles):
    print(f"===>got the articles... {articles}")
    """Write a newsletter with the given articles/text"""
    print("Writing a newsletter with the search results...")
    newsletter = ""
    for article in articles:
        newsletter += article

    return newsletter


def review_newsletter(newsletter: str):
    """Review the newsletter before sending it out"""
    print("Reviewing the newsletter...")
    return f"Reviewing the newsletter:\n{newsletter}"


# Function to transfer control to the Search Agent
def transfer_to_search():
    return search_agent


# Function to transfer control to the Writing Agent
def transfer_to_writer():
    return writer_agent


# Function to transfer control to the Editor Agent
def transfer_to_editor():
    return editor_agent


# Initialize the agents
search_agent = Agent(
    name="Search Agent",
    instructions="""
        You are a world-class search agent (web searcher). Your role is to:
        1. Search for news (most recent) articles based on a query provided by the user.
        2. Retrieve the article title, content, and URL.
        and then transfer the control to the Writing Agent for drafting the newsletter.
        Make sure to make the transfer only after you have found the articles.
    """,
    functions=[search_news, transfer_to_writer],
)

writer_agent = Agent(
    name="Writing Agent",
    instructions="""Take search results and generate a newsletter draft.
    Make sure that you include the title, content, and URL of each article.
    Transfer the draft to the Editor Agent for review.
    """,
    functions=[write_newsletter, transfer_to_editor],
)
editor_agent = Agent(
    name="Editor Agent",
    instructions="""Review the newsletter draft and decide if it needs revision.
    If it needs revision, transfer it back to the Writing Agent.""",
    functions=[review_newsletter, transfer_to_writer],
)

# orchestrator agent
triage_agent = Agent(
    name="Triage Agent",
    instructions="""Determine the appropriate agent based on the task.
    Make sure to transfer the control to the correct agent based on the task at hand.
    If the task is to search for news, transfer the control to the Search Agent.
    If the task is to write a newsletter, transfer the control to the Writing Agent.
    If the task is to review the newsletter, transfer the control to the Editor Agent.
    
    """,
)
triage_agent.functions = [transfer_to_search, transfer_to_writer, transfer_to_editor]


# Run the demo loop
if __name__ == "__main__":
    # res = search_news("AI")
    # print(res)
    run_demo_loop(triage_agent)
