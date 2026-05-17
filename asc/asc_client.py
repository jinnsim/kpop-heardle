"""
Minimal App Store Connect API client for the K-Pop Heardle submission
workflow.

Auth: ES256 JWT signed with the .p8 private key. Token TTL kept short
(10 minutes) since each script invocation is one-shot. Key + issuer
read from environment so the .p8 path and the key id never end up in
git.

Environment expected:
  ASC_KEY_ID         e.g. YJ6FY4Q284
  ASC_ISSUER_ID      e.g. 69a6de70-f5b7-47e3-e053-5b8c7c11a4d1
  ASC_KEY_PATH       absolute path to AuthKey_*.p8

Reference: https://developer.apple.com/documentation/appstoreconnectapi
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import jwt
import requests

API_BASE = "https://api.appstoreconnect.apple.com/v1"
TOKEN_TTL_SECONDS = 600  # 10 min, Apple max is 20


class ASCError(RuntimeError):
    """API error with status + parsed body if available."""
    def __init__(self, status: int, payload: Any, message: str = ""):
        super().__init__(message or f"ASC API {status}: {payload}")
        self.status = status
        self.payload = payload


class ASCClient:
    def __init__(self,
                 key_id: str | None = None,
                 issuer_id: str | None = None,
                 key_path: str | None = None):
        self.key_id = key_id or os.environ["ASC_KEY_ID"]
        self.issuer_id = issuer_id or os.environ["ASC_ISSUER_ID"]
        key_path = key_path or os.environ["ASC_KEY_PATH"]
        self._private_key = Path(key_path).read_text()
        self._token: str | None = None
        self._token_expiry: float = 0.0

    def token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expiry - 30:
            return self._token
        payload = {
            "iss": self.issuer_id,
            "iat": int(now),
            "exp": int(now + TOKEN_TTL_SECONDS),
            "aud": "appstoreconnect-v1",
        }
        self._token = jwt.encode(
            payload,
            self._private_key,
            algorithm="ES256",
            headers={"kid": self.key_id, "typ": "JWT"},
        )
        self._token_expiry = now + TOKEN_TTL_SECONDS
        return self._token

    def _headers(self, content_type: str | None = "application/json") -> dict:
        h = {"Authorization": f"Bearer {self.token()}"}
        if content_type:
            h["Content-Type"] = content_type
        return h

    def _request(self,
                 method: str,
                 path: str,
                 *,
                 params: dict | None = None,
                 json_body: dict | None = None) -> Any:
        url = path if path.startswith("http") else f"{API_BASE}{path}"
        response = requests.request(
            method, url,
            headers=self._headers(),
            params=params,
            json=json_body,
            timeout=30,
        )
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = response.text
            detail = json.dumps(payload, indent=2, ensure_ascii=False)[:1500]
            raise ASCError(response.status_code, payload,
                           f"{method} {url} → {response.status_code}\n{detail}")
        if response.status_code == 204 or not response.text:
            return None
        return response.json()

    def get(self, path: str, **params) -> Any:
        return self._request("GET", path, params=params or None)

    def post(self, path: str, body: dict) -> Any:
        return self._request("POST", path, json_body=body)

    def patch(self, path: str, body: dict) -> Any:
        return self._request("PATCH", path, json_body=body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    # ── convenience helpers ─────────────────────────────────────────────

    def list_apps(self) -> list[dict]:
        return self.get("/apps")["data"]

    def find_app(self, bundle_id: str) -> dict | None:
        for app in self.list_apps():
            if app["attributes"].get("bundleId") == bundle_id:
                return app
        return None


def main() -> int:
    """Quick smoke test — print bundle ids of apps the key can see."""
    client = ASCClient()
    apps = client.list_apps()
    print(f"Authenticated. {len(apps)} app(s) visible:")
    for app in apps:
        a = app["attributes"]
        print(f"  - id={app['id']}  bundle={a.get('bundleId')}  name={a.get('name')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
