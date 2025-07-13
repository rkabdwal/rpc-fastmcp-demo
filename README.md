# AdventureWorks MCP Demo using FASTMCP

A minimal MCP-compliant server & client for querying AdventureWorksLT2019 via natural language.

## Features

- **MCP Prompts**: first-class prompt primitive for NL→T-SQL templates  
- **MCP Resources**: `schema://sqlserver` exposing your DB schema  
- **MCP Tools**: `query_data` & `nl_query` for SQL execution  
- **Streaming JSON-RPC** over HTTP/SSE  
- **FASTMCP 2.0**

## Prerequisites

- Python 3.9+  
- Microsoft ODBC Driver 17 for SQL Server installed  
- A running SQL Server instance with AdventureWorksLT2019  
- An OpenAI API key

## Setup

1. Copy and edit the env file:

   ```bash
   cp .env.example .env

2. Clone and enter the folder:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

## Run

1. Run MCP Server

   ```bash
   python rpc_server.py

2. Run Client

   ```bash
   python rpc_client.py
