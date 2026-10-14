"""Demo de login y perfil con HTTP y SQLite de la biblioteca estándar."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("LOGIN_DB", ROOT / "data" / "login.sqlite3"))
SESSION_SECONDS = 60 * 60


def connect(db_path=DB_PATH):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def password_hash(password, salt=None):
    # Una sal distinta por usuario evita que contraseñas iguales generen hashes iguales.
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}:{digest.hex()}"


def check_password(password, stored):
    salt_hex, expected = stored.split(":", 1)
    actual = password_hash(password, bytes.fromhex(salt_hex)).split(":", 1)[1]
    return hmac.compare_digest(actual, expected)


def init_db(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = connect(db_path)
    try:
        with db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    expires_at INTEGER NOT NULL
                );
            """)
            for name, email, role, password in (
                ("Ana García", "ana@demo.local", "admin", "AnaDemo123!"),
                ("Luis Moreno", "luis@demo.local", "miembro", "LuisDemo123!"),
            ):
                db.execute(
                    "INSERT OR IGNORE INTO users (name, email, role, password_hash) VALUES (?, ?, ?, ?)",
                    (name, email, role, password_hash(password)),
                )
    finally:
        db.close()


def authenticate(email, password, db_path=DB_PATH):
    if not isinstance(email, str) or not isinstance(password, str) or not password:
        return None
    db = connect(db_path)
    try:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        if user is None or not check_password(password, user["password_hash"]):
            return None
        return dict(user)
    finally:
        db.close()


def create_session(user_id, db_path=DB_PATH):
    token = secrets.token_urlsafe(32)
    db = connect(db_path)
    try:
        with db:
            db.execute(
                "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                (token, user_id, int(time.time()) + SESSION_SECONDS),
            )
    finally:
        db.close()
    return token


def get_profile(token, db_path=DB_PATH):
    if not token:
        return None
    db = connect(db_path)
    try:
        row = db.execute("""
            SELECT users.id, users.name, users.email, users.role
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.expires_at > ?
        """, (token, int(time.time()))).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        db.close()


def logout(token, db_path=DB_PATH):
    if not token:
        return
    db = connect(db_path)
    try:
        with db:
            db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    finally:
        db.close()


class Handler(BaseHTTPRequestHandler):
    db_path = DB_PATH

    def send_json(self, status, payload, cookie=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            return cookie["session"].value if "session" in cookie else None
        except Exception:
            return None

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 10_000:
                return None
            data = json.loads(self.rfile.read(length))
            return data if isinstance(data, dict) else None
        except (ValueError, json.JSONDecodeError):
            return None

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/profile":
            profile = get_profile(self.token(), self.db_path)
            return self.send_json(HTTPStatus.OK if profile else HTTPStatus.UNAUTHORIZED,
                                  profile or {"error": "Inicia sesión."})
        files = {"/": ("index.html", "text/html"),
                 "/profile": ("profile.html", "text/html"),
                 "/styles.css": ("styles.css", "text/css"),
                 "/app.js": ("app.js", "text/javascript")}
        if path not in files:
            return self.send_json(HTTPStatus.NOT_FOUND, {"error": "No encontrado."})
        filename, mime = files[path]
        body = (ROOT / "static" / filename).read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/login":
            data = self.read_json()
            if data is None:
                return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Datos inválidos."})
            user = authenticate(data.get("email"), data.get("password"), self.db_path)
            if user is None:
                return self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Credenciales inválidas."})
            token = create_session(user["id"], self.db_path)
            cookie = f"session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_SECONDS}"
            return self.send_json(HTTPStatus.OK, {"ok": True}, cookie)
        if path == "/api/logout":
            logout(self.token(), self.db_path)
            return self.send_json(HTTPStatus.OK, {"ok": True},
                                  "session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")
        return self.send_json(HTTPStatus.NOT_FOUND, {"error": "No encontrado."})


def main():
    init_db(DB_PATH)
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Demo disponible en http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
