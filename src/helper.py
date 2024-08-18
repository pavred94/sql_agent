# #!/usr/bin/env python3
# helper.py
#
# Contains helper functions

import io
from PIL import Image as PIL_Image

from langchain_core.language_models import BaseChatModel
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_core.tools import tool, BaseTool

from langgraph.graph import StateGraph


def connect_to_psql_db(user: str, password: str, host: str, port: str, dbname: str, model: BaseChatModel) \
        -> tuple[SQLDatabase, SQLDatabaseToolkit]:
    """
    Establish connection to PostgreSQL database via given information and connection URI.
    :param user: DB username
    :param password: DB password
    :param host: DB host
    :param port: DB port
    :param dbname: DB name
    :param model: DB model
    :return: SQLDatabase, SQLDatabaseToolkit
    """
    CONNECTION_STRING = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    db = SQLDatabase.from_uri(CONNECTION_STRING)
    sql_toolkit = SQLDatabaseToolkit(db=db, llm=model)
    return db, sql_toolkit


def get_psql_checkpointer_uri(user: str, password: str, host: str, port: str, dbname: str) -> str:
    """
    Generates connection string for PostgreSQL checkpointer.
    :param user: DB username
    :param password: DB password
    :param host: DB host
    :param port: DB port
    :param dbname: DB name
    :return: PostgreSQL checkpointer URI
    """
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode=disable"


def generate_tools(db: SQLDatabase, sql_tools: list[BaseTool]) -> list[BaseTool]:
    """
    Collates the SQL tools for use by the SQL Agent
    :param db: SQL database
    :param sql_tools: Default SQL tools from SQLDatabaseToolkit
    :return: SQL Query DB (sql_db_query),
             SQL List Tables (sql_db_list_tables),
             SQL Get Schema (sql_db_schema)
    """

    @tool
    def sql_db_query(query: str) -> str:
        """
        Custom tool that executes a SQL query against a database and returns the result.
        :param query: The SQL query to execute.
        :return: The result of the SQL query.
                  - Results with errors will have prefix, "Error:".
                  - All other results are considered a successful query.
        """
        return db.run_no_throw(query)

    sql_db_list_tables = next(t for t in sql_tools if t.name == "sql_db_list_tables")
    sql_db_schema = next(t for t in sql_tools if t.name == "sql_db_schema")
    return [sql_db_query, sql_db_list_tables, sql_db_schema]


def print_graph(agent_graph: StateGraph):
    """
    Generates SQL Agent graph
    :param agent_graph: SQL Agent graph
    """
    image = PIL_Image.open(
        io.BytesIO(
            agent_graph.get_graph().draw_mermaid_png(
                draw_method=MermaidDrawMethod.API,
            )
        ))
    image.show()
