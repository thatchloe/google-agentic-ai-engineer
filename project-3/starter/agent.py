import os

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient

from .date_tool import get_current_date
from .datastore import datastore_search_tool
from .search_agent import search_agent_tool

# Configure short-term session to use the in-memory service.
# The agent remembers facts from earlier turns in the same conversation, but
# nothing persists once the process exits (no long-term memory is required).
session_service = InMemorySessionService()

# Read the instructions from a file in the same
# directory as this agent.py file.
script_dir = os.path.dirname(os.path.abspath(__file__))
instruction_file_path = os.path.join(script_dir, "agent-prompt.txt")
with open(instruction_file_path, "r") as f:
    instruction = f.read()

# Model selection. The project guide suggests comparing gemini-2.5-pro,
# gemini-2.5-flash and gemini-2.5-flash-lite, but the lab project used here has
# no access to the 2.5 family (404 from Vertex AI), so the equivalent current
# tiers were compared instead: gemini-3.1-pro-preview (pro), gemini-3.5-flash
# (flash) and gemini-3.5-flash-lite (lite). Flash is the best balance of quality
# and latency for this multi-tool use case. Override with ROOT_AGENT_MODEL.
# Note: these models are only served from the "global" location.
model = os.environ.get("ROOT_AGENT_MODEL", "gemini-3.5-flash")

# Set up the tools that we will be using for the root agent
tools = [
    # Tool 2: store-document Q&A via Vertex AI Search (hours, location, history, staff)
    datastore_search_tool,
    # Tool 3: general bird knowledge via Grounding with Google Search (AgentTool)
    search_agent_tool,
    # Extra: today's date and weekday so the agent can answer "are you open today?"
    get_current_date,
]

# Tool 1: product price lookup via the MCP Toolbox server (Cloud SQL / MySQL).
toolbox_url = os.environ.get("TOOLBOX_URL", "http://127.0.0.1:5000")
try:
    db_client = ToolboxSyncClient(toolbox_url)
    tools.append(db_client.load_tool("get_product_price"))
    print(f"Loaded get_product_price from Toolbox at {toolbox_url}")
except Exception as e:  # noqa: BLE001
    # Keep the agent usable (document + web search) even if the Toolbox server
    # is not running, but make the problem obvious in the console.
    print(f"WARNING: could not load Toolbox tools from {toolbox_url}: {e}")

# Create our agent
root_agent = Agent(
    name="bettys_bird_boutique_agent",
    description=(
        "Customer-support agent for Betty's Bird Boutique. Answers questions about "
        "the store (hours, location, history, staff), general bird knowledge, and "
        "product prices. Does not take orders."
    ),
    instruction=instruction,
    model=model,
    tools=tools,
)
