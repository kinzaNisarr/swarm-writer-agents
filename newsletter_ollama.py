import json
from tavily import TavilyClient

from dotenv import load_dotenv
import os
from swarm import Agent
from swarm.repl import run_demo_loop
from openai import OpenAI
from swarm import Swarm

load_dotenv()


tavily = TavilyClient(api_key=os.getenv("TVLY_API_KEY"))

MODEL = "llama3.2"
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
)


# Swarm(client=ollama_client)  # client is an instance of the Swarm class


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
    model=MODEL,
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
    model=MODEL,
    instructions="""Take search results and generate a newsletter draft.
    Make sure that you include the title, content, and URL of each article.
    Transfer the draft to the Editor Agent for review.
    """,
    functions=[write_newsletter, transfer_to_editor],
)
editor_agent = Agent(
    name="Editor Agent",
    model=MODEL,
    instructions="""Review the newsletter draft and decide if it needs revision.
    If it needs revision, transfer it back to the Writing Agent.""",
    functions=[review_newsletter, transfer_to_writer],
)

# orchestrator agent
triage_agent = Agent(
    name="Triage Agent",
    model=MODEL,
    instructions="""Determine the appropriate agent based on the task.
    Make sure to transfer the control to the correct agent based on the task at hand.
    If the task is to search for news, transfer the control to the Search Agent.
    If the task is to write a newsletter, transfer the control to the Writing Agent.
    If the task is to review the newsletter, transfer the control to the Editor Agent.
    
    """,
)
triage_agent.functions = [transfer_to_search, transfer_to_writer, transfer_to_editor]


def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


# Run the demo loop
def run_demo_loop(
    triage_agent, context_variables=None, stream=False, debug=False
) -> None:
    client = Swarm(client=ollama_client)
    print("Starting Ollama Swarm CLI 🐝")

    messages = []
    agent = triage_agent

    while True:
        user_input = input("\033[90mUser\033[0m: ")
        messages.append({"role": "user", "content": user_input})

        response = client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )

        if stream:
            response = process_and_print_streaming_response(response)
        else:
            pretty_print_messages(response.messages)

        messages.extend(response.messages)
        agent = response.agent


if __name__ == "__main__":
    run_demo_loop(triage_agent)

# if __name__ == "__main__":
#     # res = search_news("news on AI and ML")
#     # print(res)
#     run_demo_loop(triage_agent)
