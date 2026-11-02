"""
One-shot setup for the Vertex AI Search app used by the Betty's Bird Boutique agent.

Creates (idempotently) in the project named by DATASTORE_PROJECT_ID:
  1. a GCS bucket  <project>-bettys-docs  and uploads starter/docs/*.pdf
  2. a Vertex AI Search data store  (unstructured, layout-based chunking)
  3. an import of the PDFs into the data store (waits for indexing)
  4. a Search engine/app whose ID is written to DATASTORE_ENGINE_ID in starter/.env

Usage (from the project/ directory, with starter/.env filled in and
`gcloud auth application-default login` done):

    .venv/bin/python setup_search_app.py
"""
import json
import os
import pathlib
import sys
import time

import google.auth
from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession

HERE = pathlib.Path(__file__).resolve().parent
ENV_FILE = HERE / "starter" / ".env"
DOCS_DIR = HERE / "starter" / "docs"
DATASTORE_ID = "bettys-bird-boutique-docs"
ENGINE_ID = os.environ.get("DATASTORE_ENGINE_ID", "bettys-bird-boutique-engine")


def main() -> None:
  load_dotenv(ENV_FILE)
  project = os.environ.get("DATASTORE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
  location = os.environ.get("DATASTORE_LOCATION", "global")
  if not project:
    sys.exit("Set DATASTORE_PROJECT_ID (or GOOGLE_CLOUD_PROJECT) in starter/.env first.")

  creds, _ = google.auth.default()
  s = AuthorizedSession(creds)
  bucket = f"{project}-bettys-docs"
  de = f"https://discoveryengine.googleapis.com/v1/projects/{project}/locations/{location}/collections/default_collection"

  # 1. bucket + upload
  r = s.post(f"https://storage.googleapis.com/storage/v1/b?project={project}", json={"name": bucket, "location": "US"})
  print("bucket:", "created" if r.ok else ("exists" if r.status_code == 409 else r.text[:200]))
  for pdf in sorted(DOCS_DIR.glob("*.pdf")):
    r = s.post(
      f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o?uploadType=media&name={pdf.name}",
      data=pdf.read_bytes(), headers={"Content-Type": "application/pdf"})
    print(f"  upload {pdf.name}: {'ok' if r.ok else r.text[:200]}")

  # 2. data store
  r = s.post(f"{de}/dataStores?dataStoreId={DATASTORE_ID}", json={
    "displayName": "Betty's Bird Boutique Docs",
    "industryVertical": "GENERIC",
    "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
    "contentConfig": "CONTENT_REQUIRED",
    "documentProcessingConfig": {
      "chunkingConfig": {"layoutBasedChunkingConfig": {"chunkSize": 500, "includeAncestorHeadings": True}},
      "defaultParsingConfig": {"layoutParsingConfig": {}},
    },
  })
  print("data store:", "created" if r.ok else ("exists" if r.status_code == 409 else r.text[:200]))

  # 3. import documents and wait
  r = s.post(f"{de}/dataStores/{DATASTORE_ID}/branches/0/documents:import", json={
    "gcsSource": {"inputUris": [f"gs://{bucket}/*.pdf"], "dataSchema": "content"},
    "reconciliationMode": "INCREMENTAL",
  })
  if not r.ok:
    sys.exit(f"import failed: {r.text[:300]}")
  op = r.json()["name"]
  print("import started; waiting for indexing (typically 5-10 minutes) ...")
  while True:
    o = s.get(f"https://discoveryengine.googleapis.com/v1/{op}").json()
    if o.get("done"):
      print("import finished:", json.dumps(o.get("response", o.get("error")))[:200])
      break
    time.sleep(15)

  # 4. engine / app
  r = s.post(f"{de}/engines?engineId={ENGINE_ID}", json={
    "displayName": "Betty's Bird Boutique Engine",
    "solutionType": "SOLUTION_TYPE_SEARCH",
    "industryVertical": "GENERIC",
    "dataStoreIds": [DATASTORE_ID],
    "searchEngineConfig": {"searchTier": "SEARCH_TIER_STANDARD", "searchAddOns": ["SEARCH_ADD_ON_LLM"]},
  })
  print("engine:", "created" if r.ok else ("exists" if r.status_code == 409 else r.text[:200]))

  # write engine id back to .env
  text = ENV_FILE.read_text() if ENV_FILE.exists() else ""
  if "DATASTORE_ENGINE_ID=" in text:
    text = "\n".join(
      f"DATASTORE_ENGINE_ID={ENGINE_ID}" if line.startswith("DATASTORE_ENGINE_ID=") else line
      for line in text.splitlines()) + "\n"
  else:
    text += f"\nDATASTORE_ENGINE_ID={ENGINE_ID}\n"
  ENV_FILE.write_text(text)
  print(f"DATASTORE_ENGINE_ID={ENGINE_ID} written to {ENV_FILE}")


if __name__ == "__main__":
  main()
