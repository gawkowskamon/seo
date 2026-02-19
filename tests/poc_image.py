"""POC: Gemini Nano Banana image generation test"""
import asyncio
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

from emergentintegrations.llm.chat import LlmChat, UserMessage

async def test_image_gen():
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: No EMERGENT_LLM_KEY")
        return False
    
    chat = LlmChat(
        api_key=api_key,
        session_id="poc-image-gen",
        system_message="You are a helpful image generation assistant"
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    
    msg = UserMessage(
        text="Create a professional, clean illustration for a blog article about VAT tax accounting in Poland. Show a desk with tax documents, calculator, and Polish flag colors (red and white). Modern flat design style, business theme."
    )
    
    print("Generating image...")
    text, images = await chat.send_message_multimodal_response(msg)
    
    print(f"Text: {text[:100] if text else 'None'}")
    print(f"Images: {len(images) if images else 0}")
    
    if images:
        for i, img in enumerate(images):
            print(f"Image {i}: mime={img['mime_type']}, data_len={len(img['data'])}")
            image_bytes = base64.b64decode(img['data'])
            with open(f"/tmp/test_gen_image_{i}.png", "wb") as f:
                f.write(image_bytes)
            print(f"Saved to /tmp/test_gen_image_{i}.png ({len(image_bytes)} bytes)")
        return True
    else:
        print("No images generated!")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_image_gen())
    print(f"\n{'SUCCESS' if result else 'FAILED'}")
