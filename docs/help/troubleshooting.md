# Troubleshooting

**"Piper not found" when you preview or generate audio.** The `piper` command
is not on your PATH. Install Piper, open a new terminal, run `piper --help`, and
start PiperScribe from that terminal.

**Generation fails.** The voice model file may be missing or moved. Open
**Edit → Preferences → Voice** and choose the voice again.

**Audio generated, but nothing plays.** Check the **Audio player** setting on
the Voice tab. Test your player from a terminal on a WAV file. On Linux,
`aplay -q somefile.wav` should play it.

**No audio player was found.** Install a WAV player for your system, or choose
one in **Edit → Preferences → Voice**.

**The window is larger than the screen.** This can happen on Wayland with HiDPI
scaling. Start PiperScribe with `./run-piperscribe-safe.sh`.

**A PDF imports with no text.** The PDF is probably a scan. PiperScribe reads
text-based PDFs only.

**The audio is gone after a restart.** Audio made before the project was saved
was in the temporary folder. Use **File → Save Audio to Folder…** to keep it,
and set **Audio folder** in Preferences so new audio is saved permanently.

The full manual is under **Help → Help Contents…** → **User Manual**.
