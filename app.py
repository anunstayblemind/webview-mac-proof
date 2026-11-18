"""Proof: a local animated web page inside a native window, from Python, with pywebview.

Checks, and writes to a JSON file: animation frames ran, a CSS animation looped, a bundled local font loaded
(and a deliberately missing one did not), Web Audio started without a click, Python called the page and the page
called Python. Exit code 0 only if the required checks pass.

usage: app.py <result.json> <visible|offscreen>
"""
import json
import os
import platform
import sys
import sysconfig
import threading
import time

out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "result.json")
mode = sys.argv[2] if len(sys.argv) > 2 else "visible"
t0 = time.time()
res = {"mode": mode, "frozen": bool(getattr(sys, "frozen", False)), "python": sys.version.split()[0],
       "platform": platform.platform(), "machine": platform.machine(), "mac_ver": platform.mac_ver()[0],
       "framework_python": sysconfig.get_config_var("PYTHONFRAMEWORK") or "",
       "js_called_python": [], "misses": ["did not finish"]}


def write():
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)


def hard_stop():
    res["misses"] = ["timeout after 150 s"] + [m for m in res.get("misses", []) if m != "did not finish"]
    write()
    os._exit(3)


threading.Timer(150, hard_stop).start()          # whatever happens, never hang
write()
variant = sys.argv[3] if len(sys.argv) > 3 else "server"      # "server": pywebview's built-in page server; "file": file://
res["variant"] = variant
fast = variant.endswith("-fast")       # take the host-name lookup out of the page server's start (it took 35 s on a Mac)
if fast:
    variant = variant[:-5]
res["lookup_removed"] = fast

# Where does start-up time go? Time every host-name lookup and every request the page server answers.
import socket
from wsgiref import simple_server

res["getfqdn_calls"], res["requests"] = [], []
_getfqdn = socket.getfqdn


def timed_getfqdn(name=""):
    a = time.time()
    try:
        return (name or "localhost") if fast else _getfqdn(name)
    finally:
        res["getfqdn_calls"].append([round(a - t0, 2), str(name), round(time.time() - a, 2)])


socket.getfqdn = timed_getfqdn
_handle = simple_server.WSGIRequestHandler.handle


def timed_handle(self):
    a = time.time()
    try:
        return _handle(self)
    finally:
        res["requests"].append([round(a - t0, 2), round(time.time() - t0, 2), str(getattr(self, "path", None))])


simple_server.WSGIRequestHandler.handle = timed_handle

try:
    import webview
    from importlib.metadata import version
    res["pywebview"] = version("pywebview")
except Exception as e:                          # noqa: BLE001
    res["misses"] = [f"import failed: {e!r}"]
    write()
    os._exit(4)

base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


class Api:
    def echo(self, s):
        res["js_called_python"].append(s)
        return "py-got:" + str(s)


def judge():
    p = res.get("page") or {}
    misses = []
    if not (p.get("rafFrames") or 0) >= 30:
        misses.append(f"animation frames: {p.get('rafFrames')}")
    if not (p.get("cssAnimIterations") or 0) >= 1:
        misses.append(f"css animation loops: {p.get('cssAnimIterations')}")
    if not p.get("fontCheck") or p.get("fontWidthProof") == p.get("fontWidthFallback"):
        misses.append("bundled font did not load")
    if p.get("controlMissingFontWidth") != p.get("fontWidthFallback"):
        misses.append("control: a missing font changed the text width")
    if res.get("py2js_add") != 5:
        misses.append(f"python to page: {res.get('py2js_add')!r}")
    if p.get("js2py") != "py-got:hello-from-js":
        misses.append(f"page to python: {p.get('js2py')!r}")
    if p.get("errors"):
        misses.append(f"page errors: {p.get('errors')}")
    audio = p.get("audio") or {}
    res["audio_running"] = audio.get("stateAfter700ms") == "running"      # reported, not required:
    res["misses"] = misses                                                # a build machine may have no sound device
    return misses


def run(win):
    try:
        res["renderer"] = getattr(webview, "renderer", None)
        shown = win.events.shown.wait(60)                      # how long a cold start really takes
        res["shown_s"] = round(time.time() - t0, 1) if shown else None
        loaded = win.events.loaded.wait(60)
        res["loaded_s"] = round(time.time() - t0, 1) if loaded else None
        if not loaded:
            res["misses"] = [f"page did not load within 60 s of the window (shown={shown})"]
            write()
            os._exit(2)
        res["py2js_add"] = win.evaluate_js("add(2, 3)")
        res["py2js_beep"] = win.evaluate_js("beep()")
        time.sleep(3)
        win.evaluate_js("collect().then(r => { window.__r = r; }, e => { window.__r = JSON.stringify({collectError: String(e)}); }); 1")
        time.sleep(1)
        res["page"] = json.loads(win.evaluate_js("window.__r"))
        res["seconds_to_result"] = round(time.time() - t0, 1)
        judge()
    except Exception as e:                      # noqa: BLE001
        res["misses"] = [f"exception: {e!r}"]
    write()
    try:
        win.destroy()
    except Exception:                           # noqa: BLE001
        pass
    time.sleep(0.5)
    os._exit(0 if not res["misses"] else 2)


kw = {"x": -32000, "y": -32000, "focus": False} if mode == "offscreen" else {"x": 60, "y": 60}
page = os.path.join(base, "web", {"csp": "index-csp.html", "csp-eval": "index-csp-eval.html"}.get(variant, "index.html"))
if variant == "file":
    from pathlib import Path
    page = Path(page).as_uri()
res["create_s"] = round(time.time() - t0, 2)
w = webview.create_window("proof", page, js_api=Api(), width=480, height=360, **kw)
res["start_called_s"] = round(time.time() - t0, 2)
res["t0_epoch_ms"] = round(t0 * 1000)
webview.start(run, w, http_server=(variant != "file"))
os._exit(0 if not res["misses"] else 2)
