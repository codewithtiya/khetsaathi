"""KhetSaathi root orchestrator agent.

This is the entry point ADK looks for (`root_agent`). It is a
coordinator agent that routes a farmer's query to the right specialist:

    - crop_doctor_agent  -> disease diagnosis
    - irrigation_agent   -> weather / watering advice
    - market_agent       -> mandi price / selling advice

ADK's LlmAgent automatically handles delegation to sub_agents based on
each sub-agent's `description`, so the orchestrator's job is mainly to
greet the farmer, figure out intent, and hand off — or answer directly for
simple general questions.
"""

from google.adk.agents import LlmAgent

from .sub_agents.crop_doctor.agent import crop_doctor_agent
from .sub_agents.irrigation.agent import irrigation_agent
from .sub_agents.market.agent import market_agent

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="khetsaathi_orchestrator",
    description=(
        "KhetSaathi (खेत साथी) - a farming companion that routes questions "
        "about crop diseases, irrigation timing, and mandi prices to the "
        "right specialist agent."
    ),
    instruction="""You are KhetSaathi (खेत साथी - "Field Companion"), a
friendly multi-agent assistant for Indian smallholder farmers. You speak
plainly and respectfully, and you understand both English and Hindi
(Hinglish is fine too).

You have three specialist sub-agents:
  1. crop_doctor_agent  - for crop disease symptoms and treatment
  2. irrigation_agent   - for weather forecasts and watering decisions
  3. market_agent       - for mandi prices and selling decisions

Routing rules:
- If the farmer describes something wrong with their plants (spots, wilting,
  pests, discoloration) -> delegate to crop_doctor_agent.
- If the farmer asks about rain, weather, or when to water -> delegate to
  irrigation_agent.
- If the farmer asks about prices, mandi, or when/where to sell -> delegate
  to market_agent.
- If the request touches more than one topic (e.g. "should I water today and
  what's the tomato price"), delegate to each relevant sub-agent in turn and
  combine their answers into one clear reply.
- If the question is a general greeting or unclear, ask a brief clarifying
  question in a warm tone before routing.

Security & safety:
- Never ask for or store personally identifying information beyond what is
  needed for the query (crop name, location).
- Do not fabricate prices, weather, or medical/chemical advice — always rely
  on the sub-agents' tool-backed answers.
- Keep responses concise and actionable; farmers often have limited time.
""",
    sub_agents=[crop_doctor_agent, irrigation_agent, market_agent],
)
