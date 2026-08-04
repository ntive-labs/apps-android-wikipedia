#!/usr/bin/env python3
"""Mock MediaWiki backend for the Maestro login-CAPTCHA test cases (2 and 3).

The Wikipedia app is pointed at this server with the debug-only launch-argument seam
(`apiBaseUrl`, see org.wikipedia.settings.AppConfig), which redirects the *home wiki*'s
Action API (/w/api.php), REST v1 API (/api/rest_v1/) and core REST API (/w/rest.php/).

It reproduces the exact MediaWiki conversation that org.wikipedia.login.LoginClient
performs when a login requires an image CAPTCHA:

  1. GET  /w/api.php?action=query&meta=tokens&type=login
         -> a login token
  2. POST /w/api.php?action=clientlogin        (username + password, no captcha)
         -> {"clientlogin": {"status": "FAIL", ...}}
  3. GET  /w/api.php?action=query&meta=authmanagerinfo&amirequestsfor=login
         -> a CaptchaAuthenticationRequest carrying a captchaId, which is what makes
            LoginClient call back with `uiPrompt(captchaId = ...)` and makes
            LoginActivity show the image-captcha widget.
  4. GET  /w/index.php?title=Special:Captcha/image&wpCaptchaId=<id>
         -> a generated PNG that spells out the expected answer
  5. POST /w/api.php?action=clientlogin        (now with captchaId + captchaWord)
         -> {"clientlogin": {"status": "PASS", "username": ...}} when the word matches
  6. GET  /w/api.php?action=query&meta=userinfo...
         -> the signed-in user's info, which completes the login

Tapping the CAPTCHA image asks for a replacement challenge (CaptchaHandler.requestNewCaptcha),
which adds two more exchanges — these are what test case 3 exercises:

  7. GET  /w/api.php?action=fancycaptchareload
         -> a *new* captcha index, exactly as MediaWiki's FancyCaptcha does. Each reload
            mints a fresh id (`mock-captcha-reload-N`), so the app ends up pointing at a
            different image URL than the one it was showing.
  8. GET  /w/index.php?title=Special:Captcha/image&wpCaptchaId=<new id>
         -> a *different* PNG: replacement ids render `--reload-answer` (and use a
            different noise seed), so the served bytes differ from the original image.

The word a replacement challenge expects is remembered, so a later clientlogin carrying
that id only passes when it is answered with the word drawn into *that* image.

`GET /mock/stats` reports what the server has been asked for since the current login
attempt started — the reload count and one entry per CAPTCHA image served (id + SHA-256
of the exact bytes) — which is how a flow proves that a replacement image was fetched,
that it really differs from the original, and that it was requested exactly once.

Everything else answers with a benign, empty-but-valid MediaWiki response so that the
rest of the app (Explore feed, announcements, site info, ...) fails softly instead of
throwing while the test drives the login screen.

Usage:
    python3 .maestro/mock/captcha_login_server.py [--port 8080] [--answer AMBERTIDE]
                                                  [--reload-answer ZEBRAWIND]

No third-party dependencies: it uses only the Python standard library, and the CAPTCHA
PNG is rendered from a built-in 5x7 bitmap font.
"""

import argparse
import hashlib
import json
import math
import random
import re
import struct
import sys
import threading
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DEFAULT_PORT = 8080
DEFAULT_ANSWER = "AMBERTIDE"
DEFAULT_RELOAD_ANSWER = "ZEBRAWIND"
CAPTCHA_ID = "mock-captcha-4242"
RELOAD_CAPTCHA_ID_PREFIX = "mock-captcha-reload-"

# Noise/wobble seed for the very first challenge. Replacement challenges derive their own
# seed from their id, so two images never come out byte-identical even by accident.
ORIGINAL_CAPTCHA_SEED = 1234

# The user name the mock reports back on a successful login. Overridden per-run by the
# username the flow actually types (the app stores whatever `clientlogin.username` says).
DEFAULT_USER_ID = 24601


# --------------------------------------------------------------------------------------
# Tiny 5x7 bitmap font, enough to draw the CAPTCHA answer into a PNG.
# --------------------------------------------------------------------------------------

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000",) * 7,
}

BACKGROUND = (247, 245, 238)
INK = (32, 32, 32)
NOISE = (150, 150, 150)


