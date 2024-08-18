# #!/usr/bin/env python3
# main.py
#
# Basic Streamlit app for SQL agent

import streamlit as st

from langchain_ollama import ChatOllama
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError

from helper import connect_to_psql_db, generate_tools, print_graph
from sql_agent import SQLAgent

def main():
    """
    Create SQL Agent.
    Simple Streamlit interface.
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

    # Agent configurations
    config = {"configurable": {"recursion_limit": 25,
                               "thread_id": "1",
                               "callback": [StreamlitCallbackHandler(st.container())]}}
    # Streamlit App
    if prompt := st.chat_input():
        st.chat_message("user").write(prompt)
        inputs = {"messages": [("user", prompt)]}
        with st.chat_message("ai"):
            try:
                result = agent_executor.graph.invoke(inputs, config=config)["messages"][-1]
                print(result)
                if result.content:
                    st.json(result.content)
                else:
                    st.json(result.response_metadata["message"]["tool_calls"][0]["function"]["arguments"])
            except GraphRecursionError:
                st.write("NOTICE: Agent time out.")


if __name__ == '__main__':
    st.set_page_config(page_title="LangGraph SQL Agent")
    st.title("LangGraph SQL Agent")
    main()
