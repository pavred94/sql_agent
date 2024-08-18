# #!/usr/bin/env python3
# main.py
#
# Command-line application for SQL Agent. Useful for testing/debugging agent.

from langchain_ollama import ChatOllama

from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError

from helper import connect_to_psql_db, generate_tools, print_graph
from sql_agent import SQLAgent


def main():
    """
    Create SQL Agent.
    Command-line interface.
    """
    # Define model
    MODEL_NAME = "llama3.1"
    model = ChatOllama(model=MODEL_NAME, temperature=0.0, format="json")

    # Connect to DB
    db, sql_toolkit = connect_to_psql_db(user="postgres",
                                         password="postgres",
                                         host="localhost",
                                         port=5432,
                                         dbname="student_data",
                                         model=model)
    tools = generate_tools(db, sql_toolkit.get_tools())

    # Create SQL agent with in-memory checkpointer
    agent_executor = SQLAgent(model=model,
                              sql_tools=tools,
                              checkpointer=MemorySaver())

    print_graph(agent_executor.graph)

    # Agent configurations
    config = {"configurable": {"thread_id": "3"}}

    # Event loop to chat with AI agent via command-line
    while True:
        user_input = input("\nPrompt> ")
        if not user_input:
            continue

        if user_input.lower() == "\\q":
            print("\nExiting SQL Bot.")
            break

        print("\nSQL Bot Response>\n")
        inputs = {"messages": [("user", user_input)]}
        try:
            for s in agent_executor.graph.stream(inputs, stream_mode="values", config=config):
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
        except GraphRecursionError:
            print("\nNOTICE: Agent time out.")


if __name__ == '__main__':
    main()
