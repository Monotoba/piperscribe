# Design notes (v0.1)

## Core model
- `DocumentProject`
  - `text`: extracted plain text
  - `exclusions`: list of half-open spans `[start, end)` into `text`
  - `piper`: settings used to call Piper

Spans are clamped, sorted, and merged via `normalize_spans()`.

## Exclude/include UX
- User selects text in the viewer
- **Exclude** adds the selection as a span
- **Include** removes overlap by clipping or deleting spans
- Rendering uses Qt `ExtraSelection` with strikethrough + grey foreground

## Export
- `included_text()` removes excluded spans
- `export_wav()` calls the Piper CLI and writes a single WAV

## Importers
Importer registry chooses based on file extension.
Each importer returns a simple `{title, text}`.

## Testing
- `tests/test_spans.py` validates merging/clamping and subtraction
- `tests/test_export.py` validates excluded text removal
- `tests/test_import_txt.py` sanity check for TXT importer

## Voice discovery (v0.1.2)
- On startup, the app scans common Piper voice directories for `*.onnx` models.
- A voice dropdown is populated from discovered models and selecting one sets the model path.
- If Piper is not on PATH, the app warns the user (import/exclude still work).
