# Getting Started with PiperScribe

## What is PiperScribe?

PiperScribe is a desktop application for converting text to speech using Piper TTS. It provides a user-friendly interface for:

- Managing text documents with TTS-specific preprocessing
- Applying regex rules to clean and format text
- Generating high-quality speech with Piper voices
- Previewing and exporting audio files

## Prerequisites

### Installing Piper TTS

PiperScribe requires Piper TTS to be installed on your system:

1. Download Piper from [github.com/rhasspy/piper](https://github.com/rhasspy/piper)
2. Follow the installation instructions for your platform
3. Ensure `piper` is available in your system PATH
4. Test installation: Open Preferences → Voice tab → Click "Test Piper Installation"

### Installing Voices

Piper voices are required for speech generation:

1. Open **Tools → Browse & Download Voices**
2. Browse available voices by language and quality
3. Click **Download Voice** for your preferred voice
4. Voices install to `~/.local/share/piper/voices/`

## Creating Your First Project

### Quick Start

1. **Launch PiperScribe**
   - The main window displays with an empty document

2. **Enter or Import Text**
   - Type text directly into the editor, or
   - Use **File → Import** to load from TXT, DOCX, PDF, or Markdown

3. **Select a Voice**
   - Go to **Edit → Preferences → Voice** tab
   - Choose a voice from the dropdown
   - Click **Test Selected Voice** to hear a sample

4. **Generate Speech**
   - Click **Generate All** to process the entire document
   - Or select text and use the selection toolbar for partial generation
   - Audio plays automatically when complete

5. **Export Audio**
   - Use **File → Export Audio** to save as WAV file
   - Choose your preferred export location

## Basic Workflow

```
1. Create/Import Text
   ↓
2. Apply Regex Rules (optional)
   ↓
3. Select Voice
   ↓
4. Generate Speech
   ↓
5. Preview/Listen
   ↓
6. Export Audio
```

## Next Steps

- **Learn about text preprocessing**: See [User Guide](user-guide.md) → Regex Rules
- **Explore keyboard shortcuts**: See [Keyboard Shortcuts](keyboard-shortcuts.md)
- **Troubleshoot issues**: See [Troubleshooting](troubleshooting.md)

## Project Files

PiperScribe projects are saved as `.json` files containing:
- Document text content
- Applied regex rules
- Voice settings
- TTS parameters (speed, noise scales)

Save your work with **File → Save Project** (Ctrl+S)
