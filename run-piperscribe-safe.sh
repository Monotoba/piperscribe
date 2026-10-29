#!/usr/bin/env bash
# Launch PiperScribe with Qt HiDPI workarounds. See docs/HIDPI_QT6_WAYLAND_FIX.md.
set -euo pipefail

cd "$(dirname "$0")"

if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
  export QT_QPA_PLATFORM=xcb
fi

unset QT_SCALE_FACTOR QT_SCREEN_SCALE_FACTORS QT_AUTO_SCREEN_SCALE_FACTOR QT_ENABLE_HIGHDPI_SCALING
export QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough

exec ./.venv/bin/piperscribe "$@"
