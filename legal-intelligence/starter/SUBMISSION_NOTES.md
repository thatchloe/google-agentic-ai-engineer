# Legal Intelligence AI System: Submission Notes

The two earlier attempts contained the wrong project. The Legal Intelligence work was on a side branch, so the bird boutique project on `main` was submitted instead. This archive contains the Legal Intelligence source tree.

## Run it

```bash
pip install -r requirements.txt
python run_validation.py      # persona scores and quality ranking, no credentials needed
python tests/test_todos.py    # 31 tests, no credentials needed
cp .env.example .env          # add PROJECT_ID and the key path for a live run
python test_setup.py
uvicorn main:app --port 8010
```

Credentials are not included. The live run used `LOCATION=global` and `MODEL=gemini-3.5-flash`.

## Where each criterion is met

| Criterion | Code | Evidence |
| --- | --- | --- |
| Role-based personas | `BUSINESS_ANALYST_PERSONA`, `MARKET_RESEARCHER_PERSONA`, `STRATEGIC_CONSULTANT_PERSONA` in `src/prompts/personas.py` | All three score 1.00 (`evidence/validation_output.txt`) |
| Quality validation | `calculate_coherence_score()`, `calculate_groundedness_score()` in `src/core/quality_validator.py` | High 0.853 > medium 0.317 > low 0.051 (`evidence/validation_output.txt`) |
| Agent integration | `initialize_vertex_ai()`, `generate_section_content()`, `generate_complete_report()` in `src/core/agent_system.py` | Live run in `final_report.md`; 31 tests in `evidence/test_results.txt` |
| Production readiness | Exponential backoff in `generate_section_content()`; quality retries and graceful degradation in `generate_complete_report()` | Cost and timing in `evidence/run_metrics.txt` and `evidence/live_run_log.txt` |
| Best practices | Run-tagged logging in `src/utils/logger.py`; per-section audit trail in report metadata; bias rules in `src/prompts/personas.py` | `metadata.audit_trail` in `evidence/run_metrics.txt` |

## Live run result

Run `1b361ee1` returned HTTP 200 in 113.2 seconds with 6 sections, 32,558 tokens, an estimated cost of $0.2553, and a confidence score of 0.94.

Context passing is visible in the output. The 25% base-case probability set in Liability Assessment is reused in Damage Calculation and Risk Assessment. `audit_trail[].context_sections` lists the sections each prompt received, and `test_context_passes_between_sections` checks the chaining.

## Design decisions and limits

- **Six sections:** the report follows the starter's six-section sequence, not the four in the criterion wording.
- **Persona keys:** the code keeps the starter's persona names. The TODO labels in the test summary use the instructions' names.
- **Retries:** no retry fired in the live run, because every section passed first time. The backoff, quality-retry, and degradation paths are shown by unit tests with mocked failures.
- **Cost:** figures are estimates from list prices in `MODEL_PRICING`, not billed amounts. The gemini-3.5-flash rate comes from third-party listings.
- **Scoring:** the quality scores are rule-based heuristics for structure and keywords. They catch weak output but do not check whether a legal conclusion is correct.
- **Legal content:** the report is AI-generated course work, not legal advice. Citations are tagged for attorney verification.
- **Screenshots:** the images in `screenshots/` were rendered from captured output of the real runs, not taken from a terminal window.
