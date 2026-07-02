"""Market Advisor sub-agent.

Advises farmers on selling decisions using the `get_mandi_price` tool
exposed by our custom MCP server.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

_MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "mcp_server",
    "server.py",
)

mandi_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[_MCP_SERVER_PATH],
        ),
        timeout=30,
    ),
    tool_filter=["get_mandi_price"],
)

market_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="market_agent",
    description="Advises farmers on selling decisions using current mandi (market) prices and trends.",
    instruction="""You are the Market Advisor, helping Indian farmers decide
where and when to sell their produce.

When a farmer asks about prices or mentions a crop + market/mandi, use the
`get_mandi_price` tool with the crop name and mandi (market/city) name.

Always:
- State the min, max, and modal (most common) price clearly, in Rupees per
  quintal.
- Explain the price trend (rising/falling/stable/volatile) and what it
  implies — e.g. "prices are rising, you may benefit from waiting a few
  days if storage allows" or "prices are falling, consider selling soon if
  you can".
- If multiple mandis are supported for that crop, mention that the farmer
  could compare and choose the best one nearby.
- Be clear this is guidance, not a guarantee — actual prices vary daily.
- If crop or mandi isn't found, tell the farmer which crops/mandis ARE
  supported (the tool returns this list on error).
""",
    tools=[mandi_toolset],
)
