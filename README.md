# Anki Agent - AI-Powered Japanese Flashcard Generator

A Python application that automatically generates Japanese flashcards with AI-generated content and images, then uploads them directly to Anki via AnkiConnect.

## 🎯 Features

- **AI-Powered Content Generation**: Uses OpenRouter API to generate structured Japanese vocabulary data
- **Image Generation**: Creates custom illustrations for each flashcard using AI
- **Anki Integration**: Automatically uploads cards and images to Anki via AnkiConnect
- **Structured Data**: Generates comprehensive card data including kanji, kana, meanings, and example sentences
- **Media Management**: Properly handles image uploads to Anki's media folder
- **Error Handling**: Robust error handling and debugging output

## 🚀 Quick Start

### Prerequisites

1. **Anki**: Install [Anki](https://apps.ankiweb.net/) on your system
2. **AnkiConnect**: Install the [AnkiConnect add-on](https://ankiweb.net/shared/info/2055492159) in Anki
3. **Python 3.10+**: Ensure you have Python 3.10 or higher
4. **OpenRouter API Key**: Get an API key from [OpenRouter](https://openrouter.ai/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd anki-agent
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file
   echo "OPENROUTER_API_KEY=your_api_key_here" > .env
   ```

4. **Configure settings** (optional):
   Edit `config.yaml` to customize models and settings.

### Usage

1. **Start Anki** with AnkiConnect enabled
2. **Run the application**:
   ```bash
   python main.py
   ```
3. **Enter a Japanese word** when prompted
4. **Watch the magic happen** - the app will:
   - Generate structured vocabulary data
   - Create a custom illustration
   - Upload everything to Anki

## 📁 Project Structure

```
anki-agent/
├── main.py               # Main application
├── mobile_main.py        # Main application tailored for android
├── config.yaml           # Configuration settings
├── pyproject.toml        # Python project configuration
├── .python-version       # Python version specification
├── .gitignore            # Git ignore rules
├── outputs/              # Generated files
│   ├── *_card.json       # Card data files
│   └── *_image.png       # Generated images
└── README.md             # This file
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Config File (config.yaml)

```yaml
text_model: "openai/gpt-5-nano"           # Text generation model
image_model: "openai/gpt-5-image-mini"    # Image generation model
output_dir: "outputs"                     # Output directory
```

## 🔧 How It Works

### 1. Content Generation
- Takes a Japanese word/phrase as input
- Uses OpenRouter API to generate structured data:
  - Kanji and kana readings
  - English meanings
  - Example sentences (Japanese and English)
  - Image generation prompts

### 2. Image Generation
- Creates custom illustrations using AI
- Generates images based on the vocabulary word
- Saves images to the outputs directory

### 3. Anki Integration
- Uploads images to Anki's media folder using AnkiConnect
- Creates flashcards with embedded images
- Handles duplicate detection and error management

## 📊 Generated Card Structure

Each generated card includes:

```json
{
  "kanji": "窓",
  "kana": "まど", 
  "english_meaning": "window",
  "example_sentence_jp": "窓を開けて風を入れた。",
  "example_sentence_en": "I opened the window to let in a breeze.",
  "anki_format": {
    "front": "窓 (まど) — window",
    "back": "Meaning: window\nReading: まど\nExample: 窓を開けて風を入れた。 / I opened the window to let in a breeze.",
    "tags": ["Japanese", "Vocabulary", "Kanji", "N5"]
  },
  "image_prompt": "A clean, minimal illustration of a Japanese window..."
}
```

## 🛠️ API Integration

### OpenRouter API
- **Text Generation**: Uses GPT models for content creation
- **Image Generation**: Uses image models for illustrations
- **Structured Output**: Ensures consistent JSON format

### AnkiConnect API
- **Media Upload**: Uses `storeMediaFile` action for images
- **Card Creation**: Uses `addNote` action for flashcards
- **Error Handling**: Comprehensive error checking and reporting

## 🎨 Customization

### Model Selection
Edit `config.yaml` to use different AI models:

```yaml
text_model: "openai/gpt-4o-mini"        # Different text model
image_model: "dall-e-3"                 # Different image model
```

### Card Templates
Modify the card structure in `main.py` to customize:
- Field names and content
- HTML formatting
- Tag assignments
- Image placement

## 🔍 Troubleshooting

### Common Issues

1. **"Cannot connect to AnkiConnect"**
   - Ensure Anki is running
   - Verify AnkiConnect add-on is installed and enabled
   - Check that port 8765 is accessible

2. **"API key not found"**
   - Verify your `.env` file contains `OPENROUTER_API_KEY`
   - Check that the API key is valid and has credits

3. **"Image upload failed"**
   - Check that the image file exists in outputs/
   - Verify AnkiConnect is responding to requests
   - Check file permissions

4. **"Duplicate card error"**
   - This is normal - the app prevents duplicate cards
   - Change `allowDuplicate` to `True` in the code if needed

### Debug Mode

The application includes extensive debugging output:
- Card data structure
- Image upload progress
- AnkiConnect responses
- Error details

## 🚀 Advanced Usage

### Batch Processing
```python
# Process multiple words
words = ["猫", "犬", "鳥"]
for word in words:
    # Your processing logic here
    pass
```

### Custom Prompts
Modify the system prompt in `generate_flashcard_data()` to:
- Change the output format
- Add specific requirements
- Customize the language level

## 📝 Dependencies

- **requests**: HTTP requests to APIs
- **pyyaml**: Configuration file parsing
- **python-dotenv**: Environment variable management
- **pathlib**: File path handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review AnkiConnect documentation
3. Verify your API keys and configuration
4. Open an issue on the project repository

## 🎉 Acknowledgments

- **AnkiConnect** for seamless Anki integration
- **OpenRouter** for AI model access
- **Anki** for the amazing spaced repetition system

---

**Happy studying! 📚✨**