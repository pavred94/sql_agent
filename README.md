<!-- omit in toc -->
# LangGraph SQL Agent

<!-- omit in toc -->
## Table of Contents
- [Overview](#overview)

## Overview
A proof-of-concept SQL Agent utilizing LangGraph, a relativelty new extension to Langchain.

## Descriptions
TODO

### PostgreSQL Checkpointer
```
from langgraph.checkpoint.postgres import PostgresSaver

# Get checkpointer URL for PSQL
DB_URI = get_psql_checkpointer_uri(user="postgres",
                                   password="postgres",
                                   host="localhost",
                                   port=5432,
                                   dbname="checkpointer")
# Create graph
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
```

### Misc
