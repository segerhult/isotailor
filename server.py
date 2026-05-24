import argparse
import cgi
import html
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_INDEX_PATH = DATA_DIR / "uploads.json"


DEFAULT_SOFTWARE = [
    "curl",
    "git",
    "htop",
    "nano",
    "openssh-server",
    "python3",
    "rsync",
    "sudo",
    "vim",
    "wget",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if not UPLOADS_INDEX_PATH.exists():
        UPLOADS_INDEX_PATH.write_text(json.dumps({"uploads": {}}, indent=2), encoding="utf-8")


def load_index() -> dict:
    ensure_storage()
    try:
        return json.loads(UPLOADS_INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"uploads": {}}


def save_index(index: dict) -> None:
    ensure_storage()
    tmp_path = UPLOADS_INDEX_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(UPLOADS_INDEX_PATH)


def normalize_software_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        item = raw.strip()
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned


def parse_custom_software(text: str) -> list[str]:
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts.append(line)
    return parts


def page(title: str, body: str) -> bytes:
    doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; max-width: 900px; }}
      .row {{ display: flex; gap: 24px; flex-wrap: wrap; }}
      .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 16px; flex: 1; min-width: 320px; }}
      .muted {{ color: #666; }}
      label {{ display: block; margin: 6px 0; }}
      input[type="text"] {{ width: 100%; padding: 8px; }}
      textarea {{ width: 100%; min-height: 110px; padding: 8px; }}
      button {{ padding: 10px 14px; border-radius: 8px; border: 1px solid #333; background: #111; color: #fff; cursor: pointer; }}
      a {{ color: #0a58ca; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 6px; }}
      .error {{ color: #b00020; }}
      ul {{ padding-left: 18px; }}
    </style>
  </head>
  <body>
    {body}
  </body>
</html>
"""
    return doc.encode("utf-8")


def software_checkboxes(selected: set[str]) -> str:
    items = []
    for name in DEFAULT_SOFTWARE:
        checked = "checked" if name in selected else ""
        items.append(
            f'<label><input type="checkbox" name="software" value="{html.escape(name)}" {checked} /> {html.escape(name)}</label>'
        )
    return "\n".join(items)


class IsoTailorHandler(BaseHTTPRequestHandler):
    server_version = "isotailor/0.1"

    def send_html(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def not_found(self) -> None:
        body = page(
            "Not Found",
            "<h1>Not Found</h1><p class='muted'>That page does not exist.</p><p><a href='/'>Go home</a></p>",
        )
        self.send_html(HTTPStatus.NOT_FOUND, body)

    def bad_request(self, message: str) -> None:
        body = page(
            "Bad Request",
            f"<h1>Bad Request</h1><p class='error'>{html.escape(message)}</p><p><a href='/'>Go home</a></p>",
        )
        self.send_html(HTTPStatus.BAD_REQUEST, body)

    def method_not_allowed(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            index = load_index()
            upload_count = len(index.get("uploads", {}))
            body = page(
                "isotailor",
                f"""
                <h1>isotailor</h1>
                <p class="muted">Upload an ISO and choose what software should be installed.</p>
                <div class="row">
                  <div class="card">
                    <h2>Create job</h2>
                    <form action="/create" method="post" enctype="multipart/form-data">
                      <label>ISO file</label>
                      <input type="file" name="iso" accept=".iso" required />
                      <hr />
                      <label><strong>Software</strong> (defaults)</label>
                      {software_checkboxes(set())}
                      <label style="margin-top: 10px;"><strong>Custom software</strong> (one per line)</label>
                      <textarea name="custom_software" placeholder="e.g.\nDocker\nkubectl"></textarea>
                      <div style="margin-top: 14px;">
                        <button type="submit">Upload ISO + Save selection</button>
                      </div>
                    </form>
                  </div>
                  <div class="card">
                    <h2>Existing uploads</h2>
                    <p class="muted">{upload_count} saved</p>
                    <p><a href="/uploads">View uploads</a></p>
                    <p class="muted">Data is stored locally under <code>./data</code>.</p>
                  </div>
                </div>
                """,
            )
            self.send_html(HTTPStatus.OK, body)
            return

        if path == "/uploads":
            index = load_index()
            uploads = index.get("uploads", {})
            items = []
            for upload_id, meta in sorted(uploads.items(), key=lambda kv: kv[1].get("created_at", ""), reverse=True):
                original = meta.get("original_filename", upload_id)
                items.append(
                    f"<li><a href='/uploads/{html.escape(upload_id)}'>{html.escape(original)}</a> "
                    f"<span class='muted'>(id: <code>{html.escape(upload_id)}</code>)</span></li>"
                )
            body = page(
                "Uploads",
                f"""
                <h1>Uploads</h1>
                <p><a href="/">Home</a></p>
                <ul>
                  {''.join(items) if items else "<li class='muted'>No uploads yet</li>"}
                </ul>
                """,
            )
            self.send_html(HTTPStatus.OK, body)
            return

        if path.startswith("/uploads/"):
            parts = [p for p in path.split("/") if p]
            if len(parts) == 2:
                upload_id = parts[1]
                index = load_index()
                meta = index.get("uploads", {}).get(upload_id)
                if not meta:
                    self.not_found()
                    return
                software = meta.get("software", [])
                software_html = "".join(f"<li>{html.escape(s)}</li>" for s in software) or "<li class='muted'>None</li>"
                body = page(
                    f"Upload {upload_id}",
                    f"""
                    <h1>Upload</h1>
                    <p><a href="/uploads">Back</a></p>
                    <p><strong>ID:</strong> <code>{html.escape(upload_id)}</code></p>
                    <p><strong>ISO:</strong> {html.escape(meta.get("original_filename",""))}</p>
                    <p class="muted"><strong>Stored at:</strong> <code>{html.escape(meta.get("iso_path",""))}</code></p>
                    <p class="muted"><strong>Created:</strong> {html.escape(meta.get("created_at",""))}</p>
                    <h2>Software to install</h2>
                    <ul>{software_html}</ul>
                    <p><a href="/uploads/{html.escape(upload_id)}/edit">Edit software selection</a></p>
                    """,
                )
                self.send_html(HTTPStatus.OK, body)
                return

            if len(parts) == 3 and parts[2] == "edit":
                upload_id = parts[1]
                index = load_index()
                meta = index.get("uploads", {}).get(upload_id)
                if not meta:
                    self.not_found()
                    return
                selected = set(meta.get("software", []))
                custom_only = [s for s in meta.get("software", []) if s not in DEFAULT_SOFTWARE]
                custom_text = "\n".join(custom_only)
                body = page(
                    f"Edit {upload_id}",
                    f"""
                    <h1>Edit software</h1>
                    <p><a href="/uploads/{html.escape(upload_id)}">Back</a></p>
                    <form action="/uploads/{html.escape(upload_id)}/software" method="post">
                      <label><strong>Software</strong> (defaults)</label>
                      {software_checkboxes(selected)}
                      <label style="margin-top: 10px;"><strong>Custom software</strong> (one per line)</label>
                      <textarea name="custom_software">{html.escape(custom_text)}</textarea>
                      <div style="margin-top: 14px;">
                        <button type="submit">Save</button>
                      </div>
                    </form>
                    """,
                )
                self.send_html(HTTPStatus.OK, body)
                return

        self.not_found()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/create":
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self.bad_request("Expected multipart/form-data")
                return

            ensure_storage()
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                },
            )

            if "iso" not in form:
                self.bad_request("Missing ISO file field")
                return

            iso_field = form["iso"]
            if not getattr(iso_field, "file", None):
                self.bad_request("Missing ISO file content")
                return

            original_filename = os.path.basename(getattr(iso_field, "filename", "") or "")
            if not original_filename.lower().endswith(".iso"):
                self.bad_request("Only .iso files are allowed")
                return

            upload_id = uuid.uuid4().hex
            stored_iso_path = UPLOADS_DIR / f"{upload_id}.iso"

            with stored_iso_path.open("wb") as out_f:
                shutil.copyfileobj(iso_field.file, out_f, length=1024 * 1024)

            selected_software = []
            if "software" in form:
                software_field = form["software"]
                if isinstance(software_field, list):
                    selected_software.extend([f.value for f in software_field])
                else:
                    selected_software.append(software_field.value)

            custom_text = ""
            if "custom_software" in form:
                custom_text = form.getfirst("custom_software", "")

            software = normalize_software_list(selected_software + parse_custom_software(custom_text))

            index = load_index()
            uploads = index.setdefault("uploads", {})
            uploads[upload_id] = {
                "id": upload_id,
                "original_filename": original_filename,
                "iso_path": str(stored_iso_path.relative_to(REPO_ROOT)),
                "created_at": now_iso(),
                "software": software,
            }
            save_index(index)

            self.redirect(f"/uploads/{upload_id}")
            return

        if path.startswith("/uploads/") and path.endswith("/software"):
            parts = [p for p in path.split("/") if p]
            if len(parts) != 3:
                self.not_found()
                return
            upload_id = parts[1]

            length_header = self.headers.get("Content-Length", "")
            try:
                content_length = int(length_header)
            except ValueError:
                self.bad_request("Invalid Content-Length")
                return

            raw = self.rfile.read(content_length).decode("utf-8", errors="replace")
            params = parse_qs(raw, keep_blank_values=True)
            selected_software = params.get("software", [])
            custom_text = (params.get("custom_software", [""])[0] or "")
            software = normalize_software_list(selected_software + parse_custom_software(custom_text))

            index = load_index()
            meta = index.get("uploads", {}).get(upload_id)
            if not meta:
                self.not_found()
                return

            meta["software"] = software
            meta["updated_at"] = now_iso()
            save_index(index)
            self.redirect(f"/uploads/{upload_id}")
            return

        self.method_not_allowed()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="isotailor")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    return p


def main() -> int:
    args = build_parser().parse_args()
    ensure_storage()
    server = ThreadingHTTPServer((args.host, args.port), IsoTailorHandler)
    print(f"Serving on http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
