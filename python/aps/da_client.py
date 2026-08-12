"""Autodesk Platform Services — Design Automation for Revit (.rfa generation)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class ApsError(RuntimeError):
    pass


class ApsClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        bucket: str | None = None,
        activity_id: str | None = None,
    ):
        self.client_id = client_id or os.environ.get("APS_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("APS_CLIENT_SECRET", "")
        self.bucket = (bucket or os.environ.get("APS_BUCKET", "substation-family-agent")).lower()
        self.activity_id = activity_id or os.environ.get(
            "APS_ACTIVITY_ID", ""
        )  # e.g. <nickname>.FamilyOpsActivity+prod
        self.region = os.environ.get("APS_REGION", "US")
        self._token: str | None = None
        self._token_expires = 0.0

        if not self.client_id or not self.client_secret:
            raise ApsError(
                "Missing APS_CLIENT_ID / APS_CLIENT_SECRET. "
                "Create an app at https://aps.autodesk.com/myapps and export the secrets."
            )
        if not self.activity_id:
            raise ApsError(
                "Missing APS_ACTIVITY_ID. Complete one-time setup in revit/APS_SETUP.md "
                "then export APS_ACTIVITY_ID=<nickname>.FamilyOpsActivity+prod"
            )

    def token(self) -> str:
        if self._token and time.time() < self._token_expires - 60:
            return self._token
        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "data:read data:write data:create bucket:read bucket:create code:all",
            }
        ).encode()
        req = urllib.request.Request(
            "https://developer.api.autodesk.com/authentication/v2/token",
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        data = self._json(req)
        self._token = data["access_token"]
        self._token_expires = time.time() + int(data.get("expires_in", 3600))
        return self._token

    def _json(self, req: urllib.request.Request) -> Any:
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise ApsError(f"APS HTTP {e.code}: {detail}") from e

    def _auth_headers(self, content_type: str | None = "application/json") -> dict[str, str]:
        h = {"Authorization": f"Bearer {self.token()}"}
        if content_type:
            h["Content-Type"] = content_type
        return h

    def ensure_bucket(self) -> None:
        url = f"https://developer.api.autodesk.com/oss/v2/buckets"
        payload = json.dumps(
            {"bucketKey": self.bucket, "policyKey": "temporary", "access": "full"}
        ).encode()
        req = urllib.request.Request(url, data=payload, method="POST", headers=self._auth_headers())
        try:
            self._json(req)
        except ApsError as e:
            if "409" not in str(e) and "BucketAlreadyExists" not in str(e):
                # already exists is fine
                if "already exists" not in str(e).lower():
                    raise

    def upload(self, local_path: Path, object_key: str) -> str:
        """Upload file; return signed GET URL for DA workitem."""
        self.ensure_bucket()
        object_key = object_key.lstrip("/")
        size = local_path.stat().st_size
        # S3 signed upload (OSS v2)
        params = urllib.parse.urlencode({"minutesExpiration": 60})
        url = (
            f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket}"
            f"/objects/{urllib.parse.quote(object_key, safe='')}/signeds3upload?{params}"
        )
        req = urllib.request.Request(url, method="GET", headers=self._auth_headers(None))
        meta = self._json(req)
        upload_key = meta["uploadKey"]
        urls = meta["urls"]
        with open(local_path, "rb") as f:
            data = f.read()
        # single-part for typical ops/json/rft sizes
        put = urllib.request.Request(urls[0], data=data, method="PUT", headers={"Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(put, timeout=300) as resp:
            resp.read()
        complete = json.dumps({"uploadKey": upload_key}).encode()
        creq = urllib.request.Request(
            f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket}"
            f"/objects/{urllib.parse.quote(object_key, safe='')}/signeds3upload",
            data=complete,
            method="POST",
            headers=self._auth_headers(),
        )
        self._json(creq)
        return self.signed_download_url(object_key)

    def signed_download_url(self, object_key: str, minutes: int = 60) -> str:
        object_key = object_key.lstrip("/")
        url = (
            f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket}"
            f"/objects/{urllib.parse.quote(object_key, safe='')}/signed"
            f"?access=read&minutesExpiration={minutes}"
        )
        req = urllib.request.Request(url, method="POST", data=b"{}", headers=self._auth_headers())
        return self._json(req)["url"]

    def signed_upload_url(self, object_key: str, minutes: int = 60) -> str:
        object_key = object_key.lstrip("/")
        url = (
            f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket}"
            f"/objects/{urllib.parse.quote(object_key, safe='')}/signed"
            f"?access=write&minutesExpiration={minutes}"
        )
        req = urllib.request.Request(url, method="POST", data=b"{}", headers=self._auth_headers())
        return self._json(req)["url"]

    def submit_workitem(
        self,
        ops_url: str,
        template_url: str,
        result_put_url: str,
    ) -> str:
        payload = {
            "activityId": self.activity_id,
            "arguments": {
                "revit_ops": {"url": ops_url, "localName": "revit_ops.json", "verb": "get"},
                "template": {"url": template_url, "localName": "template.rft", "verb": "get"},
                "result": {"url": result_put_url, "verb": "put", "localName": "result.rfa"},
            },
        }
        req = urllib.request.Request(
            "https://developer.api.autodesk.com/da/us-east/v3/workitems",
            data=json.dumps(payload).encode(),
            method="POST",
            headers=self._auth_headers(),
        )
        data = self._json(req)
        return data["id"]

    def wait_workitem(self, workitem_id: str, timeout_s: int = 900, poll_s: float = 5.0) -> dict:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            req = urllib.request.Request(
                f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}",
                method="GET",
                headers=self._auth_headers(None),
            )
            data = self._json(req)
            status = data.get("status")
            if status in ("success", "failed", "cancelled"):
                return data
            time.sleep(poll_s)
        raise ApsError(f"Workitem {workitem_id} timed out")

    def download(self, url: str, dest: Path) -> Path:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=300) as resp:
            dest.write_bytes(resp.read())
        return dest


def generate_rfa(
    job_dir: Path,
    template_rft: Path,
    family_name: str | None = None,
) -> Path:
    """Upload ops+template, run DA workitem, download result.rfa into job_dir."""
    job_dir = Path(job_dir)
    ops = job_dir / "revit_ops.json"
    if not ops.exists():
        raise ApsError(f"Missing {ops}")
    if not template_rft.exists():
        raise ApsError(
            f"Missing family template: {template_rft}\n"
            "Copy a Metric Generic Model / Electrical Equipment .rft from your Revit "
            "templates folder and set APS_TEMPLATE_RFT."
        )

    plan_path = job_dir / "family_plan.json"
    if family_name is None and plan_path.exists():
        family_name = json.loads(plan_path.read_text()).get("family_name", "Equipment")
    family_name = family_name or "Equipment"

    client = ApsClient()
    stamp = job_dir.name
    ops_url = client.upload(ops, f"{stamp}/revit_ops.json")
    template_url = client.upload(Path(template_rft), f"{stamp}/template.rft")
    result_key = f"{stamp}/result.rfa"
    result_put = client.signed_upload_url(result_key)

    wid = client.submit_workitem(ops_url, template_url, result_put)
    print(f"APS workitem {wid} submitted…")
    status = client.wait_workitem(wid)
    print(json.dumps({"workitem": wid, "status": status.get("status"), "reportUrl": status.get("reportUrl")}, indent=2))
    if status.get("status") != "success":
        raise ApsError(f"Design Automation failed: {status}")

    dest = job_dir / f"{family_name}.rfa"
    # download via signed GET on the object we uploaded to
    get_url = client.signed_download_url(result_key)
    client.download(get_url, dest)
    # also keep canonical name
    (job_dir / "result.rfa").write_bytes(dest.read_bytes())
    print(f"Wrote {dest}")
    return dest
