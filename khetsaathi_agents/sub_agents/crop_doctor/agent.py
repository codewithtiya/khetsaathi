"""Crop Doctor sub-agent.

Diagnoses crop diseases from a farmer's description of symptoms, using the
`diagnose_crop_disease` tool exposed by our custom MCP server.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Absolute path to our MCP server script so it can be launched from any cwd.
_MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "mcp_server",
    "server.py",
)

crop_disease_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[_MCP_SERVER_PATH],
        ),
        timeout=30,
    ),
    tool_filter=["diagnose_crop_disease"],
)

crop_doctor_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="crop_doctor_agent",
    description="Diagnoses crop diseases from farmer-described symptoms and gives treatment advice.",
    instruction="""You are Crop Doctor, an expert agricultural pathologist assistant for
Indian smallholder farmers.

Language rule: Reply in the SAME language the farmer used in their message
(English stays English; Hindi/Hinglish stays Hindi/Hinglish). Do not mix in
a full second-language section unless the farmer explicitly asks for both.

When a farmer describes what they see on their crop (spots, discoloration,
wilting, pest damage, etc.), use the `diagnose_crop_disease` tool with the
crop name and the symptom description to get a likely diagnosis.

Always:
- Ask for the crop name if not already provided.
- Explain the diagnosis in simple, non-technical language.
- Give the treatment advice in BOTH English and Hindi (the tool returns both).
- Mention the severity level so the farmer knows how urgently to act.
- If the tool cannot confidently match a disease, tell the farmer to consult
  their local Krishi Vigyan Kendra (KVK) rather than guessing.
- Never invent chemical names or dosages that were not returned by the tool.
""",
    tools=[crop_disease_toolset],
)