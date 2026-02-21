"""
AI Chat Assistant Service
Contextual AI assistant for article editing.
"""

import json
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# Store active chat sessions
_chat_sessions = {}

ASSISTANT_SYSTEM = """Jestes asystentem AI do pisania artykulow SEO z zakresu ksiegowosci i podatkow w Polsce.
Pomagasz uzytkownikowi edytowac i ulepszac artykuly. Masz dostep do kontekstu aktualnego artykulu.

Twoje mozliwosci:
- Poprawianie SEO tekstu (naglowki, slowa kluczowe, meta opisy)
- Pisanie nowych akapitow i sekcji
- Generowanie FAQ
- Upraszczanie jezyka
- Dodawanie przykladow liczbowych
- Sprawdzanie aktualnosci danych podatkowych
- Sugestie linkowania wewnetrznego

Odpowiadaj po polsku. Jesli uzytkownik prosi o napisanie lub poprawienie tekstu, zwroc go w HTML (p, strong, em, ul, li).
Jesli uzytkownik prosi o zmiane w JSON, zwroc JSON.
W pozostalych przypadkach odpowiadaj normalnym tekstem."""


async def chat_with_assistant(session_id: str, message: str, article_context: dict, emergent_key: str) -> str:
    """Send message to AI assistant with article context."""
    
    # Build context summary
    ctx_parts = []
    if article_context.get("title"):
        ctx_parts.append(f"Tytul artykulu: {article_context['title']}")
    if article_context.get("primary_keyword"):
        ctx_parts.append(f"Slowo kluczowe: {article_context['primary_keyword']}")
    if article_context.get("sections"):
        headings = [s.get("heading", "") for s in article_context["sections"][:6]]
        ctx_parts.append(f"Sekcje: {', '.join(headings)}")
    if article_context.get("seo_score"):
        score = article_context["seo_score"]
        if isinstance(score, dict):
            ctx_parts.append(f"Wynik SEO: {score.get('percentage', '?')}%")
    
    context_str = "\n".join(ctx_parts) if ctx_parts else "Brak kontekstu artykulu."
    
    # Create or reuse chat session
    if session_id not in _chat_sessions:
        chat = LlmChat(
            api_key=emergent_key,
            session_id=session_id,
            system_message=ASSISTANT_SYSTEM + f"\n\nKONTEKST ARTYKULU:\n{context_str}"
        )
        chat.with_model("openai", "gpt-4.1-mini")
        _chat_sessions[session_id] = chat
    
    chat = _chat_sessions[session_id]
    
    response = await chat.send_message(UserMessage(text=message))
    return response.strip() if isinstance(response, str) else str(response)


def clear_chat_session(session_id: str):
    """Clear a chat session."""
    _chat_sessions.pop(session_id, None)
