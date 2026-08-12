"""One-time APS Design Automation registration: AppBundle + Activity."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def token(client_id: str, client_secret: str) -> str:
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all data:read data:write data:create bucket:create bucket:read",
        }
    ).encode()
    req = urllib.request.Request(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())["access_token"]


def api(tok: str, method: str, url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Authorization": f"Bearer {tok}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode(errors='replace')}") from e


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True, help="FamilyOpsDA.zip AppBundle")
    parser.add_argument("--engine", default="Autodesk.Revit+2025")
    parser.add_argument("--bundle-id", default="FamilyOpsBundle")
    parser.add_argument("--activity-id", default="FamilyOpsActivity")
    args = parser.parse_args()

    cid = os.environ.get("APS_CLIENT_ID", "")
    secret = os.environ.get("APS_CLIENT_SECRET", "")
    if not cid or not secret:
        raise SystemExit("Set APS_CLIENT_ID and APS_CLIENT_SECRET")

    tok = token(cid, secret)
    nickname = os.environ.get("APS_NICKNAME")
    if nickname:
        api(tok, "PATCH", "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me", {"nickname": nickname})
    me = api(tok, "GET", "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me")
    # me may be a string nickname in some responses
    nick = nickname or (me if isinstance(me, str) else me.get("nickname") or cid)

    bundle_qualified = f"{nick}.{args.bundle_id}"
    # create / update appbundle
    try:
        api(
            tok,
            "POST",
            "https://developer.api.autodesk.com/da/us-east/v3/appbundles",
            {"id": args.bundle_id, "engine": args.engine, "description": "FamilyOpsDA"},
        )
    except SystemExit as e:
        if "409" not in str(e):
            print(str(e), file=sys.stderr)

    # new version + upload
    ver = api(
        tok,
        "POST",
        f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{args.bundle_id}/versions",
        {"engine": args.engine, "description": f"upload {time.time()}"},
    )
    upload = ver["uploadParameters"]
    form = upload["formData"]
    boundary = "----FamilyOpsBoundary"
    body = b""
    for k, v in form.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    file_bytes = args.bundle.read_bytes()
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{args.bundle.name}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    ureq = urllib.request.Request(
        upload["endpointURL"],
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(ureq, timeout=300) as resp:
        resp.read()

    alias_payload = {"version": ver["version"], "id": "prod"}
    try:
        api(
            tok,
            "POST",
            f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{args.bundle_id}/aliases",
            alias_payload,
        )
    except SystemExit:
        api(
            tok,
            "PATCH",
            f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{args.bundle_id}/aliases/prod",
            {"version": ver["version"]},
        )

    activity = {
        "id": args.activity_id,
        "commandLine": [
            "$(engine.path)\\\\revitcoreconsole.exe /al \"$(appbundles[{0}].path)\"".format(args.bundle_id)
        ],
        "parameters": {
            "revit_ops": {"verb": "get", "description": "ops json", "localName": "revit_ops.json", "required": True},
            "template": {"verb": "get", "description": "family template", "localName": "template.rft", "required": True},
            "result": {"verb": "put", "description": "output rfa", "localName": "result.rfa", "required": True},
        },
        "engine": args.engine,
        "appbundles": [f"{bundle_qualified}+prod"],
        "description": "Build .rfa from revit_ops.json",
    }
    try:
        api(tok, "POST", "https://developer.api.autodesk.com/da/us-east/v3/activities", activity)
    except SystemExit as e:
        if "409" not in str(e):
            print(str(e), file=sys.stderr)

    act_ver = api(
        tok,
        "POST",
        f"https://developer.api.autodesk.com/da/us-east/v3/activities/{args.activity_id}/versions",
        {k: v for k, v in activity.items() if k != "id"},
    )
    try:
        api(
            tok,
            "POST",
            f"https://developer.api.autodesk.com/da/us-east/v3/activities/{args.activity_id}/aliases",
            {"version": act_ver["version"], "id": "prod"},
        )
    except SystemExit:
        api(
            tok,
            "PATCH",
            f"https://developer.api.autodesk.com/da/us-east/v3/activities/{args.activity_id}/aliases/prod",
            {"version": act_ver["version"]},
        )

    activity_id = f"{nick}.{args.activity_id}+prod"
    print("Registered.")
    print(f"export APS_ACTIVITY_ID={activity_id}")
    print(f"AppBundle: {bundle_qualified}+prod")


if __name__ == "__main__":
    main()
