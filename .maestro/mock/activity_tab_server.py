#!/usr/bin/env python3
"""Mock MediaWiki backend for the Activity tab Maestro flows.

Stands in for the home wiki that the app is pointed at through the debug-only
``apiBaseUrl`` launch argument (see ``org.wikipedia.settings.AppConfig``). It serves
just enough of the MediaWiki APIs to

  1. sign a user in without a CAPTCHA or a second factor, and
  2. give the Activity tab's modules real, deterministic content, so a flow can
     meaningfully assert that a module is - or is no longer - on screen.

Routes
------
Action API (``/w/api.php``)
  ``action=query&meta=tokens``               login/CSRF tokens
  ``action=clientlogin`` (POST)              PASS for MOCK_USERNAME/MOCK_PASSWORD
  ``action=query&meta=userinfo``             the signed-in user (id, name, groups)
  ``action=query&meta=globaluserinfo&...``   global edit count + page info, which is what
                                             the "All time impact" module renders
  ``action=query&list=usercontribs``         the edits the Timeline module lists
  ``action=query&...&titles=|pageids=``      page info for those timeline entries

Core REST API (``/w/rest.php``)
  ``growthexperiments/v0/user-impact/#<id>`` the GrowthUserImpact payload behind
                                             the "All time impact" module

Everything else answers with a benign empty payload, so unrelated startup traffic
(Explore feed, announcements, site info, ...) fails soft instead of crashing the app.

Standard library only, so there is no install step.

Environment variables:
  PORT            port to listen on            (default 8080)
  MOCK_USERNAME   username expected to sign in (default maestro-user)
  MOCK_PASSWORD   password expected to sign in (default correct-horse-battery)
"""

import json
import os
import sys
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", "8080"))
USERNAME = os.environ.get("MOCK_USERNAME", "maestro-user")
PASSWORD = os.environ.get("MOCK_PASSWORD", "correct-horse-battery")

USER_ID = 424242
LOGIN_TOKEN = "mock-login-token+\\"
CSRF_TOKEN = "mock-csrf-token+\\"

# The edits the Timeline module lists. Both are recent, so the timeline renders a single,
# predictable "Today" date separator above them.
TIMELINE_PAGES = [
    {"pageid": 7001, "revid": 900001, "title": "Maestro (software)",
     "description": "Mobile UI testing framework"},
    {"pageid": 7002, "revid": 900002, "title": "Android (operating system)",
     "description": "Mobile operating system"},
]


def _iso_utc(minutes_ago):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _edit_counts_by_day():
    """A dense editCountByDay map, so the impact module's charts have something to draw."""
    today = datetime.now(timezone.utc).date()
    return {(today - timedelta(days=n)).isoformat(): (n % 4) + 1 for n in range(30, -1, -1)}


def _daily_total_views():
    today = datetime.now(timezone.utc).date()
    return {(today - timedelta(days=n)).isoformat(): 100 + n * 7 for n in range(30, -1, -1)}


def _db_key(title):
    """MediaWiki's own normalisation: spaces and underscores are interchangeable in titles."""
    return title.replace("_", " ").strip()


def page_entries(titles=None, page_ids=None):
    """`prop=info|description|pageimages` style page objects.

    Titles come back in display form (spaces, never underscores) exactly like the real API,
    because `PageTitle.text` re-adds the underscores when ActivityTabViewModel.loadImpact()
    looks each page back up in the impact payload's `topViewedArticles` map - with `!!`, so a
    mismatch here is a crash rather than a soft failure.
    """
    selected = TIMELINE_PAGES
    if titles:
        wanted = [_db_key(t) for t in titles.split("|") if t]
        selected = [p for p in TIMELINE_PAGES if p["title"] in wanted]
        known = {p["title"] for p in selected}
        selected = selected + [
            {"pageid": 7100 + i, "revid": 0, "title": t, "description": "Mock article"}
            for i, t in enumerate(wanted) if t not in known
        ]
    elif page_ids:
        wanted = {int(p) for p in page_ids.split("|") if p.strip().isdigit()}
        selected = [p for p in TIMELINE_PAGES if p["pageid"] in wanted]

    return [
        {
            "pageid": page["pageid"],
            "ns": 0,
            "title": page["title"],
            "displaytitle": page["title"],
            "description": page["description"],
            "descriptionsource": "local",
            "varianttitles": {"en": page["title"]},
        }
        for page in selected
    ]


def token_response():
    return {"batchcomplete": True,
            "query": {"tokens": {"logintoken": LOGIN_TOKEN, "csrftoken": CSRF_TOKEN}}}


def login_passed_response(username):
    return {"clientlogin": {"status": "PASS", "username": username}}


def login_failed_response():
    return {"clientlogin": {"status": "FAIL",
                            "message": "Incorrect username or password entered.",
                            "messagecode": "wrongpassword"}}


def user_info_response(username):
    return {
        "batchcomplete": True,
        "query": {"userinfo": {
            "id": USER_ID,
            "name": username,
            "groups": ["*", "user", "autoconfirmed"],
            "editcount": 4242,
            "registrationdate": "2019-04-01T09:00:00Z",
            "latestcontrib": _iso_utc(30),
        }},
    }


