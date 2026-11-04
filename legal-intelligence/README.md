# Legal Intelligence AI System - Project

Welcome to the Legal Intelligence AI System project! You've been hired as the Lead AI Architect at LexiMind Solutions to fix a broken AI system that analyzes legal cases.

## Project Overview

The engineering team has built the infrastructure, but the AI agents don't know how to think, analyze, or communicate. Your mission is to complete 8 TODOs to make the system intelligent.

### What's Working ✅
- FastAPI server and endpoints
- Data models and validation
- Logging and monitoring
- Basic infrastructure

### What's Broken ❌
- Can't connect to Vertex AI (TODO 1)
- Can't generate content (TODO 2)
- Can't create complete reports (TODO 3)
- No quality validation (TODOs 4-5)
- Agents have no personalities (TODOs 6-8)

## Project Structure

```
project/
├── starter/              # Your working directory (broken code)
│   ├── main.py          # FastAPI application
│   ├── src/
│   │   ├── core/        # Core system components
│   │   │   ├── agent_system.py    # TODOs 1-3: AI integration
│   │   │   └── quality_validator.py # TODOs 4-5: Quality scoring
│   │   ├── prompts/     # Agent personas
│   │   │   └── personas.py         # TODOs 6-8: Expert personas
│   │   ├── models/      # Data models (working)
│   │   └── utils/       # Utilities (working)
│   ├── tests/           # Test suite
│   └── test_scenarios.json # Sample legal cases
│
└── solution/            # Reference implementation (don't peek!)
```

## The 8 TODOs

### TODO 1: Initialize Vertex AI (agent_system.py)
Connect to Google's Vertex AI to enable AI capabilities.

### TODO 2: Generate Section Content (agent_system.py)
Implement content generation with retry logic and token tracking.

### TODO 3: Generate Complete Report (agent_system.py)
Orchestrate multiple agents to create comprehensive legal analysis.

### TODO 4: Coherence Scoring (quality_validator.py)
Build an algorithm to score logical flow and structure.

### TODO 5: Groundedness Scoring (quality_validator.py)
Build an algorithm to score technical accuracy and relevance.

### TODO 6: Business Analyst Persona (personas.py)
Create a quantitative analysis expert persona.

### TODO 7: Market Researcher Persona (personas.py)
Create a competitive intelligence expert persona.

### TODO 8: Strategic Consultant Persona (personas.py)
Create a strategic planning expert persona.

## Getting Started

### Prerequisites

1. **Google Cloud Project** with Vertex AI API enabled
2. **Python 3.9+**
3. **Access to Google Cloud Console** (web interface)

### Setup Instructions

1. **Set up Google Cloud Project**:
     - Creating/selecting a project
     - Enabling APIs via Console
     - Creating service accounts
     - Downloading JSON keys
   - No command-line tools needed!

2. **Navigate to the starter directory**:
```bash
cd project/starter
```

4. **Configure your environment**:
   - Create a `.env` file (copy from `.env.example`)
   - Add your Project ID from Google Cloud Console
   - Place your service account JSON key in the project
   - Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

5. **Test your setup**:
```bash
# First, test your Google Cloud configuration
python test_setup.py

# Once setup test passes, run the project tests (will fail initially)
python tests/test_todos.py
```

## Working on the Project

### Step-by-Step Approach

1. **Start with TODO 1**: Get Vertex AI connection working first
2. **Then TODOs 2-3**: Implement content generation and report assembly
3. **Then TODOs 4-5**: Add quality validation algorithms
4. **Finally TODOs 6-8**: Create the expert personas

### Running the System

1. **Start the server**:
```bash
python main.py
```

2. **Open the API documentation**:
Navigate to `http://localhost:8000/docs`

3. **Test with sample scenario**:
```bash
# POST to /analyze endpoint with test_scenarios.json data
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d @test_scenarios.json
```

### Testing Your Implementation

Run tests for specific TODOs:
```bash
# Test all TODOs
python tests/test_todos.py

# Test specific TODO (example)
python -m unittest tests.test_todos.TestTODO1_VertexAIInitialization
```

## Tips for Success

### For TODO 1 (Vertex AI)
- Use `vertexai.init(project=..., location=...)`
- Create `GenerativeModel(model_name)`
- Test with a simple prompt
- Handle exceptions gracefully

### For TODO 2 (Content Generation)
- Build prompt with `self._build_prompt()`
- Use `self.model.generate_content()`
- Implement retry with exponential backoff
- Track tokens from `response.usage_metadata`

