import os

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

# Definition of a tool that accesses a Vertex AI Search Datastore

#
# Attribution: the search() function is based on the sample code provided by
# Google at
# https://cloud.google.com/generative-ai-app-builder/docs/samples/genappbuilder-search
#
# Choices made relative to that sample:
#   * The request and its nested specs are plain dicts rather than instances of
#     the discoveryengine_v1 classes. The classes are generated from protobufs,
#     so many IDEs cannot resolve them and flag false errors; the client
#     accepts dicts with exactly the same field names and converts them. The
#     class each dict stands in for is named in a comment next to it. Enums are
#     still referenced through the classes so the values are type-checked.
#     Definitions: https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types
#   * Results are requested in CHUNKS mode (with one neighbouring chunk on each
#     side) instead of whole documents, because the LLM only needs the passage
#     that answers the question, not the entire PDF.
#   * Query expansion and spell correction are set to AUTO so that customer
#     typos ("thursday hours", "who is bety") still find the right passage.
#
def search(
    project_id: str,
    location: str,
    engine_id: str,
    search_query: str,
) -> list[str]:
  #  For more information, refer to:
  # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
  client_options = (
    ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
    if location != "global"
    else None
  )

  # Create a client
  client = discoveryengine.SearchServiceClient(client_options=client_options)

  # The full resource name of the search app serving config
  serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

  # discoveryengine.SearchRequest.ContentSearchSpec
  # Ask for the matching chunks of the PDFs rather than whole documents, which
  # gives the LLM compact, relevant text.
  content_search_spec = {
    "search_result_mode": discoveryengine.SearchRequest.ContentSearchSpec.SearchResultMode.CHUNKS,
    # discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec
    "chunk_spec": {
      "num_previous_chunks": 1,
      "num_next_chunks": 1,
    },
  }

  # discoveryengine.SearchRequest.QueryExpansionSpec
  query_expansion_spec = {
    "condition": discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
  }

  # discoveryengine.SearchRequest.SpellCorrectionSpec
  spell_correction_spec = {
    "mode": discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO,
  }

  # discoveryengine.SearchRequest
  request = {
    "serving_config": serving_config,
    "query": search_query,
    "page_size": 5,
    "content_search_spec": content_search_spec,
    "query_expansion_spec": query_expansion_spec,
    "spell_correction_spec": spell_correction_spec,
  }

  page_result = client.search(request)

  # Format and return the results as a list of text passages.
  results: list[str] = []
  for result in page_result:
    chunk = result.chunk
    if not chunk or not chunk.content:
      continue
    # Stitch the neighbouring chunks (if requested) around the matched chunk so
    # the model sees a little context on either side.
    text_parts = [c.content for c in chunk.chunk_metadata.previous_chunks]
    text_parts.append(chunk.content)
    text_parts.extend(c.content for c in chunk.chunk_metadata.next_chunks)
    title = chunk.document_metadata.title if chunk.document_metadata else ""
    passage = "\n".join(p for p in text_parts if p)
    results.append(f"[{title}]\n{passage}" if title else passage)

  return results


def datastore_search_tool(search_query: str) -> dict:
  """
  Searches Betty's Bird Boutique's own documents for information about the store:
  hours of operation, location/address, the history of the store, the current
  staff, and the birds that the staff own.

  Use this tool for ANY question about the store itself or its people. Do not
  use it for general bird facts or product prices.

  Args:
      search_query (str): A natural-language description of the store information
          the customer is looking for, e.g. "Thursday opening hours" or "who is Betty".

  Returns:
      dict: {"status": "success", "results": [passage, ...]} with the most relevant
      text passages from the store documents, or {"status": "not_found"} if nothing
      matched, or {"status": "error", "message": ...} if the search failed.
  """
  # Configuration comes from the environment (.env), with the project falling
  # back to the main GCP project and the location to the global multi-region.
  project_id = os.environ.get("DATASTORE_PROJECT_ID", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
  location = os.environ.get("DATASTORE_LOCATION", "global")
  engine_id = os.environ.get("DATASTORE_ENGINE_ID", "bettys-bird-boutique-engine")
  if not project_id:
    return {"status": "error", "message": "DATASTORE_PROJECT_ID / GOOGLE_CLOUD_PROJECT is not set"}

  try:
    results = search(
      project_id=project_id,
      location=location,
      engine_id=engine_id,
      search_query=search_query,
    )
  except Exception as e:  # noqa: BLE001 - surface any API failure to the model
    return {"status": "error", "message": f"Document search failed: {e}"}

  if not results:
    return {"status": "not_found", "results": []}
  return {"status": "success", "results": results}
