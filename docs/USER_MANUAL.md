# PiperScribe User Manual

Version 0.1.21

This manual covers installing PiperScribe, importing documents, choosing voices,
marking text, generating and playing audio, and exporting results.

Contents

1. [What PiperScribe does](#1-what-piperscribe-does)
2. [Installing and setting up Piper](#2-installing-and-setting-up-piper)
3. [The main window](#3-the-main-window)
4. [Projects](#4-projects)
5. [Importing documents](#5-importing-documents)
6. [Marking text: exclude and include](#6-marking-text-exclude-and-include)
7. [Regex rules](#7-regex-rules)
8. [Voices](#8-voices)
9. [Document settings](#9-document-settings)
10. [Generating audio](#10-generating-audio)
11. [Preview](#11-preview)
12. [Playing audio](#12-playing-audio)
13. [Exporting](#13-exporting)
14. [Finding text](#14-finding-text)
15. [Preferences](#15-preferences)
16. [Keyboard shortcuts](#16-keyboard-shortcuts)
17. [Troubleshooting](#17-troubleshooting)
18. [Files and folders](#18-files-and-folders)

---

## 1. What PiperScribe does

PiperScribe takes text from documents, lets you decide which parts should be
spoken, and generates speech with a Piper voice. Piper runs on your computer, so
no text is sent to a web service.

A typical workflow:

1. Import one or more documents into a project.
2. Mark text you don't want read, by hand or with rules.
3. Choose a voice, and adjust its speed if you want.
4. Preview a passage, then generate audio for a document or for the whole project.
5. Play the result, and export it as a WAV file or a playlist.

## 2. Installing and setting up Piper

PiperScribe needs two things beyond the app itself:

- **Python 3.10 or later**, plus the packages PiperScribe installs for you.
- **The `piper` command**, which must be on your PATH. PiperScribe calls it to
  generate speech.

Run the install script for your system, or follow [INSTALL.md](../INSTALL.md):

- Linux: `./setup-prj.sh`, then `./run.sh`
- macOS: `install-macos.sh`
- Windows: `install-windows.bat` or `install-windows.ps1`

### Getting a voice

A voice is a Piper model file, with a `.onnx` extension and a matching
`.onnx.json` file. You can get one in two ways:

- **Tools → Browse && Download Voices…** lists voices you can download straight
  into the voice folder. Use the filters to narrow the list by name, language, or quality.
- **Tools → Import Voice Model…** copies a voice you already have into the voice folder.

Voices are normally stored in `~/.local/share/piper/voices/`.

### Checking the setup

Open **Edit → Preferences → Voice** and click **Test Piper Installation**. If
it reports that Piper is missing, install Piper and make sure `piper` runs from a
terminal.

Then click **Test Selected Voice**. You should hear a short sample. If you don't,
see [Troubleshooting](#17-troubleshooting).

## 3. The main window

The main window has four areas:

- **Document list (left).** Every document in the project. Click a document to
  show its text. Drag rows to reorder them. Each row shows two marks: ✓ or ⨯
  for enabled or disabled in the playlist, 🔊 for audio that is current, ↻ for audio made from an older voice, speed, or text
  (it regenerates on Play), and ⚫ for no audio yet.
- **Text editor (centre).** The text of the selected document. Text you have
  excluded is shaded so you can see what will not be spoken.
- **Selection toolbar.** Appears when you select text. It has the actions
  Exclude, Include, Preview, and Stop. You can hide it in
  **Preferences → Appearance**.
- **Audio toolbar (top).** Play, Pause, and Stop for generated audio.

The status bar shows statistics for the selected document, or for the whole
project when nothing is selected.

### Menus

| Menu | Items |
|------|-------|
| **File** | New Project, Import Document(s)…, Open Document(s)…, Save Project…, Load Project…, Close Project, Recent Files, Recent Projects, Export WAV…, Save Audio to Folder…, Generate All Audio, Export Playlist…, Quit |
| **Edit** | Preferences…, Find… |
| **Tools** | Exclude selection, Include selection, Preview selection, Stop Preview, Rules…, Reapply Rules, Import Voice Model…, Browse && Download Voices… |
| **Help** | Help Contents…, About PiperScribe |

### Right-click menu on a document

Right-click a document in the list to:

- Open **Document Settings…**
- **Play Audio** (enabled when the document has audio)
- **Generate Audio** for this document
- **Enable/Disable in Playlist**
- **Remove Document**

## 4. Projects

A project holds your documents, their text, the marked exclusions, and the
voice settings. Save it so you can come back to it.

- **New Project** starts an empty project.
- **Save Project…** saves to a project file. PiperScribe uses the
  `.abproj.json` extension for audiobook projects.
- **Load Project…** opens a saved project.
- **Close Project** closes the current project.
- **Recent Files** and **Recent Projects** reopen the last few items you used.

**Save the project before you generate audio.** Audio is stored in a folder next
to the project file, or in the **Audio folder** you set in Preferences. A project
that has never been saved has no project folder, so its audio goes into a
temporary folder that the system may clear.

If audio is only in the temporary folder, PiperScribe warns you before you quit,
start a new project, close the project, or open another project. You can save the
audio to a folder, discard it, or cancel and keep working.
Use **File → Save Audio to Folder…** at any time to copy the audio somewhere permanent.

## 5. Importing documents

Choose **File → Import Document(s)…** (Ctrl+I) or **File → Open Document(s)…** (Ctrl+O). Both do the same thing. Click **Import…** above the
document list. You can select several files at once. Each one is added as its
own document, and the existing documents stay in the project.

| Format | Notes |
|--------|-------|
| TXT | Plain text. |
| DOCX | Requires `python-docx`. |
| Markdown | Requires `markdown-it-py` for full formatting; a simpler reader is used otherwise. |
| HTML | Requires `beautifulsoup4` for full cleaning; a simpler reader is used otherwise. |
| PDF | Requires `PyMuPDF`. Works with text-based PDFs only. Scanned pages have no text to read, and PiperScribe does not do OCR. |

Imported text is cleaned by the enabled regex rules when **Auto-apply rules** is
on (the default). You can change the text in the editor afterwards.

## 6. Marking text: exclude and include

Some text should not be spoken: page headers, page numbers, web addresses,
table-of-contents lists. Mark it as excluded.

1. Select the text in the editor.
2. Click **Exclude selection** in the selection toolbar, or choose
   **Tools → Exclude selection**.

Excluded text stays in the document, and it is shaded in the editor. It is
skipped when audio is generated or exported.

To put excluded text back, select it and click **Include selection**, or choose
**Tools → Include selection**.

Manual exclusions are kept separately from rule-based exclusions. When you
reapply rules, your manual choices stay as they are.

## 7. Regex rules

Regex rules find text by pattern and exclude it automatically. They are useful
when the same kind of text appears throughout a document, such as URLs or page
numbers.

Open **Tools → Rules…**. It opens the Rules tab of Preferences. Each rule has:

- a **name** and a **pattern** (a regular expression)
- an **action**: exclude matching text
- an **enabled** check box, and flags for case sensitivity, multi-line matching,
  and "dot matches newline"

Use the test area on the Rules tab to try a pattern against sample text before
you rely on it. The app ships with several rules, such as one that removes web
addresses. Some rules are off by default. Turn on the ones you need.

**Tools → Reapply Rules** recalculates the rule-based exclusions for the
current document. Use it after you change a rule. If **Auto-apply rules** is on,
rules are also applied when a document is opened and when you export.

Rules run in list order, from top to bottom.

## 8. Voices

### Choosing a voice for the project

Pick a voice in the **voice dropdown on the toolbar** or on the Voice tab of
**Edit → Preferences**. Both set the project voice.

Each document also keeps its own copy of the voice it was created with. A
toolbar or Preferences change updates the project voice and every document still
using the previous project voice. A voice you picked for a single document in
**Document Settings** stays as it is.

Speed, noise scale, and noise W follow the same rule: a change on the Voice tab
updates every document still using the project's values. A document you set
differently in Document Settings keeps its own values.

Click **Test Selected Voice** on the Voice tab to hear a sample. The sample uses
the speed and noise values shown on that tab, whether or not you have pressed OK.

### Voice settings

These controls appear on the Voice tab:

- **Speed** (0.5 to 2.0). Higher is faster.
- **Noise scale** (0.0 to 2.0). How much the voice varies in tone. Default 0.67.
- **Noise W** (0.0 to 2.0). How much the rhythm varies. Default 0.8.

### Audio player

**Audio player** on the Voice tab chooses the program used to play WAV files.

- **Auto (detect every run)** looks for a player each time PiperScribe starts.
- **Default (detect and save)** looks for a player once and remembers it.
- Or choose a specific player from the list.

If the player you picked is not installed, PiperScribe looks for another one.

On Linux, install `alsa-utils` to get `aplay`, or install PipeWire's `pw-play`
or PulseAudio's `paplay`.

### Deleting a voice

On the Voice tab, select a voice and click **Delete Selected Voice**. Both its
`.onnx` file and its `.onnx.json` file are removed.

## 9. Document settings

Right-click a document and choose **Document Settings…**. These settings apply
only to that document:

- **Title.** The name shown in the list, and used in the audio file name.
- **Voice model.** Use a different voice for this document. Click **Browse…** to find a model file.
- **Speed.** From 0.1 to 3.0. Higher is faster.
- **Noise scale** and **Noise W.** Same meaning as on the Voice tab.
- **Test Voice.** Generates and plays a short sample with these settings.

When a document has its own voice model, **Generate Audio** uses it. Otherwise
the project voice is used.

## 10. Generating audio

There are three ways to generate audio. Each one writes WAV files to the audio folder
audio folder (see [Files and folders](#18-files-and-folders)).

- **File → Generate All Audio** generates audio for every **enabled** document
  in the playlist. A progress dialog shows each step, and you can cancel. If one
  document fails, the others still run, and PiperScribe reports which one failed.
- **Right-click → Generate Audio** generates audio for one document.
- **Play** on the audio toolbar generates audio for the current document first,
  if it doesn't have any. A message reports where the file was saved, and then
  the audio plays.

Generation uses only the text that is not excluded. A document with all of its
text excluded is skipped, and PiperScribe tells you.

**Play regenerates stale audio.** PiperScribe records the voice, speed, noise
settings, and text each audio file was made from. When you press **Play**, it
checks that record. If you changed the voice (on the toolbar or in Document
Settings), the speed or noise settings, or the text, it shows the progress dialog,
generates the audio again, and then plays it. If nothing changed, it plays the
existing file. Documents made before this check was added are regenerated the
first time you press Play.

**Generate All Audio** always regenerates every enabled document.

Whenever audio has to be generated, a **Preparing Audio** popup appears and asks
you to be patient. Generation can take a minute or more for a long document.
The rest of the window keeps responding while it runs. Click **Cancel** on the
popup to stop; a document that was cancelled keeps its previous audio, if any.
Generate All stops after the document in progress.

## 11. Preview

Preview lets you hear a passage before you generate the whole document.

1. Select a few sentences in the editor.
2. Click **Preview selection** on the selection toolbar, or choose
   **Tools → Preview selection**.

PiperScribe generates the selected text and plays it. Click **Stop** on the
toolbar to cancel, or **Tools → Stop Preview**.

A new preview replaces the previous one. Preview uses the project's voice
settings (the ones on the Voice tab), not the per-document settings.

## 12. Playing audio

The audio toolbar controls playback of a document's generated audio:

- **▶ Play** starts the current document. If it has no audio, it is generated first.
- **⏸ Pause** pauses playback. Play then changes to **▶ Resume**.
- **⏹ Stop** stops playback.

Selecting a document that has audio in the document list starts playing it. Generating audio does not start playback by itself.

Changing the voice or speed while audio plays stops the playback. Press Play again
to hear the new audio.

Playback of a whole project is not automatic. Play each document in turn, or
export a playlist and play it with another player.

## 13. Exporting

### Save Audio to Folder

**File → Save Audio to Folder…** copies the generated audio for every document
into a folder you name. Choose where the folder goes, then type its name. The
name is pre-filled with the project title. Files with the same name in that
folder are replaced. Afterwards, each document plays from its new location.

Use this when you want the audio in a folder of your choice, for example to keep
it with other files for a book or course.

### Export WAV

**File → Export WAV…** saves one WAV file that contains all the enabled
documents, read in playlist order. Excluded text is left out. Export uses the
project voice settings, not the per-document voice settings.

### Export Playlist

**File → Export Playlist…** writes an M3U playlist, which VLC, mpv, and most
audio players can open, plus a JSON file next to it. The JSON file records the
project title, the number of documents, the total duration, and the list of
documents, for use by other tools. Generate audio for your documents first, or
the playlist has nothing to point at.

## 14. Finding text

Press **Ctrl+F**, or choose **Edit → Find…**. A find bar opens at the top of the
editor. Type the text you want, and use **Next** and **Prev** to move between
matches. Click **×** to close the find bar.

## 15. Preferences

Open **Edit → Preferences…**. It has three tabs.

**Appearance**
- **Theme:** System, Light, or Dark.
- **Show selection toolbar:** shows or hides the Exclude/Include/Preview/Stop toolbar.
- **Use default font** and **Use default colors:** turn these off to choose your own font, size, and colors for the editor. Use the **Background** and **Text** buttons to pick colors.

**Voice**
- Voice selection, testing, and deletion.
- Speed, noise scale, and noise W.
- The audio player.
- **Audio folder.** Where generated audio is saved. Click **Browse…** to choose a
  folder. Leave it empty to keep audio next to the project file.
- **Browse && Download Voices…**

**Rules**
- The list of regex rules, and the test area.
- **Reset Settings to Defaults** erases your saved settings and restores the defaults for every tab. Use it only if you want to start over.

Settings are saved in `~/.config/piperscribe/settings.json`, so they stay the same
between sessions.

## 16. Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+I | Import Document(s) |
| Ctrl+O | Open Document(s) (same as Import) |
| Ctrl+F | Find |
| Ctrl+Q | Quit |
| F1 | Help Contents |

Other actions have no shortcut yet. Use the menus or the toolbar buttons.

## 17. Troubleshooting

**"Piper not found" when I preview or generate audio.** The `piper` command is
not on your PATH. Install Piper, then open a new terminal and run `piper --help`.
Start PiperScribe from that terminal.

**Generation fails with a "voice" or "model" error.** The model file is missing
or was moved. Open **Preferences → Voice**, and choose the voice again.

**I hear nothing when I play audio, but generation worked.** Check the audio
player on the Voice tab. Run the player from a terminal on a WAV file to confirm
that it works. On Linux, `aplay -q somefile.wav` should play the file. If it
reports no sound device, check your system's audio output.

**No audio player was found.** Install a WAV player for your system (see
[Audio player](#audio-player)), or choose one from the list in Preferences.

**The window is larger than the screen.** This can happen on Wayland with HiDPI
scaling. Start PiperScribe with `./run-piperscribe-safe.sh`. The developer notes
are in [HIDPI_QT6_WAYLAND_FIX.md](HIDPI_QT6_WAYLAND_FIX.md).

**A PDF imports with no text.** The PDF is probably a scan. PiperScribe reads
only text-based PDFs.

**My audio disappeared.** Audio for a project that was never saved was kept in
the temporary folder, which the system may clear. To avoid this, save the audio
with **File → Save Audio to Folder…**, and set **Audio folder** in Preferences
so new audio goes somewhere permanent. PiperScribe also warns you before you
quit while audio is only in the temporary folder.

The in-app Help (**Help → Help Contents…**) has more on these topics.

## 18. Files and folders

| What | Where |
|------|-------|
| Project file | Wherever you save it, usually ending in `.abproj.json` |
| Generated audio | The **Audio folder** from Preferences, if you set one. Otherwise a folder next to the project file, named after the project with `_audio` added (for example, `MyBook.abproj.json` uses `MyBook_audio/`). |
| Audio for an unsaved project | The system temporary folder, in `piperscribe_audio/`, unless you set an Audio folder. PiperScribe warns you before you quit. |
| Audio you saved with Save Audio to Folder | The folder you chose and named |
| Settings | `~/.config/piperscribe/settings.json` (or `$XDG_CONFIG_HOME/piperscribe/settings.json`) |
| Voices | `~/.local/share/piper/voices/` by default |

Generated audio files are named after the document title, with part of the
document ID added: `Chapter-One-1a2b3c4d.wav`.