### For TODO 3 (Complete Report)
- Define section sequence with personas
- Pass previous sections for context
- Validate quality and retry if needed
- Assemble all sections into report

### For TODOs 4-5 (Quality Scoring)
- Score from 0.0 to 1.0
- Check multiple quality indicators
- Weight different components
- Return combined score

### For TODOs 6-8 (Personas)
- Minimum 150 words each
- Include role, expertise, style, frameworks
- Make them distinct and specialized
- Focus on legal/business expertise

## Validation Checklist

Before submitting, ensure:

- [ ] All tests pass (`python tests/test_todos.py`)
- [ ] Server starts without errors
- [ ] Can generate reports via API
- [ ] Quality scores are > 0.7
- [ ] Each persona is distinct and complete

## Common Issues

### "PROJECT_ID not set"
- Check your `.env` file has `PROJECT_ID=your-project-id`
- Make sure `.env` is in the correct directory
- Verify the project ID matches your Google Cloud Console

### "Not authenticated"
- Ensure your service account JSON key file exists
- Check `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`
- Verify the service account has proper roles (Vertex AI User)
- Run `python test_setup.py` to diagnose authentication issues

### "Vertex AI not enabled"
- Go to Google Cloud Console → APIs & Services
- Search for "Vertex AI API" and click Enable
- Wait 2-3 minutes for the API to activate
- Also enable Cloud Storage and Logging APIs

### Tests failing
- Start with TODO 1 and work sequentially
- Check test output for specific failure reasons
- Ensure all dependencies are installed
- Run `python test_setup.py` first to verify setup

## Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Reference](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

If you get stuck:
1. Review the test file for hints
2. Check the error messages carefully
3. Refer to the course exercises for similar patterns
4. Remember: The infrastructure works, you're just adding the intelligence!

Good luck, Lead AI Architect! 🚀

---

# Project Brief: Saving the "TechFlow" Case

Welcome to your first day as the Lead AI Architect at LexiMind Solutions!

You've just joined a cutting-edge LegalTech startup with a problem. The engineering team has built an enterprise-grade infrastructure, but there's one piece is missing: The Intelligence.

You have been brought in to implement "Agentic Reasoning" and teach AI agents how to think.

## Saving the "TechFlow" Case

The firm has just landed a large client, TechFlow Innovations, who is facing a complex intellectual property dispute.

They are looking to your new Legal Intelligence Agent System to save the day. But when they run the system, it fails. The agents don't know who they are, how to reason through the problem, or how to talk to each other.

## Your Project is to Fix the Legal Intelligence Agent System

- Define the Personas. You need to craft prompts that give the system personas, defining exactly how it should speak, think, and structure its analysis.
- You must implement Chain-of-Thought (CoT) logic so they break down complex liability questions step-by-step.
- You will use Vertex AI's Optimization tools to mathematically tune your prompts for maximum precision and cost-efficiency.
- You need to build a Context Chain so that input and output flow from one specialist to another.
- You will implement a Quality Validation Loop that catches low-confidence answers and forces the agents to "try again" until the output is better.

By the end of this project, you will have a functioning, multi-agent system that takes a raw legal complaint and outputs a professional, court-ready strategic analysis.

## Assessment

Your project will be assessed by a Udacity mentor against a rubric you'll find on the following pages. Read the rubric before starting the project, check it while you're working on the project, and check it before you submit your project.

---

# Legal Intelligence AI System GCP Configuration Guide

This guide will walk you through setting up your Google Cloud Project using the Google Cloud Console (web interface). You will NOT need the gcloud CLI for this setup, but if you want to use gcloud locally, you absolutely can. You'll need to get your GCP credentials from the Cloud Resources Tab regardless if you set up your project with the Google Cloud web console or gcloud. You'll find the starter code for the project in the workspace on the next page.

## Prerequisites

Before starting:

1. Access your Google Cloud Platform credentials by opening Cloud Resources in the classroom.
2. Start the cloud resources, click on Start Cloud Resources
3. Document your Google Cloud Credentials somewhere, you'll need these credentials and information for various parts of the project.
4. Open the Google Cloud web console, ideally in an incognito window. If not in an incognito window, make sure you've signed out of Google accounts in your browser. Use the provided email and password to sign into the Google Cloud Console

## Step 2: Select your Project

1. Click the project dropdown
2. Select your project from the list
3. Note your Project ID from the Cloud resources tab or the dashboard.

Copy your Project ID somewhere safe - you'll need it for the `.env` file!

