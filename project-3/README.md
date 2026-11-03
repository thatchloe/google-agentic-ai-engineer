# Taking Wing: Building an Agentic Bird Brain

You’re the brand-new owner of **Betty’s Bird Boutique**, a pet store that caters to people who are buying birds and all the food and accessories they may need. You don’t actually know much about birds, but you have always wanted to own a store, and the opportunity came up.

### The Challenge
Unfortunately, the store's website is pretty basic. You want to enhance it by adding an AI agent to answer customer questions about birds in general and what your store offers.

A key requirement is that the agent should not take orders—the goal is to encourage customers to come into the store and establish a good relationship.

### The Goal
You will build an agent that can answer questions about your store and birds based on information from three primary sources:

- **A price database** stored in a relational database.
- **PDF or other text files** containing information about your store, such as hours of operation and its history.
- **Web-sourced information** for general questions about birds.

The agent must also have **guardrails** to avoid answering questions that are unrelated to birds or your store. Before deploying to a live website, you will test and refine the agent in a dedicated development environment.

---

## Project Summary
Using **Google’s Agent Development Kit (ADK)** and a **GCP** runtime environment, you will build a simple customer support agent that answers questions topically relevant to your store. It should be able to carry on a multi-turn conversation, remembering facts from previous turns, but it does not need to store information from previous conversations.

The agent should have three tools that it is able to use:

1. **Look up prices:** Connect to a relational database to find the price of a specific item.
2. **Answer store-specific questions:** Use PDF documents as a knowledge base to answer questions about:

- The store hours
- The store location
- The history of the store, the current staff, their birds, etc.
3. **Answer general questions about birds:** Use information from Google Search and the web.

The agent should also have guardrails, implemented through prompt engineering or tools, to avoid answering questions that are not related to birds or your store.

You will develop this project using a workspace where you can run the python script in the **“adk web” testing environment**. This will allow you to have conversations with your agent, providing a simulation of the customer experience along with valuable debugging feedback.

---

# Betty's Bird Boutique Agent

A customer-support agent for Betty's Bird Boutique built with Google's Agent
Development Kit (ADK). It answers questions about the store (hours, location,
history, staff), about birds in general, and about product prices. It never takes
orders; it invites customers into the store instead.

The root agent (`starter/agent.py`) uses three tools, each built a different way:

| Tool | Built with | Source of truth |
|------|-----------|-----------------|
| `get_product_price` | MCP Toolbox (`starter/tools.yaml`) | `betty.products` table in MySQL |
| `datastore_search_tool` | Vertex AI Search via `google-cloud-discoveryengine` (`starter/datastore.py`) | PDFs in `starter/docs/` indexed in a Vertex AI Search datastore |
| `search_agent` | `AgentTool` wrapping a Gemini agent with Grounding with Google Search (`starter/search_agent.py`) | The web |
| `get_current_date` | Plain Python function tool (`starter/date_tool.py`) | The system clock, so "Are you open today?" works |

Short-term memory is an `InMemorySessionService`, so the agent remembers earlier turns
of the current conversation but nothing across restarts.

## Getting Started

### Dependencies

