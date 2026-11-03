import os

from google.adk.agents import Agent
from google.adk.tools import AgentTool, google_search

# Definition of an agent tool that accesses Grounding with Google Search

# Read the instructions from a file in the same
# directory as this file.
script_dir = os.path.dirname(os.path.abspath(__file__))
instruction_file_path = os.path.join(script_dir, "search-prompt.txt")
with open(instruction_file_path, "r") as f:
  instruction = f.read()

# This sub-agent has its own model configuration, separate from the root agent.
# Grounding with Google Search is a built-in tool, and built-in tools can only
# be used by an agent that has no other tools, which is why it lives in its own
# agent and is exposed to the root agent as an AgentTool.
#
# Model selection: gemini-2.5-flash (Gemini 2.5 family).
#
# Why this model suits the search agent and its performance requirements:
#   * Latency. The search agent runs *inside* a root-agent turn: the root agent
#     is blocked waiting for it, and the grounded search itself already adds a
#     round-trip to Google. A Flash-tier model keeps that extra wait to about a
#     second, whereas a Pro-tier model roughly triples it for no better answers
#     on the kind of question this agent gets ("what do cockatiels eat?").
#   * Task shape. The agent does one narrow thing: run one grounded search and
#     write a short, cited summary of the results. It does not need Pro-level
#     reasoning; it needs fast, faithful summarisation with citations, which
#     is exactly what Flash is tuned for.
#   * Grounding support. Grounding with Google Search is a built-in tool of the
#     Gemini 2.x family on Vertex AI, and 2.5 Flash returns grounding metadata
#     (the source pages) that the prompt turns into the "Sources:" line.
#   * Cost. Every customer question about birds goes through this agent, so the
#     cheaper Flash tier matters more here than anywhere else in the app.
#   The three tiers were compared in adk web on the same five-question
#   conversation (see README). The lite tier is slightly faster again but
#   occasionally answers without searching, which defeats the purpose of the
#   tool; the pro tier was about 3x slower with no quality gain. Flash is the
#   best balance, so 2.5 Flash is the default.
#
# The model can be overridden with SEARCH_AGENT_MODEL. The Udacity lab project
# used to record the submission screenshots returns 404 for the entire
# gemini-2.0 and gemini-2.5 families (they are not enabled in that project), so
# starter/.env there sets SEARCH_AGENT_MODEL=gemini-3.5-flash, the equivalent
# Flash tier that *is* served. On a project with normal model access, leave the
# variable unset to get gemini-2.5-flash.
model = os.environ.get("SEARCH_AGENT_MODEL", "gemini-2.5-flash")

search_agent = Agent(
  name="search_agent",
  description=(
    "Researches general knowledge about birds (species, diet, habitat, care, "
    "lifespan, behavior) using Google Search. Use for any bird question that is "
    "not about Betty's Bird Boutique or its products."
  ),
  instruction=instruction,
  model=model,
  tools=[google_search],
)

search_agent_tool = AgentTool(agent=search_agent)
