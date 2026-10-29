# Getting Started

PiperScribe turns documents into speech with Piper voices. It runs on your
computer, so your text stays on your machine.

## Before you start

1. Install Piper, and make sure the `piper` command runs from a terminal.
   Open **Edit → Preferences → Voice** and click **Test Piper Installation**.
2. Get a voice. Use **Tools → Browse && Download Voices…**, or **Tools → Import Voice Model…**
   if you already have a `.onnx` file.
3. In the Voice tab, click **Test Selected Voice** and check that you hear a sample.

## Make your first audio

1. **File → Import Document(s)…** (Ctrl+I), or type text into the editor.
2. Select text you don't want read, and click **Exclude selection** on the selection toolbar.
3. Click **Preview selection** to hear a passage.
4. **File → Generate All Audio** to make audio for every enabled document.
5. **File → Save Project…** before you go further. Audio is kept next to the project file.
6. **File → Export WAV…** to make one WAV file of the whole project.

## Saving your audio

Audio made before you save the project goes to a temporary folder, which the
system may clear. PiperScribe warns you when you quit with audio like that.
Use **File → Save Audio to Folder…** to copy it into a folder with a name you
choose. To pick a permanent folder for all generated audio, set **Audio folder**
in **Edit → Preferences → Voice**.

For the full guide, open **Help → Help Contents…** and choose **User Manual**.
