"""
Shared LLM helper with retry, exponential backoff, and model fallback.
All services should use this for resilient LLM calls.
"""
import asyncio
import logging
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    ("gemini", "gemini-2.0-flash"),
    ("openai", "gpt-4.1-mini"),
    ("openai", "gpt-5.2"),
]


async def llm_chat(
    prompt: str,
    system_message: str,
    session_id: str = "default",
    timeout: int = 120,
    max_retries: int = 2,
    models: list = None,
) -> str:
    """
    Send a chat message with automatic retry and model fallback.
    Returns the raw response text.
    """
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")

    models_to_try = models or FALLBACK_MODELS
    last_error = None

    for model_idx, (provider, model) in enumerate(models_to_try):
        for attempt in range(max_retries):
            try:
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"{session_id}-m{model_idx}-a{attempt}",
                    system_message=system_message,
                )
                chat.with_model(provider, model).with_params(timeout=timeout)
                response = await chat.send_message(UserMessage(text=prompt))
                logger.info(f"[llm_helper] {provider}/{model} succeeded (attempt {attempt+1})")
                return response
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_transient = any(
                    x in err_str
                    for x in ["502", "503", "504", "bad gateway", "timeout", "rate_limit", "overloaded", "connection"]
                )
                if is_transient and attempt < max_retries - 1:
                    wait = 5 * (2 ** attempt)
                    logger.warning(f"[llm_helper] {model} attempt {attempt+1} failed: {e}. Retry in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.warning(f"[llm_helper] {model} exhausted: {e}")
                    break

    raise last_error or ValueError("All LLM models failed")


def llm_chat_sync(
    prompt: str,
    system_message: str,
    session_id: str = "default",
    timeout: int = 120,
    max_retries: int = 2,
    models: list = None,
) -> str:
    """
    Synchronous version of llm_chat for use in ThreadPoolExecutor threads.
    Creates its own event loop.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            llm_chat(prompt, system_message, session_id, timeout, max_retries, models)
        )
    finally:
        loop.close()
