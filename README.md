<!-- omit in toc -->
# LangGraph SQL Agent

<!-- omit in toc -->
## Table of Contents
- [Overview](#overview)
   * [SQL Agent Graph](#sql-agent-graph)
- [Project Structure](#project-structure)
   * [Descriptions](#descriptions)
- [Tools & Enviroment](#tools--enviroment)
   * [Python packages/libraries (requirements.txt)](#python-packageslibraries-requirementstxt)
   * [Other](#other)
   * [Test Machine](#test-machine)
- [Next Steps / Known Issues / Observations](#next-steps--known-issues--observations)
- [Misc](#misc)
- [Author](#author)
  
## Overview
- A proof-of-concept SQL Agent utilizing LangGraph, a relatively new extension to Langchain.
- LangGraph provides a more intuitive framework to implement agent workflows than standard Langchain.
- Model/LLM: llama3.1:8b
- Local LLM Framework: Ollama
  
### SQL Agent Graph
  - `force_list_tables` & `list_table_action`: Force the to retrieval the tables from the database.
  - `force_get_schema` & `get_schema_action`: Force the retrieval the schema for all tables from the database.
  - `query_gen_agent`: LLM node. Generates SQL query in response to user question and asesses whether the response is correct.
  - `sql_db_query_action`: Action node that executes SQL queries against the database.
  <p align="center">
      <img src="https://github.com/user-attachments/assets/222d3c9d-4cfb-4826-9a51-248dcf27658e" />
  </p>

## Project Structure
```
├── sql_commands_student_data.sql
├── sql_commands_checkpointer.sql
├── sql_agent_flowchart.png
├── requirements.txt
├── src/ 
    ├── app.py
    ├── main.py
    ├── helper.py
    └── sql_chatbot.py
```
### Descriptions
- `sql_commands_student_data.sql`: Example SQL queries to generate the PostgreSQL database, student_data and example tables used in `main.py` and `app.py`.
- `sql_commands_checkpointer.sql`: Example SQL queries to generate the PostgreSQL database, checkpointer. Meant for use as a persistant checkpointer.
- `sql_agent_graph.png`: SQL Agent graph.
- `requirements.txt`: List of Python packages/libraries to run the Python scripts in `src/`.
- `sql_chatbot.py`: LangGraph SQL Agent.
- `main.py`: Command-line application for SQL Agent. Useful for testing/debugging agent.
- `app.py`: Basic Streamlit app for SQL Agent.
- `helper.py`: Contains helper functions for `main.py` and `app.py`.

## Tools & Enviroment
### Python packages/libraries (requirements.txt)
```
streamlit~=1.37.1
langgraph~=0.2.3
pillow~=10.4.0
typing_extensions~=4.12.2
pydantic~=2.8.2
requests~=2.32.3
langsmith~=0.1.99
langchain~=0.2.13
ipython~=8.26.0
```
### Other
- PostgreSQL Server 16
- Ollama=0.3.6
- Pycharm=2024.1.4
### Test Machine
```
Edition	Windows 11 Pro
Version	23H2

Processor	  12th Gen Intel(R) Core(TM) i7-12700KF   3.60 GHz
GPU         AMD Radeon RX 6800 XT
Installed   RAM	32.0 GB (31.8 GB usable)
System type	64-bit operating system, x64-based processor
```

## Next Steps / Known Issues / Observations
- Initially, I attempted to use Langchain and LangGraph's pre-built agents to meet my needs. Unfortunately, their performance was inconsistent and prone to hallucinations, making it challenging to rely on them. This experience prompted me to build my own custom agent from the ground up, which has provided me with complete control over the workflow and the ability to pinpoint issues more effectively.
- Added an experimental conditional edge and agent specifically meant to improve the termination criteria and handle translating the SQL query results to natural language. This caused more problems than it solved, so it has been removed for now. Currently, the agent's output is structured and not in a "chat" format. As such, improving the termination criteria and generating a chat-like response without hallucinations is an issue I am currently tackling.
- The agent will rarely ask the user for missing information and will often hallucinate the necessary information. The prompt has instructions to prevent this, but the agent does not follow it consistently. Related to this, when performing a new database insertion task, the agent initially succeeds in completing this
operation. However, it then fails to properly terminate and transitions the "insert" into an "update", causing it to continue indefinitely until it times out. This malfunctioning behavior results in unintended modifications to existing data. One possible solution is a human-in-the-loop implementation to force the agent to ask the user before executing a query.
- Implement a greater utilization of Pydantic to allow for more structured processing of data.
- The current prompt for the LLM is dense and long which may explain why the instructions therin are not followed consistently. It either needs to be shortened or broken up between multiple agent nodes.
- Official integration between Streamlit and LangGraph is apparently still ongoing.
  - For instance, the checkpointer malfunctions when using Streamlit. However, I have found workarounds such as the "AI Agent Service Toolkit" that I will explore in future iterations.
  - AI Agent Service Toolkit: https://github.com/JoshuaC215/agent-service-toolkit (Author: JoshuaC215; License: MIT)
- Langchain and, by extension, LangGraph are seemingly designed around OpenAI. I will need to re-think my prompt design to work more effectively with LLama. LLama's usage of tools is also inconsistent. As such, I may use an LLM such as Llama-3-Groq-Tool-Use (fine-tuned for tool use) when utilizing tools and LLama3.1 for the chat interface in a future iteration. Additionally, I will explore other open-source models and compare their performance to that of LLama's.
- I am using LLama3.1:8b, which is significantly smaller compared to the 70b and 405b versions. My hardware limitations restrict me to the 8b version. I'm interested in seeing how much the performance improves with the larger versions of the LLM.


## Misc
### PostgreSQL Checkpointer
The current iteration of the SQL Agent utilizes an in-memory checkpointer. 
The following is a sample implementation of PostgreSQL's persistent checkpointer.
- More information: https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/

```
from langgraph.checkpoint.postgres import PostgresSaver
from helper import get_psql_checkpointer_uri

# Get checkpointer URL for PSQL
DB_URI = get_psql_checkpointer_uri(user="postgres",
                                   password="postgres",
                                   host="localhost",
                                   port=5432,
                                   dbname="checkpointer")
 
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    # Create agent and so on 
```

## Author
Pavan Reddy
