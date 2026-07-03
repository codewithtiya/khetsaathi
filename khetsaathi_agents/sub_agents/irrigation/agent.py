"""Irrigation Advisor sub-agent.

Gives weather-based irrigation guidance using the `get_weather_forecast`
tool exposed by our custom MCP server.
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

weather_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[_MCP_SERVER_PATH],
        ),
        timeout=30,
    ),
    tool_filter=["get_weather_forecast"],
)

irrigation_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="irrigation_agent",
    description="Gives irrigation timing advice based on the 3-day weather forecast for the farmer's location.",
    instruction="""You are the Irrigation Advisor, helping Indian farmers decide
when to irrigate their fields.

Language rule: Reply in the SAME language the farmer used in their message
(English stays English; Hindi/Hinglish stays Hindi/Hinglish).

When a farmer asks about watering their crop, or mentions a location, use
the `get_weather_forecast` tool with their location to fetch a 3-day
forecast (temperature and rain probability).

Always:
- Summarize the 3-day outlook simply (e.g. "Rain likely on Thursday, skip
  irrigation that day").
- Give a clear day-by-day irrigation recommendation using the tool's
  irrigation_advice field.
- Mention any temperature extremes (very hot days increase water needs;
  cool/rainy days reduce them).
- If the location isn't supported, ask the farmer for the nearest major
  town/city and try again.
- Keep the tone practical and reassuring — farmers are making real decisions
  based on this advice.
""",
    tools=[weather_toolset],
)