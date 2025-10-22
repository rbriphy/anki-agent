#!/usr/bin/env python3
"""
Mobile-optimized Anki Agent for Termux
AI-powered Japanese flashcard generator with mobile-friendly features
"""

import os
import json
import yaml
import requests
import base64
import sys
from dotenv import load_dotenv
from pathlib import Path
import argparse

# Load environment variables
load_dotenv()

# Mobile-optimized settings
AGENT_DECK = "AgentDeck"
OUTPUT_DIR = Path("/sdcard/anki-agent")
OUTPUT_DIR.mkdir(exist_ok=True)
API_KEY = os.getenv("OPENROUTER_API_KEY")
TEXT_MODEL = CONFIG["text_model"]
IMAGE_MODEL = CONFIG["image_model"]

# Load configuration
try:
    with open("config.yaml", "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    # Fallback configuration for mobile
    print("Yaml not found")
    exit(1)


# Mobile-friendly progress indicators
def show_progress(message):
    """Show progress with mobile-friendly formatting"""
    print(f"📱 {message}")

def check_connectivity():
    """Check if internet connection is available"""
    try:
        requests.get("https://api.openrouter.ai", timeout=5)
        return True
    except:
        return False

def generate_flashcard_data(word: str) -> dict:
    """Generate flashcard data using OpenRouter API"""
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    if not check_connectivity():
        raise ConnectionError("No internet connection available")
    
    show_progress("🤖 Generating flashcard content...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "You are a Japanese language assistant that generates structured flashcard data "
        "for Anki. Given a Japanese word or phrase, return a JSON object with the following keys:\n"
        "{ kanji, kana, english_meaning, example_sentence_jp, example_sentence_en, "
        "anki_format: {front, back, tags}, image_prompt }.\n"
        "Keep the text concise and accurate. Example:\n"
        "{'kanji': '昨日', 'kana': 'きのう', 'english_meaning': 'yesterday', ...}"
    )

    user_prompt = f"Generate data for the word '{word}'. Output valid JSON only."

    data = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except requests.exceptions.Timeout:
        raise ConnectionError("Request timed out. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"API request failed: {e}")

def generate_image(prompt: str, filename: Path) -> Path:
    """Generate image using OpenRouter API"""
    show_progress("🎨 Generating image...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": IMAGE_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        res = response.json()
        
        img_bytes = None
        
        # Try multiple extraction methods
        try:
            # Method 1: Check if response has data field
            if "data" in res and res["data"]:
                data_item = res["data"][0]
                if "url" in data_item:
                    img_bytes = requests.get(data_item["url"]).content
                elif "b64_json" in data_item:
                    img_bytes = base64.b64decode(data_item["b64_json"])
            
            # Method 2: Check message content
            if not img_bytes:
                message = res.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                
                if isinstance(content, str):
                    if content.startswith("data:image"):
                        header, encoded = content.split(",", 1)
                        img_bytes = base64.b64decode(encoded)
                    elif content.startswith("http"):
                        img_bytes = requests.get(content).content
            
            # Method 3: Check for base64 in response
            if not img_bytes:
                response_str = json.dumps(res)
                import re
                base64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)'
                match = re.search(base64_pattern, response_str)
                if match:
                    img_bytes = base64.b64decode(match.group(1))
        
        except Exception as e:
            show_progress(f"⚠️ Error processing image response: {e}")
            raise ValueError(f"Could not extract image from response: {e}")

        if not img_bytes:
            raise ValueError("No image data found in response")

        with open(filename, "wb") as f:
            f.write(img_bytes)

        return filename
        
    except requests.exceptions.Timeout:
        raise ConnectionError("Image generation timed out. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Image generation failed: {e}")

def store_image_in_anki(image_path: Path) -> str:
    """Store image in Anki using AnkiConnect's storeMediaFile action"""
    url = "http://localhost:8765"
    
    show_progress("📤 Uploading image to Anki...")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        filename = f"anki_agent_{image_path.name}"
        payload = {
            "action": "storeMediaFile",
            "version": 6,
            "params": {
                "filename": filename,
                "data": image_b64
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result and result["error"]:
            raise ConnectionError(f"Anki error: {result['error']}")
        
        show_progress(f"✅ Image stored: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to store image in Anki: {e}")

def add_to_anki(card: dict, image_path: Path) -> bool:
    """Add card to Anki via AnkiConnect"""
    url = "http://localhost:8765"
    
    show_progress("🧠 Adding card to Anki...")
    
    # First, store the image
    try:
        anki_image_name = store_image_in_anki(image_path)
    except Exception as e:
        show_progress(f"❌ Failed to store image: {e}")
        return False
    
    # Validate card data
    anki_format = card.get("anki_format", {})
    if not anki_format:
        show_progress("❌ No anki_format found in card data")
        return False
    
    # Create note
    note = {
        "deckName": AGENT_DECK,
        "modelName": "Basic",
        "fields": {
            "Kanji": card.get("kanji", ""),
            "Kana": card.get("kana", ""),
            "English": card.get("english_meaning", ""),
            "Sentence": card.get("example_sentence_jp", ""),
            "Sentence (English)": f"{card.get('example_sentence_en', '')}<br><img src='{anki_image_name}'>",
        },
        "options": {"allowDuplicate": True},
        "tags": anki_format.get("tags", []),
    }
    
    try:
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {"note": note}
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result and result["error"]:
            show_progress(f"❌ Anki error: {result['error']}")
            return False
        
        show_progress("✅ Card added to Anki successfully!")
        return True
        
    except requests.exceptions.RequestException as e:
        show_progress(f"❌ Failed to add card to Anki: {e}")
        return False

def mobile_main():
    """Main function for mobile usage"""
    parser = argparse.ArgumentParser(description="Mobile Anki Agent")
    parser.add_argument("word", help="Japanese word or phrase to generate card for")
    parser.add_argument("--no-anki", action="store_true", help="Skip Anki upload, just generate files")
    parser.add_argument("--deck", default="AgentDeck", help="Anki deck name")
    
    args = parser.parse_args()
    word = args.word.strip()
    
    if not word:
        print("❌ Please provide a Japanese word or phrase")
        return
    
    show_progress(f"🎯 Generating card for: {word}")
    
    try:
        # Generate flashcard data
        card = generate_flashcard_data(word)
        show_progress("✅ Content generated successfully")
        
        # Save JSON
        json_path = OUTPUT_DIR / f"{word}_card.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        show_progress(f"💾 Saved: {json_path}")
        
        # Generate image
        img_prompt = card.get("image_prompt", f"illustration of '{word}'")
        img_path = OUTPUT_DIR / f"{word}_image.png"
        generate_image(img_prompt, img_path)
        show_progress(f"🖼️ Saved: {img_path}")
        
        # Add to Anki (unless --no-anki flag)
        if not args.no_anki:
            success = add_to_anki(card, img_path)
            if success:
                show_progress("🎉 Flashcard created and added to Anki!")
            else:
                show_progress("⚠️ Card generated but failed to add to Anki")
        else:
            show_progress("📁 Card generated (skipped Anki upload)")
        
    except Exception as e:
        show_progress(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(mobile_main())