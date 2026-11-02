"""A tiny tool that tells the agent what day it is.

The store hours live in the PDF documents, but the model has no idea what
today's date is, so it cannot answer "Are you open today?" on its own.
"""
from datetime import datetime


def get_current_date() -> dict:
  """
  Returns the current local date and day of the week.

  Use this before answering any question that depends on what day it is,
  such as "Are you open today?", "What time do you close tomorrow?" or
  "Are you open this weekend?". Combine the result with the store hours
  from the store documents.

  Returns:
      dict: {"date": "YYYY-MM-DD", "day_of_week": "Monday", "time": "HH:MM"}
  """
  now = datetime.now()
  return {
    "date": now.strftime("%Y-%m-%d"),
    "day_of_week": now.strftime("%A"),
    "time": now.strftime("%H:%M"),
  }
