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
# Model selection: the search agent does one thing - run a grounded search and
# summarise the results - so it does not need a "pro" model. A flash-tier model
# keeps the extra round-trip short (the root agent is already waiting on this
# call) while still writing a good summary of the search results. The intended
# choice is gemini-2.5-flash; the lab project used for this submission returns
# 404 for the whole gemini-2.5 family, so the current flash tier,
# gemini-3.5-flash, is used instead (measured ~1s per call vs ~3s for
# gemini-3.1-pro-preview, with no quality difference on bird questions). Set
# SEARCH_AGENT_MODEL=gemini-2.5-flash in .env on a project that has access to it.
model = os.environ.get("SEARCH_AGENT_MODEL", "gemini-3.5-flash")

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