def _png_bytes(width, height, pixels):
    """Encode an RGB pixel buffer (list of rows of (r, g, b)) as a PNG."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter type 0 (None)
        for r, g, b in row:
            raw += bytes((r, g, b))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def render_captcha_png(text, scale=5, seed=1234):
    """Render `text` as a slightly distorted, noisy CAPTCHA-looking PNG."""
    text = text.upper()
    glyphs = [FONT.get(ch, FONT[" "]) for ch in text]
    gap = 2 * scale
    pad = 2 * scale
    wobble = 3 * scale

    width = pad * 2 + sum(5 * scale for _ in glyphs) + gap * max(len(glyphs) - 1, 0)
    height = pad * 2 + 7 * scale + wobble * 2

    pixels = [[BACKGROUND for _ in range(width)] for _ in range(height)]
    rng = random.Random(seed)

    def put(x, y, color):
        if 0 <= x < width and 0 <= y < height:
            pixels[y][x] = color

    # Draw the glyphs, giving each column a sine wobble so the text is not axis aligned.
    cursor = pad
    for glyph in glyphs:
        for row_index, row in enumerate(glyph):
            for col_index, bit in enumerate(row):
                if bit != "1":
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        x = cursor + col_index * scale + dx
                        y = pad + wobble + row_index * scale + dy
                        y += int(wobble * math.sin(x / (4.0 * scale)))
                        put(x, y, INK)
        cursor += 5 * scale + gap

    # Speckle noise and two wavy strike-through lines, like MediaWiki's FancyCaptcha.
    for _ in range(width * height // 60):
        put(rng.randrange(width), rng.randrange(height), NOISE)
    for phase in (0.0, 2.0):
        for x in range(width):
            y = height // 2 + int((height / 4.0) * math.sin(x / (3.0 * scale) + phase))
            put(x, y, NOISE)
            put(x, y + 1, NOISE)

    return _png_bytes(width, height, pixels)


# --------------------------------------------------------------------------------------
# MediaWiki response builders
# --------------------------------------------------------------------------------------

def tokens_response():
    return {
        "batchcomplete": True,
        "query": {
            "tokens": {
                "logintoken": "mock-login-token+\\",
                "csrftoken": "mock-csrf-token+\\",
                "watchtoken": "mock-watch-token+\\",
            }
        },
    }


def captcha_authmanager_response():
    """authmanagerinfo advertising an image CAPTCHA — MwQueryResult.captchaId() reads this."""
    return {
        "batchcomplete": True,
        "query": {
            "authmanagerinfo": {
                "canauthenticatenow": True,
                "requests": [
                    {
                        "id": "CaptchaAuthenticationRequest",
                        "metadata": {},
                        "required": "required",
                        "provider": "FancyCaptcha",
                        "account": "",
                        "fields": {
                            "captchaId": {
                                "type": "hidden",
                                "label": "captcha-id",
                                "help": "captcha-id-help",
                                "value": CAPTCHA_ID,
                            },
                            "captchaWord": {
                                "type": "string",
                                "label": "captcha-word",
                                "help": "captcha-word-help",
                            },
                        },
                    }
                ],
            }
        },
    }


def empty_authmanager_response():
    return {"batchcomplete": True, "query": {"authmanagerinfo": {"canauthenticatenow": True, "requests": []}}}


def anon_userinfo_response():
    return {"batchcomplete": True, "query": {"userinfo": {"id": 0, "name": "10.0.2.2", "anon": True}}}


def logged_in_userinfo_response(user_name):
    return {
        "batchcomplete": True,
        "query": {
            "userinfo": {
                "id": DEFAULT_USER_ID,
                "name": user_name,
                "groups": ["*", "user", "autoconfirmed"],
                "rights": ["read", "edit"],
                "editcount": 42,
                "options": {},
            }
        },
    }


def clientlogin_fail():
    return {
        "clientlogin": {
            "status": "FAIL",
            "message": "Incorrect username or password entered. Please try again.",
            "messagecode": "wrongpassword",
        }
    }


def clientlogin_captcha_fail():
    return {
        "clientlogin": {
            "status": "FAIL",
            "message": "Incorrect or expired CAPTCHA answer. Please try again.",
            "messagecode": "captcha-createaccount-fail",
        }
    }


def clientlogin_pass(user_name):
    return {"clientlogin": {"status": "PASS", "username": user_name}}


def site_info_response():
    return {
        "batchcomplete": True,
        "query": {
            "general": {
                "mainpage": "Main Page",
                "sitename": "Wikipedia",
                "lang": "en",
                "maxarticlesize": 2097152,
            },
            "autocreatetempuser": {"enabled": False},
        },
    }


# --------------------------------------------------------------------------------------
# HTTP handler
# --------------------------------------------------------------------------------------

class MockState:
    def __init__(self, answer, reload_answer=DEFAULT_RELOAD_ANSWER):
        self.answer = answer.upper()
        self.reload_answer = reload_answer.upper()
        self.lock = threading.Lock()
        self.captcha_offered = False
        self.logged_in_user = None
        self.login_attempts = 0
        # Everything below is per-login-attempt bookkeeping for test case 3.
        self.reload_requests = 0
        self.image_requests = []
        # captcha id -> the word drawn into that challenge's image.
        self.captcha_words = {CAPTCHA_ID: self.answer}

    def reset(self):
        self.captcha_offered = False
        self.logged_in_user = None
        self.login_attempts = 0
        self.reload_requests = 0
        self.image_requests = []
        self.captcha_words = {CAPTCHA_ID: self.answer}

    def new_reload_captcha(self):
        """Mint the id of a replacement challenge, like FancyCaptcha handing out a new index."""
        self.reload_requests += 1
        captcha_id = "%s%d" % (RELOAD_CAPTCHA_ID_PREFIX, self.reload_requests)
        self.captcha_words[captcha_id] = self.reload_answer
        return captcha_id

    def word_for(self, captcha_id):
        return self.captcha_words.get(captcha_id)

    def stats(self):
        return {
            "login_attempts": self.login_attempts,
            "captcha_offered": self.captcha_offered,
            "logged_in_user": self.logged_in_user,
            "original_captcha_id": CAPTCHA_ID,
            # How many times action=fancycaptchareload was called, i.e. how many replacement
            # challenges the app asked for.
            "captcha_reload_requests": self.reload_requests,
            "reload_captcha_ids": [
                cid for cid in self.captcha_words if cid.startswith(RELOAD_CAPTCHA_ID_PREFIX)
            ],
            # One entry per Special:Captcha/image GET, in the order they arrived.
            "captcha_image_requests": list(self.image_requests),
            "captcha_image_request_count": len(self.image_requests),
        }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    state = None  # injected in main()

    # ---- plumbing ----------------------------------------------------------------

    def log_message(self, fmt, *args):
        sys.stderr.write("[mock] %s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status=200):
        self._send(json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8", status)

    # ---- routing -----------------------------------------------------------------

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = parsed.path

        if path == "/w/index.php" and "Special:Captcha/image" in query.get("title", [""])[0]:
            self._handle_captcha_image(query.get("wpCaptchaId", [""])[0])
            return

        if path == "/mock/reset":
            with self.state.lock:
                self.state.reset()
            self._send_json({"mock": "reset"})
            return

        if path == "/mock/stats":
            with self.state.lock:
                payload = self.state.stats()
            self._send_json(payload)
            return

        if path == "/w/api.php":
            self._handle_action_api(query)
            return

        if path.startswith("/api/rest_v1/") or path.startswith("/w/rest.php/"):
            # Reading surfaces are irrelevant to this test; answer softly so nothing crashes.
            self._send_json({}, status=404)
            return

        self._send_json({"mock": "unhandled", "path": path}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else ""
        form = parse_qs(body, keep_blank_values=True)

        if parsed.path == "/w/api.php" and query.get("action", [""])[0] == "clientlogin":
            self._handle_client_login(form)
            return

        if parsed.path == "/w/api.php":
            self._handle_action_api(query)
            return

        self._send_json({"mock": "unhandled", "path": parsed.path}, status=404)

    # ---- CAPTCHA image -----------------------------------------------------------

    def _handle_captcha_image(self, captcha_id):
        """Serve the PNG for `captcha_id` and remember exactly what was handed out.

        Each challenge renders its own word, so the replacement image the app fetches after
        a reload genuinely differs from the original one - byte for byte and to the eye.
        """
        is_reload = captcha_id.startswith(RELOAD_CAPTCHA_ID_PREFIX)
        with self.state.lock:
            # An unrecognised id falls back to the original challenge, so a stray request is
            # never mistaken for a replacement.
            word = self.state.word_for(captcha_id) or self.state.answer
            seed = zlib.crc32(captcha_id.encode()) if is_reload else ORIGINAL_CAPTCHA_SEED

        png = render_captcha_png(word, seed=seed)
        digest = hashlib.sha256(png).hexdigest()

        with self.state.lock:
            self.state.image_requests.append({
                "captchaId": captcha_id,
                "word": word,
                "sha256": digest,
                "bytes": len(png),
                "isReload": is_reload,
            })
            ordinal = len(self.state.image_requests)

        self.log_message("captcha image #%d: id=%s word=%s sha256=%s", ordinal, captcha_id, word, digest[:12])
        self._send(png, "image/png")

    # ---- Action API --------------------------------------------------------------

    def _handle_action_api(self, query):
        action = query.get("action", [""])[0]
        meta = query.get("meta", [""])[0]

        if action == "query":
            if "tokens" in meta:
                self._send_json(tokens_response())
                return
            if "authmanagerinfo" in meta:
                requests_for = query.get("amirequestsfor", [""])[0]
                with self.state.lock:
                    offer = requests_for == "login" and self.state.login_attempts > 0 and self.state.logged_in_user is None
                    if offer:
                        self.state.captcha_offered = True
                self._send_json(captcha_authmanager_response() if offer else empty_authmanager_response())
                return
            if "userinfo" in meta:
                with self.state.lock:
                    user = self.state.logged_in_user
                self._send_json(logged_in_userinfo_response(user) if user else anon_userinfo_response())
                return
            if "siteinfo" in meta:
                self._send_json(site_info_response())
                return
            self._send_json({"batchcomplete": True, "query": {}})
            return

        if action == "fancycaptchareload":
            # CaptchaHandler.requestNewCaptcha() lands here when the user taps the image.
            # Hand out a brand new index, like FancyCaptcha does - returning the same id
            # would leave the app showing the very same challenge.
            with self.state.lock:
                captcha_id = self.state.new_reload_captcha()
                count = self.state.reload_requests
            self.log_message("fancycaptchareload #%d -> new captcha id %s", count, captcha_id)
            self._send_json({"fancycaptchareload": {"index": captcha_id}})
            return

        if action == "parse":
            text = query.get("text", [""])[0]
            self._send_json({"parse": {"title": "API", "text": "<p>%s</p>" % text}})
            return

        # Anything else (logout, echo, options, ...) succeeds with an empty envelope.
        self._send_json({"batchcomplete": True})

    def _handle_client_login(self, form):
        user_name = form.get("username", [""])[0]
        captcha_id = form.get("captchaId", [""])[0]
        captcha_word = form.get("captchaWord", [""])[0]

        with self.state.lock:
            if not captcha_id and not captcha_word:
                # A credentials-only submit always starts a brand new login attempt, so reset
                # the state here: the flow can then be re-run any number of times without
                # restarting the server.
                self.state.reset()
            self.state.login_attempts += 1
            attempt = self.state.login_attempts

            if not captcha_id and not captcha_word:
                # First submit: credentials alone are never enough — MediaWiki answers FAIL and
                # the app then discovers the CAPTCHA requirement through authmanagerinfo.
                self.log_message("clientlogin #%d: no captcha supplied -> FAIL", attempt)
                payload = clientlogin_fail()
            elif captcha_word.strip().upper() == self.state.word_for(captcha_id):
                # Answered with the word drawn into *that* challenge's image - which after a
                # reload is the replacement word, not the original one.
                self.state.logged_in_user = user_name or "MockUser"
                self.log_message("clientlogin #%d: captcha %s accepted -> PASS for %s", attempt, captcha_id, self.state.logged_in_user)
                payload = clientlogin_pass(self.state.logged_in_user)
            else:
                self.log_message("clientlogin #%d: wrong captcha %r -> FAIL", attempt, captcha_word)
                payload = clientlogin_captcha_fail()

        self._send_json(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--answer", default=DEFAULT_ANSWER, help="the CAPTCHA answer the flow will type")
    parser.add_argument("--reload-answer", default=DEFAULT_RELOAD_ANSWER,
                        help="the answer drawn into replacement CAPTCHA images (after a reload)")
    args = parser.parse_args()

    for name, value in (("--answer", args.answer), ("--reload-answer", args.reload_answer)):
        if not re.fullmatch(r"[A-Za-z0-9]+", value):
            parser.error("%s must be alphanumeric (the built-in font only covers A-Z and 0-9)" % name)

    if args.answer.upper() == args.reload_answer.upper():
        parser.error("--reload-answer must differ from --answer, otherwise a replacement "
                     "CAPTCHA would be indistinguishable from the original one")

    Handler.state = MockState(args.answer, args.reload_answer)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    sys.stderr.write(
        "[mock] MediaWiki captcha-login mock listening on http://%s:%d (captcha answer: %s, after reload: %s)\n"
        % (args.host, args.port, Handler.state.answer, Handler.state.reload_answer)
    )
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
