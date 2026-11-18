# webview-mac-proof

A small test: does a local animated web page inside a native window, driven from Python with
[pywebview](https://pywebview.flowrl.com/), work on macOS (Apple Silicon), both from source and as a PyInstaller app?

The workflow opens a real window on a GitHub macOS runner and records: animation frames and frame gaps, a looping
CSS animation, a bundled local font (and a missing one as a control), Web Audio state without a click, a call from
Python to the page and a call from the page to Python. Results are printed in the job log and uploaded as files.

The font in `web/fonts/` is Tektur, under the SIL Open Font License 1.1 (see `web/fonts/OFL.txt`).
