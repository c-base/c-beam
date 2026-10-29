"""
the web assistant: the android app's voice assistant (AI-ASSISTANT.md) rebuilt
on the server side, so that the browser only ever talks to c-beam.

chat.py          http to the ai server (chat completions, later whisper and embeddings)
tools.py         what the model may call, with the QUERY / SELF / CONFIRM levels
prompt.py        the system prompt
conversation.py  the per-session history and its rules
knowledge.py     the qdrant search behind station_knowledge
"""