* Python 3.11+
* A Google Cloud project with Vertex AI and Discovery Engine (Vertex AI Search) APIs enabled
* A Vertex AI Search app ("engine") backed by a GCS bucket containing the PDFs from `starter/docs/`
* MySQL (Cloud SQL for MySQL, or a local server) loaded with `starter/docs/betty_db.sql`
* The MCP Toolbox server binary (`brew install mcp-toolbox`, or download from the
  [MCP Toolbox releases](https://github.com/googleapis/mcp-toolbox))
* Google credentials: either `gcloud auth application-default login`, or a service-account
  JSON key referenced by `GOOGLE_APPLICATION_CREDENTIALS`

Python packages (see `starter/requirements.txt`):

```
google-adk>=1.13.0
google-cloud-discoveryengine>=0.13.11
toolbox-core>=0.5.0
```

### Installation

All commands are run from this `project/` directory.

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r starter/requirements.txt
   ```

2. Create `starter/.env` with your configuration:

   ```
   GOOGLE_GENAI_USE_VERTEXAI=TRUE
   GOOGLE_CLOUD_PROJECT=<your project ID>
   # "global" is required for the Gemini 3.x models; use us-central1 if your
   # project has access to the gemini-2.5 family in that region.
   GOOGLE_CLOUD_LOCATION=global

   # Vertex AI Search
   DATASTORE_PROJECT_ID=<project ID that hosts the search app>
   DATASTORE_LOCATION=global
   DATASTORE_ENGINE_ID=<your Vertex AI Search app ID>

   # MySQL (used by the MCP Toolbox server)
   MYSQL_HOST=<Cloud SQL public IP, or 127.0.0.1 for local>
   MYSQL_PORT=3306
   MYSQL_USER=toolbox
   MYSQL_PASSWORD=<password>

   # Where the MCP Toolbox server listens
   TOOLBOX_URL=http://127.0.0.1:5001

   # Model overrides (optional). The search agent defaults to gemini-2.5-flash and
   # the root agent to gemini-3.5-flash. The Udacity lab project used for the
   # screenshots returns 404 for the whole gemini-2.0/2.5 family, so there the
   # search agent is pointed at the Flash tier that is served:
   # SEARCH_AGENT_MODEL=gemini-3.5-flash
   # ROOT_AGENT_MODEL=gemini-3.5-flash

   # Only if you use a service account instead of application-default credentials
   # GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json
   ```

   Note: port 5000 is taken by AirPlay Receiver on recent versions of macOS, which is why
   the Toolbox runs on 5001 here.

3. Load the product database and create a read-only user (works for Cloud SQL or a local server):

   ```bash
   mysql -h <MYSQL_HOST> -u root -p < starter/docs/betty_db.sql
   mysql -h <MYSQL_HOST> -u root -p -e "CREATE USER IF NOT EXISTS 'toolbox'@'%' IDENTIFIED BY '<password>'; GRANT SELECT ON betty.* TO 'toolbox'@'%'; FLUSH PRIVILEGES;"
   ```

4. Create the Vertex AI Search app. Either run the provided script, which creates the
   bucket, uploads the PDFs, creates the data store and search app, waits for indexing and
   writes `DATASTORE_ENGINE_ID` into `starter/.env`:

   ```bash
   .venv/bin/python setup_search_app.py
   ```

   or do it by hand in the Cloud console: open **AI Applications**, create a **Search** app
   with a new **Cloud Storage** data store pointing at a bucket where you have uploaded
   `bettys-history.pdf`, `bettys-hours.pdf` and `bettys-staff.pdf` (unstructured documents,
   with document chunking enabled). Wait for indexing to finish, then copy the app's ID into
   `DATASTORE_ENGINE_ID`.

5. Start the MCP Toolbox server in its own terminal (it needs the MYSQL_* variables exported):

   ```bash
   cd starter
   export $(grep -v '^#' .env | xargs)
   toolbox --config tools.yaml --port 5001
   # (older Toolbox releases use --tools-file instead of --config)
   ```

6. Start the agent in a second terminal and open the URL it prints (usually
   http://127.0.0.1:8000), then pick `starter` from the app drop-down:

   ```bash
   source .venv/bin/activate
   adk web
   ```

## Testing

There is no automated test suite; the agent is tested interactively in `adk web`.
Each tool can also be exercised on its own.

### Break Down Tests

* **Toolbox / database tool** - confirms `tools.yaml`, the MySQL user and the data are correct:

  ```bash
  .venv/bin/python -c "from toolbox_core import ToolboxSyncClient; c = ToolboxSyncClient('http://127.0.0.1:5001'); print(c.load_tool('get_product_price')(product_name='seed'))"
  ```

  Expected output lists `Bird Seed Mix` and `Sunflower Seeds` with their prices.

* **Vertex AI Search tool** - confirms the datastore is indexed and reachable:

  ```bash
  cd project && .venv/bin/python -c "from dotenv import load_dotenv; load_dotenv('starter/.env'); from starter.datastore import datastore_search_tool; print(datastore_search_tool('Thursday hours'))"
  ```

* **Full conversation** - in `adk web`, start a new session and ask, in order:

  1. *When are you open on Thursday?* (datastore tool)
  2. *Who is Betty?* (datastore tool)
  3. *What kind of bird did she own?* (web search tool, resolves "she" from context)
  4. *What do they eat?* (web search tool, resolves "they" from context)
  5. *Can I buy that from you?* (database tool; the agent quotes a price and invites the
     customer in rather than taking an order)

  Also try an off-topic question such as *Help me with my calculus homework* to confirm the
  guardrail declines politely.

  The **Events** tab in `adk web` shows which tool was called for each turn, which is useful
  when comparing models. Models are swapped with the `ROOT_AGENT_MODEL` and
  `SEARCH_AGENT_MODEL` environment variables.

  **Search agent model.** `starter/search_agent.py` defaults to `gemini-2.5-flash` (Gemini 2.5
  family) and the comment above the model line explains why: the search agent runs inside a
  root-agent turn, so latency matters more than reasoning depth; it only has to run one grounded
  search and write a short cited summary; and it is called for every general bird question, so
  the cheaper Flash tier matters. The project guide suggests comparing `gemini-2.5-pro`,
  `gemini-2.5-flash` and `gemini-2.5-flash-lite`. The lab project used for this submission has
  no access to the 2.5 family (404 from Vertex AI), so the equivalent current tiers were
  compared instead (`gemini-3.1-pro-preview`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`) on the
  conversation above: the lite model is faster but occasionally skips the search, and the pro
  model is about 3x slower with no better answers. Flash is the best balance, which is why the
  default is 2.5 Flash and the lab `.env` sets `SEARCH_AGENT_MODEL=gemini-3.5-flash`.

## Project Instructions

### Screenshots

All screenshots are in [`screenshots/`](screenshots/) and come from **one `adk web` session,
`7e064897-8557-44d4-a3f3-098476ec61ef`**, recorded on 2026-11-03 with the Events panel open.
The session was renamed to its own ID so the ID is visible in the top bar of every screenshot,
and the session drawer (which also lists the ID) is open in the conversation shots. Files are
numbered in conversation order; `-conversation` shows the user request and agent reply,
`-request` shows the selected tool-call event (function name and arguments) and `-response`
shows the function response returned by the tool.

| Turn | User request | Tool(s) | Files |
|------|--------------|---------|-------|
| 1 | What are the store's working hours? | `datastore_search_tool` | `01-datastore-store-hours-*` (response is the raw `bettys-hours` passage) |
| 2 | Who is Betty? | `datastore_search_tool` | `02-datastore-who-is-betty-*` (response is the raw `bettys-history` passage) |
| 3 | What kind of bird did she own? | none (answered from turn 2's context) | `03-datastore-bettys-bird-conversation` |
| 4 | What do they eat? | `search_agent` (Grounding with Google Search) | `04-websearch-what-they-eat-*`; `-response-2-sources` shows the Sources list at the end of the grounded result |
| 5 | Can I buy that from you? | `get_product_price` x4 (MySQL via MCP Toolbox) | `05-database-can-i-buy-*`; prices quoted, no order taken |
| 6 | How much is a Bird Bath? | `get_product_price` | `06-database-bird-bath-price-*`; request `"Bird Bath"`, response `{"product_name":"Bird Bath","price":"75.99"}` |
| 7 | Do you sell hamster wheels? | `get_product_price` | `07-database-not-found-*`; response `null`, agent says the item is not carried |
| 8 | What are the latest news or trends in pet bird keeping this year? | `get_current_date`, `search_agent` | `08-websearch-current-info-*`; current-information query with Sources |
| 9 | Help me with my calculus homework | none (guardrail) | `09-guardrail-off-topic-conversation` |
| all | whole conversation, scrolled top to bottom | | `10-full-conversation-1` to `-5` |

To reproduce: start the Toolbox and `adk web` as described above, open a **New Session**, ask
the questions in the table in order, then click each tool-call chip in the chat to show its
request or response in the left panel.

### Deliverables


1. `starter/agent.py` with the in-memory session service, the three tools, and the root agent.
2. `starter/agent-prompt.txt` with the on-topic guardrail and the "no orders" rule.
3. `starter/tools.yaml` defining the `get_product_price` tool for the MCP Toolbox.
4. `starter/datastore.py` implementing `search()` and `datastore_search_tool()`.
5. `starter/search_agent.py` and `starter/search-prompt.txt` implementing the grounded search `AgentTool`.
6. `starter/date_tool.py`, the date-awareness tool from the "stand out" suggestions.
7. `screenshots/` with the conversation and tool-call evidence listed above.

## Built With

* [Google Agent Development Kit](https://google.github.io/adk-docs/) - Agent framework, `adk web` previewer, `AgentTool`, `google_search`
* [Vertex AI (Gemini)](https://cloud.google.com/vertex-ai) - `gemini-2.5-flash` for the search agent (`gemini-3.5-flash` in the lab project), `gemini-3.5-flash` for the root agent
* [Vertex AI Search / Discovery Engine](https://cloud.google.com/generative-ai-app-builder/docs) - Document retrieval over the store PDFs
* [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox) - Exposes the MySQL price query as a tool
* [Cloud SQL for MySQL](https://cloud.google.com/sql/mysql) - Product price database

## License
[License](../LICENSE.md)
