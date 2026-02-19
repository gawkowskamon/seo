"""
Enhanced Image Generation Service using Gemini Nano Banana (gemini-3-pro-image-preview).
Generates illustrations for accounting/SEO blog articles.
Features: multiple style presets, contextual prompts, variant generation.
"""

import os
import base64
import logging
import uuid
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContent

logger = logging.getLogger(__name__)

# Enhanced style presets with detailed prompts
IMAGE_STYLES = {
    "hero": {
        "id": "hero",
        "name": "Okladka artykulu",
        "description": "Profesjonalna ilustracja naglowkowa 16:9",
        "icon": "image",
        "prompt": "Create a professional, modern hero illustration for a blog article about {topic}. Clean flat design, business and accounting theme, premium color palette (navy blue, white, warm amber accents). Wide landscape format. No text. High quality digital art."
    },
    "fotorealizm": {
        "id": "fotorealizm",
        "name": "Foto-realizm",
        "description": "Realistyczne zdjecie stockowe w stylu profesjonalnym",
        "icon": "camera",
        "prompt": "Professional stock photography style image about {topic}. Photorealistic, corporate setting, modern office environment, warm natural lighting, shallow depth of field. No text overlays. High resolution professional business photo."
    },
    "ilustracja": {
        "id": "ilustracja",
        "name": "Ilustracja flat",
        "description": "Minimalistyczna ilustracja w stylu flat design",
        "icon": "pen-tool",
        "prompt": "Minimalist flat design illustration about {topic}. Clean geometric shapes, limited color palette (navy blue, amber, light gray, white), professional business/accounting theme. Vector art style, no text, modern and clean."
    },
    "infografika": {
        "id": "infografika",
        "name": "Infografika",
        "description": "Wizualizacja danych i procesow",
        "icon": "bar-chart-3",
        "prompt": "Infographic-style illustration showing key concepts about {topic}. Visual data representation with icons, charts, arrows, and process flows. Professional accounting/business design. Navy blue and amber color scheme. Clean layout, no detailed text - use simple labels only."
    },
    "ikona": {
        "id": "ikona",
        "name": "Ikona / Symbol",
        "description": "Prosta ikona tematyczna na biale tlo",
        "icon": "circle",
        "prompt": "Simple, clean icon or symbol representing {topic}. Single object centered on white background. Professional business/accounting theme. Flat design, navy blue and amber colors. Minimal, elegant, suitable as a section marker or thumbnail."
    },
    "diagram": {
        "id": "diagram",
        "name": "Diagram / Schemat",
        "description": "Schemat blokowy lub diagram procesu",
        "icon": "git-branch",
        "prompt": "Professional diagram or flowchart illustrating the process of {topic}. Clean blocks connected with arrows, clear visual hierarchy. Business/accounting context. Navy blue, amber, and gray color scheme on white background. Professional, easy to understand."
    },
    "wykres": {
        "id": "wykres",
        "name": "Wykres / Tabela",
        "description": "Wizualizacja liczbowa - wykresy i tabele",
        "icon": "trending-up",
        "prompt": "Professional chart or data visualization related to {topic}. Clean bar chart, pie chart, or line graph style. Business/accounting data representation. Navy blue and amber color scheme. Professional, minimal, clear data visualization. No specific numbers required."
    },
    "custom": {
        "id": "custom",
        "name": "Wlasny prompt",
        "description": "Opisz dokladnie czego potrzebujesz",
        "icon": "edit",
        "prompt": "{topic}"
    }
}


def get_all_image_styles():
    """Return all available image styles."""
    return [{k: v for k, v in style.items() if k != 'prompt'} for style in IMAGE_STYLES.values()]


def _build_contextual_prompt(user_prompt: str, style_id: str, article_context: dict = None) -> str:
    """Build a contextual prompt combining user input, style, and article context."""
    style = IMAGE_STYLES.get(style_id, IMAGE_STYLES["custom"])
    
    # Start with style prompt
    if style_id != "custom":
        prompt = style["prompt"].format(topic=user_prompt)
    else:
        prompt = user_prompt
    
    # Add article context if available
    if article_context:
        topic = article_context.get("topic", "")
        keywords = article_context.get("primary_keyword", "")
        if topic and style_id != "custom":
            prompt += f"\n\nArticle context: This image is for a Polish accounting blog article about '{topic}'"
            if keywords:
                prompt += f" focusing on '{keywords}'."
            prompt += " The audience is Polish accountants and tax professionals."
    
    return prompt


async def generate_image(prompt: str, style: str = "hero", topic: str = "", article_context: dict = None, reference_image: dict = None) -> dict:
    """Generate an image using Gemini Nano Banana model.
    
    Args:
        prompt: User's image description or topic
        style: Style preset ID from IMAGE_STYLES
        topic: Legacy topic parameter
        article_context: Optional article context for contextual prompts
        reference_image: Optional reference image dict with 'data' (base64) and 'mime_type'
    
    Returns dict with 'data' (base64) and 'mime_type'.
    """
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    # Build contextual prompt
    full_prompt = _build_contextual_prompt(prompt or topic, style, article_context)
    
    # If reference image is provided, add instruction to the prompt
    if reference_image:
        full_prompt += "\n\nIMPORTANT: Use the attached reference image as inspiration for style, composition, or content. Create a new image that takes cues from this reference while matching the described style and topic."
    
    session_id = f"img-gen-{uuid.uuid4().hex[:8]}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are a professional illustration generator for business and accounting blog articles. Generate clean, professional, high-quality images. Use a navy blue and warm amber color palette unless specified otherwise."
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    
    # Build message with optional reference image
    file_contents = None
    if reference_image:
        file_contents = [
            FileContent(
                content_type=reference_image["mime_type"],
                file_content_base64=reference_image["data"]
            )
        ]
    
    msg = UserMessage(text=full_prompt, file_contents=file_contents)
    
    logger.info(f"Generating image with style={style}, prompt_len={len(full_prompt)}, has_reference={reference_image is not None}")
    
    text, images = await chat.send_message_multimodal_response(msg)
    
    if not images or len(images) == 0:
        raise ValueError("No image was generated")
    
    img = images[0]
    logger.info(f"Image generated: mime={img['mime_type']}, size={len(img['data'])}")
    
    return {
        "data": img["data"],
        "mime_type": img["mime_type"]
    }


async def generate_image_variant(original_prompt: str, style: str, variation_type: str = "color", article_context: dict = None, reference_image: dict = None) -> dict:
    """Generate a variant of an image with modifications.
    
    Args:
        original_prompt: The original image prompt
        style: Style preset
        variation_type: Type of variation (color, composition, mood, simplify)
        reference_image: Optional reference image dict with 'data' (base64) and 'mime_type'
    
    Returns dict with 'data' (base64) and 'mime_type'.
    """
    variation_instructions = {
        "color": "Use a different but still professional color scheme - try warm tones (amber, terracotta, cream) instead of blue.",
        "composition": "Create a different composition and layout. If original was centered, try asymmetric. If horizontal, try vertical elements.",
        "mood": "Change the mood - if original was formal, make it more dynamic and energetic. If vibrant, make it more calm and elegant.",
        "simplify": "Create a much simpler, more minimal version. Use fewer elements, more white space, cleaner lines."
    }
    
    instruction = variation_instructions.get(variation_type, variation_instructions["composition"])
    
    modified_prompt = f"{original_prompt}\n\nVARIATION INSTRUCTION: {instruction}"
    
    return await generate_image(
        prompt=modified_prompt,
        style=style,
        article_context=article_context,
        reference_image=reference_image
    )
