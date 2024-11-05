import json
import os
from swarm import Agent
from swarm.repl import run_demo_loop
from openai import OpenAI
from swarm import Swarm
from duckduckgo_search import DDGS  # pip install duckduckgo-search
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m")

MODEL = "llama3.2"

# ============= Source ====================
# source: https://ollama.com/blog/openai-compatibility
# ============= Source ====================
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
)

# Initialize Swarm client
client = Swarm(client=ollama_client)


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


def get_news_articles(topic):
    print(f"Running DuckDuckGo news search for {topic}...")

    # DuckDuckGo search
    ddg_api = DDGS()
    results = ddg_api.text(f"{topic} {current_date}", max_results=5)
    if results:
        news_results = "\n\n".join(
            [
                f"Title: {result['title']}\nURL: {result['href']}\nDescription: {result['body']}"
                for result in results
            ]
        )
        return news_results
    else:
        return f"Could not find news results for {topic}."


# Create AI Agents

# News Agent to fetch news
news_agent = Agent(
    name="News Assistant",
    instructions="You provide the latest news articles for a given topic using DuckDuckGo search.",
    functions=[get_news_articles],
    model="llama3.2",
)


# Editor Agent to edit news
editor_agent = Agent(
    name="Editor Assistant",
    instructions="Rewrite and give me as news article ready for publishing. Each News story in separate section.",
    model="llama3.2",
)


def run_news_workflow(topic):
    print("Running News Agent workflow...")

    # Step 1: Fetch news
    news_response = client.run(
        agent=news_agent,
        messages=[
            {
                "role": "user",
                "content": f"Get me the news about {topic} on {current_date}",
            }
        ],
    )

    raw_news = news_response.messages[-1]["content"]

    # Step 2: Pass news to editor for final review
    edited_news_response = client.run(
        agent=editor_agent,
        messages=[{"role": "user", "content": raw_news}],
    )

    return edited_news_response.messages[-1]["content"]


# res = run_news_workflow("AI and LLMs")
# print(res)


# Run the demo loop using the news workflow
def run_demo_loop(agent, context_variables=None, stream=False, debug=False):
    print("Starting Ollama Swarm CLI 🐝")

    messages = []
    current_agent = agent

    while True:
        user_input = input("\033[90mUser\033[0m: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        messages.append({"role": "user", "content": user_input})

        response = client.run(
            agent=current_agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )

        # Print the assistant's response
        if stream:
            process_and_print_streaming_response(response)
        else:
            pretty_print_messages(response.messages)

        # Extend the conversation history
        messages.extend(response.messages)

        # Move to the next agent automatically if applicable
        if current_agent == news_agent:
            raw_news = response.messages[-1]["content"]
            current_agent = editor_agent
            messages = [{"role": "user", "content": raw_news}]
        elif current_agent == editor_agent:
            print("Workflow complete.")
            break


if __name__ == "__main__":
    run_demo_loop(news_agent)
