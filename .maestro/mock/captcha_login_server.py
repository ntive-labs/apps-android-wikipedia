#!/usr/bin/env python3
"""Mock MediaWiki backend for the "login with CAPTCHA challenge" Maestro flow.

Stands in for the home wiki that the app is pointed at through the debug-only
``apiBaseUrl`` launch argument (see ``org.wikipedia.settings.AppConfig``). It
serves just enough of the Action API to drive ``LoginClient``/``LoginActivity``
through a FancyCaptcha challenge:

  1. GET  /w/api.php?action=query&meta=tokens&type=login   -> a login token
  2. POST /w/api.php?action=clientlogin  (no captcha)      -> status FAIL
  3. GET  /w/api.php?action=query&meta=authmanagerinfo     -> a captchaId, which
     makes LoginClient raise the CAPTCHA UI prompt
  4. GET  /w/index.php?title=Special:Captcha/image         -> the CAPTCHA image
  5. POST /w/api.php?action=clientlogin  (with captchaId +
     captchaWord matching MOCK_CAPTCHA_ANSWER)             -> status PASS
  6. GET  /w/api.php?action=query&meta=userinfo            -> the signed-in user

Everything else answers with a benign empty payload so unrelated startup traffic
(feed, announcements, site info, ...) fails soft instead of crashing the app.

Only the Python standard library is used, so no install step is needed.

Environment variables:
  PORT                  port to listen on               (default 8080)
  MOCK_USERNAME         username expected to sign in    (default maestro-user)
  MOCK_PASSWORD         password expected to sign in    (default correct-horse-battery)
  MOCK_CAPTCHA_ANSWER   the word drawn in the CAPTCHA   (default WIKI42)
"""

import json
import os
import struct
import sys
import threading
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", "8080"))
USERNAME = os.environ.get("MOCK_USERNAME", "maestro-user")
PASSWORD = os.environ.get("MOCK_PASSWORD", "correct-horse-battery")
CAPTCHA_ANSWER = os.environ.get("MOCK_CAPTCHA_ANSWER", "WIKI42")

LOGIN_TOKEN = "mock-login-token+\\"
CAPTCHA_ID = "mock-captcha-1234"

# --------------------------------------------------------------------------
# A dependency-free PNG renderer, so the CAPTCHA image the app displays
# actually shows the answer the flow is going to type.
# --------------------------------------------------------------------------

FONT_5X7 = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}

GLYPH_W, GLYPH_H = 5, 7
SCALE = 6
PAD = 12


