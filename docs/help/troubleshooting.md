# Troubleshooting

## Piper TTS Issues

### Piper Not Found

**Symptom**: Error message "`piper` not found on PATH" or "Piper not found"

**Solutions**:

1. **Verify Installation**:
   ```bash
   which piper        # On Linux/macOS
   where piper        # On Windows
   ```

2. **Add to PATH**:
   - Linux/macOS: Add to `~/.bashrc` or `~/.zshrc`:
     ```bash
     export PATH="$PATH:/path/to/piper"
     ```
   - Windows: Add piper directory to System Environment Variables → Path

3. **Test in Preferences**:
   - Open **Edit → Preferences → Voice**
   - Click **Test Piper Installation**
   - Should show "Found Piper at: /path/to/piper"

4. **Reinstall Piper**:
   - Download from [github.com/rhasspy/piper](https://github.com/rhasspy/piper)
   - Follow installation instructions for your platform

### Piper Fails to Run

**Symptom**: Piper found but fails to execute

**Solutions**:
- Verify piper has execute permissions: `chmod +x /path/to/piper`
- Check piper version compatibility
- Try running piper manually: `piper --help`

## Voice Issues

### No Voices Available

**Symptom**: Voice dropdown shows "(no voices found)"

**Solutions**:

1. **Download Voices**:
   - Open **Tools → Browse & Download Voices**
   - Download at least one voice model
   - Voices install to `~/.local/share/piper/voices/`

2. **Manually Install Voices**:
   - Download .onnx and .onnx.json files from [Hugging Face](https://huggingface.co/rhasspy/piper-voices)
   - Place in `~/.local/share/piper/voices/`
   - Restart PiperScribe

3. **Check Voice Directories**:
   - Piper searches these locations:
     - `~/.local/share/piper/voices`
     - `~/share/piper/voices`
     - `/usr/share/piper-voices`
     - `/usr/local/share/piper-voices`

4. **Verify Permissions**:
   - Ensure voice directory is readable: `ls -la ~/.local/share/piper/voices`

### Voice Test Fails

**Symptom**: "Test Selected Voice" button produces error

**Solutions**:
- Verify voice file exists and isn't corrupted
- Re-download voice if necessary
- Check that both .onnx and .onnx.json files are present
- Try a different voice

### Downloaded Voice Not Appearing

**Symptom**: Voice browser shows download success but voice not in dropdown

**Solutions**:
- Close and reopen Preferences dialog
- Voice should appear immediately after closing Voice Browser
- Check `~/.local/share/piper/voices/` for .onnx file

## Audio Playback Issues

### No Audio Heard

**Symptom**: TTS generation completes but no sound

**Solutions**:

1. **Check System Audio**:
   - Verify system volume is not muted
   - Test with other applications
   - Check audio output device selection

2. **Test Audio Player**:
   - Linux: Ensure `aplay` is installed (part of alsa-utils)
   - Test: `aplay /usr/share/sounds/alsa/Front_Center.wav`

3. **Try Different Voice**:
   - Some voices may produce very quiet output
   - Adjust Noise Scale parameter in Preferences

4. **Export and Play Externally**:
   - Use **File → Export Audio**
   - Play WAV file in external player
   - If this works, issue is with internal playback

### Audio Cuts Off

**Symptom**: Audio stops mid-sentence

**Solutions**:
- Check for errors in console/logs
- Try shorter text segments
- Increase timeout settings (if available)
- Update Piper to latest version

## Import/Export Issues

### Import Fails

**Symptom**: Error when importing TXT, DOCX, PDF, or Markdown

**Solutions**:

1. **Check File Format**:
   - Verify file is not corrupted
   - Try opening file in its native application
   - Supported formats: .txt, .docx, .pdf, .md

2. **Install Optional Dependencies**:
   ```bash
   pip install "piperscribe[importers]"
   ```
   - Required for DOCX, PDF, Markdown import
   - TXT import works without extra dependencies

3. **Check File Permissions**:
   - Ensure file is readable: `ls -l /path/to/file`

4. **Try Simpler Format**:
   - If DOCX/PDF fails, copy-paste text or export to TXT

### Export Fails

**Symptom**: Error when exporting audio or text

**Solutions**:
- Verify destination directory is writable
- Check available disk space
- Ensure audio has been generated before exporting
- Try different export location

## Performance Issues

### Slow TTS Generation

**Symptom**: Audio generation takes very long time

**Causes**:
- Large documents require more processing time
- Complex voice models are slower
- System resource constraints

**Solutions**:
- Generate smaller sections using selection preview
- Use lower-quality voice models for faster processing
- Close other applications to free resources
- Consider upgrading hardware (CPU is primary bottleneck)

### High Memory Usage

**Symptom**: Application uses excessive RAM

**Solutions**:
- Clear generated audio before processing new content
- Save and restart application periodically
- Reduce document size
- Close unused dialogs

## Preferences/Settings Issues

### Preferences Won't Open

**Symptom**: Edit → Preferences does nothing or shows error

**Solutions**:
- Check console for error messages
- Verify settings file isn't corrupted: `~/.config/piperscribe/settings.json`
- Reset settings: Delete `~/.config/piperscribe/settings.json` and restart
- See logs for detailed error information

### Settings Not Saving

**Symptom**: Changes to preferences don't persist

**Solutions**:
- Click **Apply** or **OK**, not just close dialog
- Check that `~/.config/piperscribe/` is writable
- Verify no permission errors in console
- Try manually editing `settings.json` (as JSON)

### Dialog Too Large for Screen

**Symptom**: Can't reach buttons in Preferences dialog

**Solutions**:
- This should be fixed in recent versions
- Try resizing window manually
- Use keyboard: Tab to navigate, Enter to accept
- Update to latest version

## Regex Rules Issues

### Rule Doesn't Match Expected Text

**Symptom**: Regex pattern doesn't find text you expect

**Solutions**:
- Use **Test** button with sample text
- Check pattern flags (case sensitivity, multiline, dotall)
- Test pattern in online regex tester: [regex101.com](https://regex101.com)
- Escape special characters: `. * + ? ^ $ { } [ ] \ | ( )`

### Rules Applied in Wrong Order

**Symptom**: Text processed incorrectly due to rule sequence

**Solutions**:
- Rules process top-to-bottom
- Reorder rules by duplicating and deleting
- Test with small samples before applying to full document

### Auto-Apply Rules Not Working

**Symptom**: Rules don't automatically process text

**Solutions**:
- Verify **Auto-apply rules** is enabled in Preferences
- Try manual **Reapply All Rules** button
- Check that rules are enabled (not disabled)

## Project File Issues

### Can't Open Project

**Symptom**: Error loading .json project file

**Solutions**:
- Verify file is valid JSON
- Check file isn't corrupted (open in text editor)
- Try creating new project and re-importing content
- Restore from backup if available

### Project Missing Content

**Symptom**: Opened project but text/settings are missing

**Causes**:
- File saved incorrectly
- Incompatible version

**Solutions**:
- Check file size (should be > 0 bytes)
- Open .json file to inspect contents
- Use **File → Import** to recover text from original source

## Getting More Help

### Where to Report Bugs

1. Check existing issues: [github.com/your-repo/piperscribe/issues](https://github.com)
2. Create new issue with:
   - PiperScribe version
   - Operating system and version
   - Steps to reproduce problem
   - Error messages or logs
   - Screenshots (if applicable)

### Log Files

Look for diagnostic information:
- Linux: Check terminal output or `~/.local/share/piperscribe/logs/`
- Windows: Check console window or AppData logs
- Run from terminal to see real-time output

### Community Support

- GitHub Discussions
- Project documentation
- Piper TTS documentation: [github.com/rhasspy/piper](https://github.com/rhasspy/piper)

### Workarounds

If you encounter persistent issues:
1. Save work frequently
2. Export audio regularly
3. Keep backups of important projects
4. Use stable voice models
5. Process in smaller chunks