## Step 2: Enable Required APIs

You need to enable several APIs for the Legal Intelligence System to work.

### Enable Vertex AI API:

1. In the search bar at the top, type "APIs & Services"
2. Click on "APIs & Services" from the results
3. Click "+ ENABLE APIS AND SERVICES" button
4. Search and "ENABLE" Agent Platform API.
5. Wait for the API to be enabled (this may take 1-2 minutes)

### Enable Additional Required APIs:

Repeat the above process for these APIs:

- IAM Service Account Credentials API (for authentication, this API is usually auto-enabled but you can double check it.)

Each API should show "API Enabled ✓" when complete.

## Step 5: Create a Service Account

Service accounts allow your application to authenticate with Google Cloud.

1. In the search bar, type "IAM & Admin"
2. Click on "IAM & Admin" from the results
3. In the left sidebar, click "Service Accounts"
4. Click "+ CREATE SERVICE ACCOUNT" at the top

### Step 5.1: Service Account Details

- Service account name: `legal-ai-agent`
- Service account ID: (auto-generated, like `legal-ai-agent@your-project.iam.gserviceaccount.com`)
- Description: "Service account for Legal Intelligence AI System"
- Click "CREATE AND CONTINUE"

### Step 5.2: Grant Permissions

Add the following roles to your service account:

1. Click "Select a role" dropdown
2. Search and add these roles (one at a time):
   - Vertex AI User (`roles/aiplatform.user`)
3. After adding the role, click "CONTINUE"

### Step 5.3: Grant User Access (Optional)

You can skip this step - click "DONE"

## Step 6: Create and Download Service Account Key

1. You should now see your service account in the list
2. Before downloading a Service Account Key for a newly created service account, ensure that your IAM user has the necessary permissions to create one. To do this, first grant the Editor role to your own IAM user. You can find your IAM username within the Udacity cloud lab environment. Once identified, proceed to attach the Editor role to your IAM user.
3. Click on your service account email (`legal-ai-agent@...`)
4. Click the "KEYS" tab at the top
5. Click "ADD KEY" → "Create new key"
6. Select "JSON" as the key type
7. Click "CREATE"
8. Download the JSON file to your computer containing this key

Save this file securely - you cannot download it again!

- Rename it to something memorable like `service-account-key.json`
- You'll upload/use this in your project workspace

## Step 7: Gather Your Configuration Values

You now have everything needed. Collect these values:

- PROJECT_ID
- Service Account file name
- Key File

## Step 8: Configure Your Project Workspace

### 8.1: Create the .env File

In your Udacity workspace, create a file named `.env` with the following content:

```bash
# Google Cloud Configuration
PROJECT_ID=your-project-id-here
MODEL=gemini-2.0-flash

# Service Account Authentication
GOOGLE_APPLICATION_CREDENTIALS=/workspace/service-account-key.json

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
PORT=8000
```

Replace `your-project-id-here` with your actual Project ID.

### 8.2: Upload Your Service Account Key

1. Upload the JSON key file you downloaded to your project root directory
2. Rename it to match the name in your `.env` file (`service-account-key.json`)
3. IMPORTANT: Add this file to your `.gitignore` to prevent accidentally committing it!

Finally, run this command in your Udacity workspace terminal

```bash
source /workspace/project/starter/.env
```

Example Directory Structure:

```
project/starter/
├── .env                        # Your configuration
├── service-account-key.json    # Your service account key
├── .gitignore                  # Should include *.json and .env
├── main.py                     # Application entry point
└── src/                        # Source code
```

## Troubleshooting Errors

### "API not enabled" Error

- Go back to Step 4 and ensure all APIs are enabled
- Wait 2-3 minutes after enabling APIs before testing

### "Permission denied" Error

- Verify your service account has all required roles (Step 5.2)
- Check that your JSON key file path is correct in `.env`

### "Invalid project ID" Error

- Double-check your PROJECT_ID in the `.env` file
- Ensure there are no extra spaces or quotes

### "Quota exceeded" Error

- You may have hit usage limits
- Check the Quotas page in Google Cloud Console

---

# Implementation Instructions - Legal Intelligence AI System

Your project will be assessed by a Udacity mentor against a rubric you'll find on the following page. Read the rubric before starting the project, check it while you're working on the project, and check it before you submit your project.

You will fix a broken Legal Intelligence AI System by completing 8 TODOs. The system analyzes intellectual property disputes using specialized AI personas with Google's Gemini model.

## Prerequisites

