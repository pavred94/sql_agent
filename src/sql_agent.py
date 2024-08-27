#!/usr/bin/env python3
# sql_agent.py
#
# LangGraph SQL Agent

from typing import Any
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks, RunnableSerializable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


class FinalResponse(BaseModel):
    """Final response to the user"""

    final_answer: str = Field(description="A full, accurate and descriptive response.")
    reasoning: str = Field(description="Steps to get to the final answer.")
    sql_query: str = Field(description="SQL queries used to get to the final answer.")


class AgentState(TypedDict):
    """Define agent state definition for SQLAgent"""

    messages: Annotated[list[AnyMessage], add_messages]


class SQLAgent:
    def __init__(self, model: BaseChatModel, sql_tools: list[BaseTool], checkpointer: MemorySaver):
        """
        LangGraph SQL Agent

        :param model: LLM
        :param sql_tools: SQL Query DB (sql_db_query),
                          SQL List Tables (sql_db_list_tables),
                          SQL Get Schema (sql_db_schema)
        :param checkpointer: Graph state checkpointer
        """
        self.model = model
        self.tools = {t.name: t for t in sql_tools}
        self.sql_db_query = self.tools["sql_db_query"]

        # **Build graph**
        # Nodes
        graph = StateGraph(AgentState)
        graph.add_node("force_list_tables", self.force_list_tables)
        graph.add_node("force_get_schema", self.force_get_schema)
        graph.add_node("list_tables_action", self.create_tool_node_with_fallback([self.tools["sql_db_list_tables"]]))
        graph.add_node("get_schema_action", self.create_tool_node_with_fallback([self.tools["sql_db_schema"]]))
        graph.add_node("query_gen_agent", self.query_gen_agent)
        graph.add_node("sql_db_query_action", self.create_tool_node_with_fallback([self.sql_db_query]))

        # Edges
        graph.add_edge(START, "force_list_tables")
        graph.add_edge("force_list_tables", "list_tables_action")
        graph.add_edge("list_tables_action", "force_get_schema")
        graph.add_edge("force_get_schema", "get_schema_action")
        graph.add_edge("get_schema_action", "query_gen_agent")
        graph.add_conditional_edges("query_gen_agent",
                                    self.should_continue,
                                    path_map={"go_back_qa": "query_gen_agent",
                                              "continue": "sql_db_query_action",
                                              "end": END})
        graph.add_edge("sql_db_query_action", "query_gen_agent")

        # Generate graph
        self.graph = graph.compile(checkpointer=checkpointer)

    def force_list_tables(self, state: AgentState) -> dict[str, list[AIMessage]]:
        """ Generates an AI Message to force the Agent to retrieve all the SQL tables"""

        return {"messages": [AIMessage(content="List tables",
                                       tool_calls=[{"name": "sql_db_list_tables",
                                                    "args": {},
                                                    "id": "sql_db_list_tables",
                                                    "type": "tool_call"},

                                                   ],
                                       )
                             ]
                }

    def force_get_schema(self, state: AgentState) -> dict[str, list[AIMessage]]:
        """
        Generates an AI Message to force the Agent to retrieve the entire SQL schema.
        Gets full list of tables from previous invocation of sql_db_list_tables.
        """

        # Get table names
        schema_input = state["messages"][-1].content
        return {"messages": [AIMessage(content="Get schema",
                                       tool_calls=[{"name": "sql_db_schema",
                                                    "args": {"table_names": schema_input},
                                                    "id": "sql_db_schema",
                                                    "type": "tool_call"},
                                                   ],
                                       )
                             ]
                }

    def get_query_generator(self) -> RunnableSerializable[dict, Any]:
        """ Binds prompt and tools (sql_db_query, FinalResponse) to LLM """

        template = """
        You are a friendly PostgreSQL expert with a strong attention to detail.
        
        # Required criteria before execution
        1 - Tools are delimited with triple backticks.
        2 - Prompt headers are preceded by a pound sign (#).
        3 - DO NOT MAKE UP INFORMATION under any circumstances.
        4 - Your final answer MUST BE of the format stated in "Final Answer Format".
        5 - Output in JSON format.
        
        # Your task is to carry out the user's action via the following steps in order
        Step 1 - Process the user's action and determine what information 
                 you need to answer it based on the already retrieved tables and database schema.
        Step 2 - Determine the set of syntactically correct set of PostgreSQL queries necessary to carry out the user's action.
                 Reference the "SQL Rules" section for guidelines when generating SQL queries.
                 DO NOT use solely the database schema to answer the user's action unless explicitly told to do so.
        Step 3 - Use ```sql_db_query``` to run the SQL queries against the database. 
        Step 4 - If at least one of the following numbered criteria is met, go to Step 5, otherwise go to Step 1.
                 1 - You do not have the information necessary to perform the user's action.
                 2 - You get a duplicate key error.
                 3 - You have determined that the user's action was unsuccessful and you cannot resolve it.
                 4 - All SQL queries were successfully executed, you have double-checked the results 
                     and have determined the user's action was executed successfully.
        Step 5 - Execute ```FinalResponse``` and format the final answer via "Final Answer Format".
        
        # SQL Rules
        Double check the PostgreSQL query for common mistakes, including:
        - Using NOT IN with NULL values
        - Using UNION when UNION ALL should have been used
        - Using BETWEEN for exclusive ranges
        - Data type mismatch in predicates
        - Properly quoting identifiers
        - Using the correct number of arguments for functions
        - Casting to the correct data type
        - Using the proper columns for joins
        
        # Final Answer Format
        1 - SQL Queries: List of SQL queries used.
        2 - Final answer: Chat-like response to user's action.
        3 - Reasoning: Brief summary of how the action was carried out.
        """
        query_gen_prompt = ChatPromptTemplate.from_messages(
            [("system", template), ("placeholder", "{messages}")]
        )
        return query_gen_prompt | self.model.bind_tools([self.sql_db_query, FinalResponse],
                                                        tool_choice="required",
                                                        strict=True)

    def query_gen_agent(self, state: AgentState) -> dict[str, list[ToolMessage]]:
        """
        Agent (LLM) node that decides when it is necessary
        to generate a query or stop and generate a response for the user.
        """

        message = self.get_query_generator().invoke(state)
        tool_messages = []
        if message.tool_calls:
            for tc in message.tool_calls:
                if tc["name"] not in ["sql_db_query", "FinalResponse"]:
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: The wrong tool was called: {tc['name']}. "
                                    f"Please fix your mistakes.",
                            tool_call_id=tc["id"],
                        )
                    )
        return {"messages": [message] + tool_messages}

    # Define a conditional edge to decide whether to continue or end the graph
    def should_continue(self, state: AgentState) -> Literal["end", "go_back_qa", "continue"]:
        """
        Defines conditional edge to determine whether to return to query_gen_agent,
        execute a SQL query or end execution.
        """

        messages = state["messages"]
        last_message = messages[-1]
        if last_message.content.startswith("Error:"):
            return "go_back_qa"  # Back to query_gen_agent
        elif (getattr(last_message, "tool_calls", None)) and (last_message.tool_calls[0]["name"] == "sql_db_query"):
            return "continue"  # Go to sql_db_query
        else:
            return "end"  # End if no tool call

    def handle_tool_error(self, state) -> dict:
        """ Generates Tool error message for LLM to process """
        error = state.get("error")
        tool_calls = state["messages"][-1].tool_calls
        return {
            "messages": [ToolMessage(content=f"Error: {repr(error)}\nPlease fix your mistakes.",
                                     tool_call_id=tc["id"])
                         for tc in tool_calls]
        }

    def create_tool_node_with_fallback(self, tools: list) -> RunnableWithFallbacks[Any, dict]:
        """
        Creates a ToolNode with a fallback to handle errors.
        """
        return ToolNode(tools).with_fallbacks(fallbacks=[RunnableLambda(self.handle_tool_error)],
                                              exception_key="error")