def render_captcha_png(word):
    """Draw `word` as a grayscale PNG that mimics a FancyCaptcha image."""
    glyphs = [FONT_5X7.get(ch.upper(), FONT_5X7[" "]) for ch in word]
    width = PAD * 2 + len(glyphs) * (GLYPH_W + 1) * SCALE
    height = PAD * 2 + GLYPH_H * SCALE
    # Light background with faint horizontal "noise" banding.
    pixels = [[0xEC if (y // 3) % 2 else 0xF6 for _ in range(width)] for y in range(height)]

    for index, glyph in enumerate(glyphs):
        # A small per-character vertical wobble, like a real CAPTCHA.
        wobble = (-1, 1, 0, 2, -2, 1)[index % 6] * (SCALE // 2)
        x0 = PAD + index * (GLYPH_W + 1) * SCALE
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                for dy in range(SCALE):
                    y = PAD + row * SCALE + dy + wobble
                    if not 0 <= y < height:
                        continue
                    for dx in range(SCALE):
                        x = x0 + col * SCALE + dx
                        if 0 <= x < width:
                            pixels[y][x] = 0x20

    # Strike-through line, another classic CAPTCHA distortion.
    for x in range(width):
        y = height // 2 + int(3 * SCALE * (0.5 - abs((x / width) - 0.5)))
        for dy in range(2):
            if 0 <= y + dy < height:
                pixels[y + dy][x] = 0x50

    raw = b"".join(b"\x00" + bytes(row) for row in pixels)

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


CAPTCHA_PNG = render_captcha_png(CAPTCHA_ANSWER)

# --------------------------------------------------------------------------
# Canned API payloads
# --------------------------------------------------------------------------

LOGIN_TOKEN_RESPONSE = {
    "batchcomplete": True,
    "query": {"tokens": {"logintoken": LOGIN_TOKEN}},
}

# Mirrors action=query&meta=authmanagerinfo&amirequestsfor=login for a wiki that
# has FancyCaptcha switched on. MwQueryResult.captchaId() reads
# requests[].fields.captchaId.value out of this.
AUTH_MANAGER_LOGIN_RESPONSE = {
    "batchcomplete": True,
    "query": {
        "authmanagerinfo": {
            "requests": [
                {
                    "id": "CaptchaAuthenticationRequest",
                    "required": "optional",
                    "provider": "FancyCaptcha",
                    "account": "",
                    "fields": {
                        "captchaId": {
                            "type": "hidden",
                            "label": "captcha-id",
                            "help": "Question ID",
                            "value": CAPTCHA_ID,
                        },
                        "captchaWord": {
                            "type": "string",
                            "label": "captcha-label",
                            "help": "Type the words that appear in the image.",
                        },
                    },
                }
            ]
        }
    },
}

CAPTCHA_REQUIRED_MESSAGE = (
    "To help protect against automated login attempts, please solve the CAPTCHA below."
)


def login_failed_response():
    return {
        "clientlogin": {
            "status": "FAIL",
            "message": CAPTCHA_REQUIRED_MESSAGE,
            "messagecode": "captcha-required",
        }
    }


def login_passed_response(username):
    return {"clientlogin": {"status": "PASS", "username": username}}


def user_info_response(username):
    return {
        "batchcomplete": True,
        "query": {
            "userinfo": {
                "id": 424242,
                "name": username,
                "groups": ["*", "user", "autoconfirmed"],
                "editcount": 12,
            }
        },
    }


class MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("[mock] %s\n" % (fmt % args))

    # -- helpers -----------------------------------------------------------
    def _send(self, body, content_type="application/json; charset=utf-8", status=200):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _query(self):
        return parse_qs(urlparse(self.path).query)

    def _param(self, params, key, default=""):
        return params.get(key, [default])[0]

    # -- routing -----------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path
        params = self._query()

        if path == "/w/index.php" and "Captcha" in self._param(params, "title"):
            self._send(CAPTCHA_PNG, content_type="image/png")
            return

        if path == "/w/api.php":
            action = self._param(params, "action")
            meta = self._param(params, "meta")
            if action == "query" and "tokens" in meta and "login" in self._param(params, "type"):
                self._send(LOGIN_TOKEN_RESPONSE)
                return
            if action == "query" and "authmanagerinfo" in meta:
                self._send(AUTH_MANAGER_LOGIN_RESPONSE)
                return
            if action == "query" and "userinfo" in meta:
                self._send(user_info_response(self.server.signed_in_user or USERNAME))
                return
            self._send({"batchcomplete": True, "query": {}})
            return

        # Unrelated startup traffic (REST feed, announcements, ...): fail soft.
        self._send({}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path
        params = self._query()
        length = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}

        if path == "/w/api.php" and self._param(params, "action") == "clientlogin":
            username = self._param(form, "username", USERNAME)
            password = self._param(form, "password")
            captcha_id = self._param(form, "captchaId")
            captcha_word = self._param(form, "captchaWord")

            solved = (
                captcha_id == CAPTCHA_ID
                and captcha_word.strip().upper() == CAPTCHA_ANSWER.upper()
            )
            credentials_ok = username == USERNAME and password == PASSWORD

            if solved and credentials_ok:
                self.server.signed_in_user = username
                self.log_message("clientlogin PASS for %s (captcha solved)", username)
                self._send(login_passed_response(username))
            else:
                self.log_message(
                    "clientlogin FAIL for %s (captcha_id=%r word=%r) -> require captcha",
                    username,
                    captcha_id,
                    captcha_word,
                )
                self._send(login_failed_response())
            return

        self._send({"batchcomplete": True})


class MockServer(ThreadingHTTPServer):
    # The app opens several connections in parallel while the home screen warms up.
    request_queue_size = 128
    allow_reuse_address = True
    signed_in_user = None


def main():
    server = MockServer(("0.0.0.0", PORT), MockHandler)
    server.signed_in_user = None
    server.daemon_threads = True
    sys.stderr.write(
        "[mock] listening on 0.0.0.0:%d  user=%s captcha=%s\n"
        % (PORT, USERNAME, CAPTCHA_ANSWER)
    )
    sys.stderr.flush()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
