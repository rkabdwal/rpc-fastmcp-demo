# server.py
import os
from dotenv import load_dotenv
import pyodbc
from openai import AsyncOpenAI
from fastmcp import FastMCP, Context
from typing import List, Dict, Any

# 1. Load environment variables
load_dotenv()
DRIVER   = os.getenv("SQL_DRIVER")
SERVER   = os.getenv("SQL_SERVER")
DATABASE = os.getenv("SQL_DATABASE")
USERNAME = os.getenv("SQL_USERNAME")
PASSWORD = os.getenv("SQL_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

# 2. Instantiate the async OpenAI client
llm = AsyncOpenAI(api_key=OPENAI_API_KEY)

# 3. Connection string builder
def get_conn():
    conn_str = (
        f"Driver={DRIVER};"
        f"Server={SERVER};"
        f"Database={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
        "Trusted_Connection=no;"
    )
    return pyodbc.connect(conn_str, autocommit=True)

# 4. Create the MCP server
mcp = FastMCP(name="AdventureWorksSQLServer")

# 5. Expose schema as a resource
@mcp.resource("schema://sqlserver")
def get_schema() -> str:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.TABLE_SCHEMA, t.TABLE_NAME,
               c.COLUMN_NAME, c.DATA_TYPE
        FROM INFORMATION_SCHEMA.TABLES AS t
        JOIN INFORMATION_SCHEMA.COLUMNS AS c
          ON t.TABLE_NAME = c.TABLE_NAME
        WHERE t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION;
    """)
    rows = cursor.fetchall()

    schema_txt = ""
    last = (None, None)
    for sch, tbl, col, dt in rows:
        if (sch, tbl) != last:
            schema_txt += f"\n-- {sch}.{tbl}\nCREATE TABLE {sch}.{tbl} (\n"
            last = (sch, tbl)
        schema_txt += f"    {col} {dt},\n"
    return schema_txt

# 6. Raw SQL executor (not a tool)
def _execute_sql(sql: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    cols = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, row)) for row in rows]

# 7. Expose the executor as an MCP tool
query_data = mcp.tool()(_execute_sql)

# 8. NL → SQL → execute tool
@mcp.tool()
async def nl_query(request: str, ctx: Context) -> List[Dict[str, Any]]:
    # Read schema
    resources = await ctx.read_resource("schema://sqlserver")
    schema_txt = (
        resources[0].content
        if isinstance(resources, list)
        else resources.content
    )

    # Build prompt
    prompt = f"""You are given this SQL Server schema:

{schema_txt}

Generate a single T-SQL SELECT statement that answers:
“{request}”

Only return the SQL."""

    # Call LLM
    resp = await llm.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
    )
    sql = resp.choices[0].message.content.strip()

    # Execute and return native Python objects
    return _execute_sql(sql)

# 9. Run the server
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/mcp",
    )
