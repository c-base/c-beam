"""
the knowledge base behind station_knowledge (AI-ASSISTANT.md, section 9).

placeholder until block 5 of ASSISTANT-TODO.md: the tool is only offered when
RAG_KEY is set, and until the qdrant search lands here that would surface as
this error in the terminal.
"""

from .chat import AssistantError


def search(query):
    raise AssistantError("wissensdatenbank noch nicht angebunden")