def global_user_info_response(titles):
    return {
        "batchcomplete": True,
        "query": {
            "globaluserinfo": {"home": "enwiki", "id": USER_ID, "name": USERNAME, "editcount": 4242},
            "pages": page_entries(titles=titles),
        },
    }


def user_contribs_response():
    return {
        "batchcomplete": True,
        "query": {"usercontribs": [
            {
                "userid": USER_ID,
                "user": USERNAME,
                "pageid": page["pageid"],
                "revid": page["revid"],
                "parentid": page["revid"] - 1,
                "ns": 0,
                "title": page["title"],
                "timestamp": _iso_utc(30 + i * 45),
                "comment": "Mock edit for the Activity tab timeline",
                "new": False,
                "minor": False,
                "top": True,
                "size": 12000 + i,
                "sizediff": 120 + i,
                "tags": [],
            }
            for i, page in enumerate(TIMELINE_PAGES)
        ]},
    }


def user_impact_response():
    now = datetime.now(timezone.utc)
    return {
        "@version": 6,
        "userId": USER_ID,
        "userName": USERNAME,
        "receivedThanksCount": 37,
        "givenThanksCount": 12,
        "editCountByNamespace": {"0": 4200, "1": 42},
        "editCountByDay": _edit_counts_by_day(),
        "editCountByTaskType": {"copyedit": 30, "links": 12},
        "totalUserEditCount": 4242,
        "totalEditsCount": 4242,
        "newcomerTaskEditCount": 42,
        "revertedEditCount": 1,
        "lastEditTimestamp": int((now - timedelta(minutes=30)).timestamp()),
        "totalArticlesCreatedCount": 9,
        "longestEditingStreak": {
            "datePeriod": {
                "start": (now - timedelta(days=21)).date().isoformat(),
                "end": (now - timedelta(days=7)).date().isoformat(),
                "days": 14,
            },
            "totalEditCountForPeriod": 140,
        },
        "dailyTotalViews": _daily_total_views(),
        "totalPageviewsCount": 987654,
        # Keyed the way GrowthExperiments keys them - by db title, i.e. with underscores. The app
        # joins these keys into the follow-up `titles=` query and then looks the pages back up by
        # `PageTitle.text`, which is also the underscored form.
        "topViewedArticles": {
            page["title"].replace(" ", "_"): {
                "firstEditDate": (now - timedelta(days=60)).date().isoformat(),
                "newestEdit": _iso_utc(30),
                "imageUrl": "",
                "viewsCount": 4321 - i * 100,
                "views": {},
            }
            for i, page in enumerate(TIMELINE_PAGES)
        },
    }


class MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("[mock] %s\n" % (fmt % args))

    def _send(self, body, status=200):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _params(self):
        return parse_qs(urlparse(self.path).query)

    @staticmethod
    def _one(params, key, default=""):
        return params.get(key, [default])[0]

    def do_GET(self):
        path = urlparse(self.path).path
        params = self._params()

        # Core REST: GrowthExperiments user impact. Retrofit sends the user id pre-encoded as
        # `%23<id>` (a literal '#'), so match on the prefix rather than the whole path.
        if path.startswith("/w/rest.php/growthexperiments/v0/user-impact/"):
            self._send(user_impact_response())
            return

        if path == "/w/api.php":
            action = self._one(params, "action")
            meta = self._one(params, "meta")
            listing = self._one(params, "list")

            if action == "query" and "tokens" in meta:
                self._send(token_response())
                return
            if action == "query" and "globaluserinfo" in meta:
                self._send(global_user_info_response(self._one(params, "titles")))
                return
            if action == "query" and "userinfo" in meta and not listing:
                self._send(user_info_response(self.server.signed_in_user or USERNAME))
                return
            if action == "query" and listing == "usercontribs":
                self._send(user_contribs_response())
                return
            if action == "query" and (params.get("titles") or params.get("pageids")):
                self._send({"batchcomplete": True, "query": {"pages": page_entries(
                    titles=self._one(params, "titles"),
                    page_ids=self._one(params, "pageids"))}})
                return

            self._send({"batchcomplete": True, "query": {}})
            return

        # Unrelated startup traffic (REST v1 feed, announcements, ...): fail soft.
        self._send({}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path
        params = self._params()
        length = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}

        if path == "/w/api.php" and self._one(params, "action") == "clientlogin":
            username = self._one(form, "username", USERNAME)
            password = self._one(form, "password")
            if username == USERNAME and password == PASSWORD:
                self.server.signed_in_user = username
                self.log_message("clientlogin PASS for %s", username)
                self._send(login_passed_response(username))
            else:
                self.log_message("clientlogin FAIL for %s", username)
                self._send(login_failed_response())
            return

        self._send({"batchcomplete": True})


class MockServer(ThreadingHTTPServer):
    # The app opens several connections in parallel while the home screen warms up.
    request_queue_size = 128
    allow_reuse_address = True
    daemon_threads = True
    signed_in_user = None


def main():
    server = MockServer(("0.0.0.0", PORT), MockHandler)
    sys.stderr.write("[mock] listening on 0.0.0.0:%d  user=%s\n" % (PORT, USERNAME))
    sys.stderr.flush()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
