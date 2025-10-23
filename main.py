import os
import json
import yaml
import requests
import base64
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# --- Load Config ---
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

AGENT_DECK = "AgentDeck"
API_KEY = os.getenv("OPENROUTER_API_KEY")
TEXT_MODEL = CONFIG["text_model"]
IMAGE_MODEL = CONFIG["image_model"]
OUTPUT_DIR = Path(CONFIG["output_dir"])
OUTPUT_DIR.mkdir(exist_ok=True)

# --- LLM Call ---
def generate_flashcard_data(word: str) -> dict:
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

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


# --- Image Generation ---
def generate_image(prompt: str, filename: Path) -> Path:
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

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    res = response.json()

    # Debug: Print the full response structure
    print("🔍 Full response structure:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    img_bytes = None
    
    try:
        # Method 1: Check if response has data field (like DALL-E format)
        if "data" in res and res["data"]:
            data_item = res["data"][0]
            if "url" in data_item:
                img_bytes = requests.get(data_item["url"]).content
            elif "b64_json" in data_item:
                img_bytes = base64.b64decode(data_item["b64_json"])
        
        # Method 2: Check message content for image data
        if not img_bytes:
            message = res.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            
            # If content is a string, it might contain base64 or URL
            if isinstance(content, str):
                if content.startswith("data:image"):
                    # Extract base64 from data URL
                    header, encoded = content.split(",", 1)
                    img_bytes = base64.b64decode(encoded)
                elif content.startswith("http"):
                    # It's a URL
                    img_bytes = requests.get(content).content
            
            # If content is a list, check each item
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url" and "image_url" in item:
                        img_bytes = requests.get(item["image_url"]["url"]).content
                        break
                    elif item.get("type") == "image" and "image_b64" in item:
                        img_bytes = base64.b64decode(item["image_b64"])
                        break
                    elif "url" in item:
                        img_bytes = requests.get(item["url"]).content
                        break
                    elif "b64_json" in item:
                        img_bytes = base64.b64decode(item["b64_json"])
                        break
        
        # Method 3: Check for any base64 data in the response
        if not img_bytes:
            response_str = json.dumps(res)
            # Look for base64 image patterns
            import re
            base64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)'
            match = re.search(base64_pattern, response_str)
            if match:
                img_bytes = base64.b64decode(match.group(1))
        
    except Exception as e:
        print(f"⚠️ Error processing image response: {e}")
        print("Full response:", json.dumps(res, indent=2, ensure_ascii=False))
        raise ValueError(f"Could not extract image from response: {e}")

    if not img_bytes:
        print("⚠️ No image data found in response")
        print("Response structure:", json.dumps(res, indent=2, ensure_ascii=False))
        raise ValueError("No image data found in response")

    with open(filename, "wb") as f:
        f.write(img_bytes)

    return filename

def store_image_in_anki(image_path: Path) -> str:
    """Store image in Anki using AnkiConnect's storeMediaFile action"""
    url = "http://localhost:8765"
    
    print(f"📤 Uploading image to Anki: {image_path.name}")
    
    # Read the image file
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Encode to base64
    import base64
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    
    # Store in Anki using AnkiConnect
    filename = f"anki_agent_{image_path.name}"
    payload = {
        "action": "storeMediaFile",
        "version": 6,
        "params": {
            "filename": filename,
            "data": image_b64
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result and result["error"]:
            print(f"❌ Error storing image: {result['error']}")
            return None
        
        print(f"✅ Image stored in Anki: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Failed to store image: {e}")
        return None

def add_to_anki(card: dict, image_path: Path, deck_name: str = "Japanese") -> bool:
    """
    Adds a card with an image to Anki via AnkiConnect.
    """
    url = "http://localhost:8765"

    print("🔍 Card data:", json.dumps(card, indent=2, ensure_ascii=False))
    
    # First, store the image in Anki
    anki_image_name = store_image_in_anki(image_path)
    if not anki_image_name:
        print("❌ Failed to store image in Anki")
        return False
    
    # Check if anki_format exists and has the required fields
    anki_format = card.get("anki_format", {})
    front = anki_format.get("front", "").strip()
    back = anki_format.get("back", "").strip()
    
    print(f"🔍 Front: '{front}'")
    print(f"🔍 Back: '{back}'")
    
    # Check if fields are empty
    if not front or not back:
        print("❌ Error: Front or Back field is empty!")
        print(f"Front: '{front}' (length: {len(front)})")
        print(f"Back: '{back}' (length: {len(back)})")
        return False

    note = {
    "deckName": "AgentDeck",
    "modelName": "Basic",
    "fields": {
        "Kanji": card["kanji"],
        "Kana": card["kana"],
        "English": card["english_meaning"],
        "Sentence": card["example_sentence_jp"],
        "Sentence (English)": f"{card['example_sentence_en']}<br><img src='{anki_image_name}'>",
    },
    "options": {
        "allowDuplicate": True,
    },
    "tags": card["anki_format"]["tags"],
}

    
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {"note": note}
    }

    r = requests.post(url, json=payload)
    r.raise_for_status()
    res = r.json()

    if "error" in res and res["error"]:
        print("❌ Anki error:", res["error"])
        return False

    print("✅ Card added successfully to Anki:", res["result"])
    return True


# --- Main ---
def main():
    word = input("Enter a Japanese word or phrase: ").strip()
    print(f"\n🔎 Generating flashcard for '{word}'...")

    card = generate_flashcard_data(word)
    print(json.dumps(card, ensure_ascii=False, indent=2))

    # Save JSON
    json_path = OUTPUT_DIR / f"{word}_card.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)

# Generate image
    img_prompt = card.get("image_prompt", f"illustration of '{word}'")
    img_path = OUTPUT_DIR / f"{word}_image.png"
    generate_image(img_prompt, img_path)
    #img_path = OUTPUT_DIR / "箱_image.png" #Note to LLM: Temporary hardcoded image path


    print(f"\n✅ Saved JSON: {json_path}")
    print(f"🖼️  Saved image: {img_path}")

    # Push to Anki
    print("\n🧠 Adding to Anki...")
    success = add_to_anki(card, img_path, AGENT_DECK)
    if success:
        requests.post("http://localhost:8765", json={"action": "sync", "version": 6})
        print("🎴 Flashcard added to Anki successfully and synced!")

    else:
        print("⚠️ Failed to add flashcard to Anki and sync.")

        



if __name__ == "__main__":
    main()