Before starting, ensure your environment is configured:

```bash
cd project/starter
python test_setup.py
```

This should show:

```
✅ Environment file exists
✅ Project ID is set
✅ Service account key exists
✅ Vertex AI API is enabled
```

If any checks fail, review the ensetup instructions.

## Implementation Guide

### Phase 1: Core Agent System (TODOs 1-3)

These TODOs establish the foundation. Complete them in order.

**TODO 1: Initialize Vertex AI**

- File: `project/starter/src/core/agent_system.py`
- Current State: System fails to connect to Vertex AI
- Your Task: Initialize Vertex AI and create the generative model

**TODO 2: Generate Section Content**

- File: `project/starter/src/core/agent_system.py`
- Current State: Content generation always fails
- Your Task: Implement content generation with retry logic

**TODO 3: Generate Complete Report**

- File: `project/starter/src/core/agent_system.py`
- Current State: Report generation not orchestrated
- Your Task: Orchestrate multi-section report generation with context chaining

### Phase 2: Quality Validation (TODOs 4-5)

**TODO 4: Coherence Scoring Algorithm**

- File: `project/starter/src/core/quality_validator.py`
- Current State: Always returns 0.0
- Your Task: Implement coherence scoring based on structure and logical flow

**TODO 5: Groundedness Scoring Algorithm**

- File: `project/starter/src/core/quality_validator.py` (line 188)
- Current State: Always returns 0.0
- Your Task: Implement groundedness scoring for legal domain content

### Phase 3: Legal Personas (TODOs 6-8)

Define specialized AI personas for legal analysis.

**TODO 6: IP Litigation Expert Persona**

- File: `project/starter/src/prompts/personas.py`
- Current State: Generic placeholder persona
- Your Task: Create comprehensive IP litigation expert persona

**TODO 7: IP Valuation Specialist Persona**

- File: `project/starter/src/prompts/personas.py` (line 82)
- Current State: Generic placeholder persona
- Your Task: Create comprehensive IP valuation specialist persona

**TODO 8: Patent Researcher Persona**

- File: `project/starter/src/prompts/personas.py` (line 127)
- Current State: Generic placeholder persona
- Your Task: Create comprehensive patent researcher persona

## Testing Your Implementation

```bash
cd project/starter
python tests/test_todos.py
```

Expected output when complete:

```
TODO 1: Vertex AI Initialization ........... ✓ PASSED
TODO 2: Generate Section Content ........... ✓ PASSED
TODO 3: Generate Complete Report ........... ✓ PASSED
TODO 4: Coherence Scoring .................. ✓ PASSED
TODO 5: Groundedness Scoring ............... ✓ PASSED
TODO 6: IP Litigation Expert Persona ....... ✓ PASSED
TODO 7: IP Valuation Specialist Persona .... ✓ PASSED
TODO 8: Patent Researcher Persona .......... ✓ PASSED

ALL TODOS COMPLETED! ✅
```

Take a screenshot of your complete TODO test running and the TODOs PASSED.

## Test the Complete System

```bash
# Start the server
python main.py

# In another terminal, test the API
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "Tech company accused of patent infringement on mobile payment processing system",
    "context": "Defendant has prior art from 2015, plaintiff filed patent in 2018"
  }'
```

Take a screenshot of the output of the API test in the terminal.

## Success Criteria

Your implementation is successful when:

- All 8 TODO tests pass
- The API returns a complete analysis report with 4 sections
- Each section has quality scores > 0.7
- Total generation cost is displayed (approximately $0.01-0.02)
- Report includes all legal analysis sections with context chaining
- Include the output report in a separate file called `final_report.md`

## Common Issues and Solutions

**Issue: "Vertex AI initialization failed"**

Solution: Verify your `.env` file has correct PROJECT_ID and credentials path

**Issue: Quality scores below 0.7**

Solution: Ensure personas are comprehensive (>200 words) with proper legal terminology

**Issue: Test failures on TODOs 4-5**

Solution: Check that your scoring algorithms return values between 0.0 and 1.0

**Issue: "Model not found" error**

Solution: Use exact models that are available for the model name

## Submission Checklist

- [ ] All 8 TODOs implemented
- [ ] All tests passing
- [ ] Server runs without errors
- [ ] API endpoint returns valid JSON response
- [ ] Quality scores meet thresholds
- [ ] Code follows existing patterns and style
- [ ] Screenshots capturing test of the complete system
- [ ] `final_report.md` file with output of your final test and the generated report.
