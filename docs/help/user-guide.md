# PiperScribe User Guide

## Multi-Document Projects

### Managing Documents

PiperScribe supports multiple documents in a single project, perfect for audiobooks, courses, or collections.

**Document List** (left sidebar):
- Shows all documents with status icons:
  - ✓/⨯ = Enabled/Disabled in playlist
  - 🔊/⚫ = Has audio/No audio
- **Drag and drop** to reorder
- **Right-click** for document options
- **Hover** for detailed tooltip

**Keyboard Shortcuts**:
- **Delete** - Remove selected document
- **Ctrl+Up/Down** - Move document up/down
- **Space** - Toggle enabled/disabled
- **Enter** - Open document settings

### Adding Documents

**File → Open** or **Ctrl+I** - Import document
- Adds to current project (doesn't replace)
- Supports: TXT, DOCX, PDF, Markdown
- Each document gets unique ID

**Add Button** - Create empty document
- Manually add content later
- Useful for organizing chapters

### Per-Document Settings

**Right-click document → Document Settings**:
- **Title**: Rename document
- **Voice Model**: Choose different voice per document
- **Speed**: Adjust playback speed (0.1x - 3.0x)
- **Noise Scale/W**: Voice quality parameters
- **Test Voice**: Preview with sample text

### Generating Audio

**Single Document**:
- Right-click → Generate Audio
- Uses document's specific settings
- Saves to `{project}_audio/` folder

**Batch Generation**:
- File → Generate All Audio
- Processes all enabled documents
- Shows progress with cancel option
- Reports errors for individual documents

### Playlist Management

**Enable/Disable Documents**:
- Right-click → Enable/Disable in Playlist
- Or press **Space** on selected document
- Disabled documents skip in playlist

**Reorder Playlist**:
- Drag documents to reorder
- Or use Ctrl+Up/Down
- Or use ↑↓ buttons
- Order determines playback sequence

**Export Playlist**:
- File → Export Playlist
- Exports both M3U and JSON formats
- M3U: Works with VLC, mpv, etc.
- JSON: Metadata for custom tools

### Document Statistics

Status bar shows:
- **When document selected**: Document title, status icons, character counts
- **When no selection**: Project stats (total docs, enabled, with audio)

## Document Editing

### Text Editor Features

The main text editor supports:
- **Standard editing**: Cut, copy, paste, undo, redo
- **Find/Replace**: Ctrl+F to search, Ctrl+H to replace
- **Auto-save**: Changes saved to project file
- **Rich text display**: Custom fonts and colors (Preferences → Appearance)

### Selection Toolbar

When text is selected, a toolbar appears with quick actions:

- **Exclude**: Mark text to skip during TTS generation
- **Include**: Mark excluded text for generation
- **Preview**: Generate and play audio for selection only
- **Stop**: Cancel ongoing TTS generation

Toggle toolbar visibility: **Edit → Preferences → General**

## Text Preprocessing with Regex Rules

### What are Regex Rules?

Regex (regular expression) rules let you automatically transform text before speech generation. Common uses:

- Remove unwanted characters or formatting
- Expand abbreviations (Dr. → Doctor)
- Convert numbers to words
- Clean up imported document artifacts

### Managing Rules

Access rules: **Tools → Rules** or **Edit → Preferences → Rules**

Each rule has:
- **Name**: Description of what the rule does
- **Pattern**: Regular expression to match
- **Action**: Either "exclude" (skip matching text) or "include" (keep only matches)
- **Flags**: Case sensitivity, multiline, dot-matches-newline options

### Testing Rules

1. Go to **Tools → Rules**
2. Select a rule from the list
3. Enter or use document text in the "Test text" field
4. Click **Test** to see matches
5. Results show match count and up to 10 previews

### Applying Rules

Rules are applied automatically when **Auto-apply rules** is enabled (default).

Manual application:
- **Tools → Rules → Reapply All Rules** button
- Processes document with current ruleset

### Canned Rules

PiperScribe includes pre-configured rules:
- **Filter images**: Remove image placeholders from imports
- **Normalize whitespace**: Clean up extra spaces/newlines
- **Remove URLs**: Strip web links
- **Expand common abbreviations**: Dr., Mr., etc.

Enable/disable individual rules as needed.

## Voice Management

### Selecting Voices

**Edit → Preferences → Voice** tab:
- Dropdown lists all installed voices
- Voice path shows selected model file location
- Voice details include language, quality, speaker count

### Testing Voices

Three test options:

1. **Test Piper Installation**: Verify piper command is available
2. **Test Selected Voice**: Generate and play sample audio
3. **Preview in document**: Select text, click Preview in toolbar

### Downloading Voices

**Tools → Browse & Download Voices**:

- Browse 150+ voices by language
- Filter by name, language, or quality
- View voice details (size, speakers, quality rating)
- Download directly to voice directory
- Voices appear immediately in Preferences dropdown

### Deleting Voices

**Edit → Preferences → Voice** tab:
- Select voice from dropdown
- Click **Delete Selected Voice**
- Confirm deletion
- Both .onnx and .onnx.json files are removed

## TTS Generation

### Voice Parameters

Configure in **Edit → Preferences → Voice**:

- **Speed**: Playback rate (0.5-2.0x, default 1.0)
- **Noise Scale**: Voice variation (0.0-2.0, default 0.667)
- **Noise W**: Additional variance (0.0-2.0, default 0.8)

### Generation Options

**Generate All**: Process entire document
- Excludes text marked with "exclude" rules
- Plays audio when complete
- Audio stored in memory for export

**Selection Preview**:
- Select specific text
- Click Preview in selection toolbar
- Useful for testing voices or specific passages

**Stop Generation**:
- Click Stop in selection toolbar
- Cancels in-progress generation

## Export Options

### Export Audio

**File → Export Audio** (Ctrl+E):
- Saves generated audio as WAV file
- Choose destination and filename
- Audio must be generated first

### Export Text

**File → Export Text**:
- Saves plain text content
- Current document state (after rule application)

## Settings and Preferences

**Edit → Preferences** (Ctrl+,):

### General Tab
- **Theme**: System, Light, or Dark mode
- **Selection toolbar**: Show/hide quick action toolbar
- **Font**: Custom font family and size
- **Colors**: Document background and text colors

### Voice Tab
- Voice selection and testing
- TTS parameter configuration
- Voice management (browse, download, delete)

### Rules Tab
- View and edit regex rules
- Test patterns against text
- Enable/disable individual rules
- Reset to default rules

## Keyboard Shortcuts

See [Keyboard Shortcuts](keyboard-shortcuts.md) for complete list.

## Tips and Best Practices

1. **Save frequently**: Use Ctrl+S or **File → Save Project**
2. **Test rules**: Always test regex patterns before applying
3. **Preview voices**: Test voice with actual document text
4. **Organize projects**: Save different documents as separate projects
5. **Rule order matters**: Rules process in list order (top to bottom)
6. **Start simple**: Begin with canned rules, customize as needed
