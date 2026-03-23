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
    system_msg = ASSISTANT_SYSTEM + f"\n\nKONTEKST ARTYKULU:\n{context_str}"
    
    # Try with existing session first, fallback to new session with different model
    from llm_helper import FALLBACK_MODELS
    
    if session_id in _chat_sessions:
        try:
            chat = _chat_sessions[session_id]
            response = await chat.send_message(UserMessage(text=message))
            return response.strip() if isinstance(response, str) else str(response)
        except Exception as e:
            logger.warning(f"Chat session {session_id} failed: {e}, trying fallback models...")
            _chat_sessions.pop(session_id, None)
    
    # Try each model
    last_error = None
    for provider, model in FALLBACK_MODELS:
        try:
            chat = LlmChat(
                api_key=emergent_key,
                session_id=f"{session_id}-{model}",
                system_message=system_msg
            )
            chat.with_model(provider, model).with_params(timeout=120)
            response = await chat.send_message(UserMessage(text=message))
            _chat_sessions[session_id] = chat
            return response.strip() if isinstance(response, str) else str(response)
        except Exception as e:
            last_error = e
            logger.warning(f"Chat assistant {model} failed: {e}")
            continue
    
    raise last_error or ValueError("Asystent AI jest tymczasowo niedostepny")


def clear_chat_session(session_id: str):
    """Clear a chat session."""
    _chat_sessions.pop(session_id, None)
