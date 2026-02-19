"""
Image Generation Service using Gemini Nano Banana (gemini-3-pro-image-preview).
Generates illustrations for accounting/SEO blog articles.
"""

import os
import base64
import logging
import uuid
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

IMAGE_PROMPTS = {
    "hero": "Create a professional, modern hero illustration for a blog article about {topic}. Clean flat design, business theme, professional colors (blue, white, light gray). No text in image. 16:9 aspect ratio style.",
    "section": "Create a simple, clean illustration to accompany a blog section about: {topic}. Minimalist flat design, professional accounting/business theme. No text in image.",
    "infographic": "Create a simple infographic-style illustration about {topic}. Show key concepts visually with icons and simple shapes. Professional business style, blue and white color scheme. No text in image.",
    "custom": "{topic}"
}


async def generate_image(prompt: str, style: str = "hero", topic: str = "") -> dict:
    """Generate an image using Gemini Nano Banana model.
    
    Returns dict with 'data' (base64) and 'mime_type'.
    """
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    # Build prompt based on style
    if style in IMAGE_PROMPTS and style != "custom":
        full_prompt = IMAGE_PROMPTS[style].format(topic=prompt or topic)
    else:
        full_prompt = prompt
    
    session_id = f"img-gen-{uuid.uuid4().hex[:8]}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are a professional illustration generator for business and accounting blog articles. Generate clean, professional images."
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    
    msg = UserMessage(text=full_prompt)
    
    logger.info(f"Generating image with style={style}, prompt_len={len(full_prompt)}")
    
    text, images = await chat.send_message_multimodal_response(msg)
    
    if not images or len(images) == 0:
        raise ValueError("No image was generated")
    
    img = images[0]
    logger.info(f"Image generated: mime={img['mime_type']}, size={len(img['data'])}")
    
    return {
        "data": img["data"],  # base64 string
        "mime_type": img["mime_type"]
    }
