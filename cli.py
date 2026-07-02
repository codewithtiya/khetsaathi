#!/usr/bin/env python3
"""
KhetSaathi CLI - Agent Skill
=============================
A lightweight command-line "skill" that lets a farmer talk to the
KhetSaathi multi-agent system directly from a terminal — useful for
low-bandwidth rural settings, SMS-gateway style integrations, or simply
demoing the agent without a web UI.

Usage:
    python cli.py                      # interactive chat session
    python cli.py ask "my wheat leaves have yellow stripes"
    python cli.py ask "mausam kaisa rahega Agra mein?" --lang hi

This wraps ADK's Runner + InMemorySessionService so the whole multi-agent
system (orchestrator -> crop_doctor/irrigation/market) runs the same way
it would under `adk run` or `adk web`, just through a farmer-friendly CLI.
"""

import argparse
import asyncio
import sys
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from khetsaathi_agents.agent import root_agent

APP_NAME = "khetsaathi"

BANNER = r"""
 _  __ _          _   ____              _    _     _
| |/ /| |__   ___| |_/ ___|  __ _  __ _| |_ | |__ (_)
| ' / | '_ \ / _ \ __\___ \ / _` |/ _` | __|| '_ \| |
| . \ | | | |  __/ |_ ___) | (_| | (_| | |_ | | | | |
|_|\_\|_| |_|\___|\__|____/ \__,_|\__,_|\__||_| |_|_|

  खेत साथी — your farming companion agent
  Type 'exit' or 'quit' to leave.
"""


async def _run_query(runner: Runner, session_id: str, user_id: str, text: str) -> str:
    content = types.Content(role="user", parts=[types.Part(text=text)])
    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(p.text or "" for p in event.content.parts)
    return final_text


async def interactive_session():
    session_service = InMemorySessionService()
    user_id = "farmer_local"
    session_id = str(uuid.uuid4())
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    print(BANNER)
    while True:
        try:
            user_input = input("Aap (You)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAlvida! (Goodbye!)")
            break
        if user_input.lower() in {"exit", "quit", "band karo"}:
            print("Alvida! (Goodbye!)")
            break
        if not user_input:
            continue

        reply = await _run_query(runner, session_id, user_id, user_input)
        print(f"\nKhetSaathi> {reply}\n")


async def single_query(query: str):
    session_service = InMemorySessionService()
    user_id = "farmer_local"
    session_id = str(uuid.uuid4())
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    reply = await _run_query(runner, session_id, user_id, query)
    print(reply)


def main():
    parser = argparse.ArgumentParser(
        prog="khetsaathi",
        description="KhetSaathi - Multi-agent farming assistant CLI (Agent Skill)",
    )
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a single question and exit")
    ask_parser.add_argument("query", type=str, help="Your question, in English or Hindi/Hinglish")
    ask_parser.add_argument("--lang", type=str, default="auto", choices=["auto", "en", "hi"],
                             help="Preferred reply language (informational; agent auto-detects too)")

    args = parser.parse_args()

    if args.command == "ask":
        asyncio.run(single_query(args.query))
    else:
        asyncio.run(interactive_session())


if __name__ == "__main__":
    sys.exit(main())
