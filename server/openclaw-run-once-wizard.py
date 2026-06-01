#!/usr/bin/env python3
"""Local-only admin form for provisioning Hostinger OpenClaw clients.

This intentionally uses only the Python standard library. It does not call any
AI agent or OpenClaw session; it validates form input and runs deterministic
shell commands on the VPS.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8099
DEFAULT_TOKEN_FILE = "/root/openclaw-client-form-token"
DEFAULT_PROVISION_CMD = "/usr/local/bin/provision-openclaw-client"
DEFAULT_DOCKER_ROOT = "/docker"
DEFAULT_OAUTH_HELPER = "/root/openclaw-codex-oauth-chat.sh"
DEFAULT_CLEANUP_COMMAND = ""
TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:-]{12,}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,50}[a-z0-9]$")
CALLBACK_RE = re.compile(r"^http://localhost:[0-9]+/auth/callback\?")
OAUTH_URL_RE = re.compile(r"https://auth\.openai\.com/oauth/authorize[^\s<>'\"]+")
DEVICE_URL_RE = re.compile(r"https?://[^\s<>'\"]+")
ANSI_RE = re.compile(r"\x1B\[[0-9;?]*[ -/]*[@-~]")
DEVICE_LABEL_URL_RE = re.compile(r"\bURL:\s*(https?://[^\s<>'\"]+)", re.IGNORECASE)
DEVICE_LABEL_CODE_RE = re.compile(r"\bCode:\s*([A-Z0-9]{4,}(?:-[A-Z0-9]{3,})+|[A-Z0-9]{6,})\b", re.IGNORECASE)
PAIRING_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{4,40}$")
SENSITIVE_KEYS = ("OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "META_API_TOKEN")
ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,80}$")
RESERVED_ENV_KEYS = {"COMPOSE_PROJECT_NAME", "PORT", "TZ", "TRAEFIK_HOST", "OPENCLAW_GATEWAY_TOKEN"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def load_or_create_token(path: Path) -> str:
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if TOKEN_RE.match(token):
            return token

    token = secrets.token_urlsafe(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "\n", encoding="utf-8")
    path.chmod(0o600)
    return token


def redact(text: str, values: list[str]) -> str:
    result = text
    for value in values:
        if value:
            result = result.replace(value, "[REDACTED]")
    for key in SENSITIVE_KEYS:
        result = re.sub(rf"({key}=)[^\s]+", rf"\1[REDACTED]", result)
    result = re.sub(r"(code=)[^&\s]+", r"\1[REDACTED]", result)
    result = re.sub(r"(state=)[^&\s]+", r"\1[REDACTED]", result)
    return result


def project_name(slug: str) -> str:
    return f"openclaw-{slug}"


def html_page(
    token: str,
    message: str = "",
    output: str = "",
    step: str = "create",
    slug: str = "",
    oauth_slug: str = "",
    oauth_url: str = "",
    device_code: str = "",
    public_url: str = "",
) -> bytes:
    safe_message = html.escape(message)
    safe_output = html.escape(output)
    safe_token = html.escape(token)
    safe_slug = html.escape(slug or oauth_slug)
    safe_oauth_slug = html.escape(oauth_slug or slug)
    safe_oauth_url = html.escape(oauth_url)
    safe_device_code = html.escape(device_code)
    safe_public_url = html.escape(public_url)
    checked_start = "checked"
    checked_smoke = "checked"
    message_html = f'<div class="msg">{safe_message}</div>' if safe_message else ""
    debug_html = ""

    create_block = f"""
      <form method="post" action="/create" data-loading="מקים לקוח OpenClaw. זה יכול לקחת דקה או שתיים.">
        <input type="hidden" name="token" value="{safe_token}">
        <div class="step-card">
          <div class="step-kicker">שלב 1 מתוך 4</div>
          <h2>יצירת לקוח</h2>
          <label for="client_name">שם לקוח / slug</label>
          <input id="client_name" name="client_name" type="text" autocomplete="off" placeholder="client-name" required>

          <label>חיבור מודל</label>
          <div class="mode-grid">
            <label><input name="auth_method" type="radio" value="oauth" checked> OpenAI OAuth</label>
            <label><input name="auth_method" type="radio" value="device_code"> OpenAI Device Code</label>
            <label><input name="auth_method" type="radio" value="api_key"> OpenAI API Key</label>
          </div>

          <div class="api-key-field">
            <label for="openai_api_key">OpenAI API Key</label>
            <input id="openai_api_key" name="openai_api_key" type="password" autocomplete="off" placeholder="sk-...">
          </div>

          <label for="telegram_bot_token">Telegram Bot Token</label>
          <input id="telegram_bot_token" name="telegram_bot_token" type="password" autocomplete="off" placeholder="123456:ABC..." required>

          <details class="advanced">
            <summary>אפשרויות מתקדמות</summary>
            <div class="row">
              <input id="start" name="start" type="checkbox" value="1" {checked_start}>
              <label for="start">להפעיל קונטיינר אחרי יצירה</label>
            </div>
            <div class="row">
              <input id="smoke" name="smoke" type="checkbox" value="1" {checked_smoke}>
              <label for="smoke">להריץ smoke אחרי חיבור מודל</label>
            </div>
            <div class="row">
              <input id="dry_run" name="dry_run" type="checkbox" value="1">
              <label for="dry_run">Dry-run בלבד</label>
            </div>
          </details>

          <button type="submit">פתח לקוח</button>
        </div>
      </form>
"""

    oauth_block = f"""
      <div class="step-card">
        <div class="step-kicker">שלב 2 מתוך 4</div>
        <h2>חיבור OpenAI</h2>
        <p class="hint">הלקוח <span dir="ltr">{safe_oauth_slug}</span> נוצר. לחץ על הכפתור, התחבר ל־OpenAI, ואז חזור לכאן עם כתובת ה־callback הסופית.</p>
        <a id="open-oauth-button" class="button-link primary" href="{safe_oauth_url}" target="_blank" rel="noopener noreferrer">פתח התחברות OpenAI</a>
      </div>
      <div id="callback-panel" class="step-card callback-panel" hidden>
        <div class="step-kicker">שלב 3 מתוך 4</div>
        <h2>הדבקת Callback URL</h2>
        <p class="hint">אחרי ההתחברות הדפדפן יגיע לכתובת שמתחילה ב־<span dir="ltr">http://localhost:</span>. הדבק כאן את כל הכתובת משורת הכתובת.</p>
        <form method="post" action="/oauth-finish" data-loading="מסיים OAuth ושומר את החיבור. האתחול יבוצע רק בסוף.">
          <input type="hidden" name="token" value="{safe_token}">
          <input type="hidden" name="slug" value="{safe_oauth_slug}">
          <label for="callback_url">Callback URL</label>
          <input id="callback_url" name="callback_url" type="text" autocomplete="off" placeholder="http://localhost:.../auth/callback?code=..." required>
          <div class="row">
            <input id="oauth_smoke" name="smoke" type="checkbox" value="1" checked>
            <label for="oauth_smoke">להריץ smoke בסוף אחרי האתחול הסופי</label>
          </div>
          <button type="submit">סיים חיבור OAuth</button>
        </form>
      </div>
"""

    device_block = f"""
      <div class="step-card">
        <div class="step-kicker">שלב 2 מתוך 4</div>
        <h2>חיבור OpenAI עם Device Code</h2>
        <p class="hint">לחץ על הכפתור, הזן את קוד האימות, ואז חזור לכאן ולחץ בדיקה. אין צורך להדביק Callback URL.</p>
        {f'<a class="button-link primary" href="{safe_oauth_url}" target="_blank" rel="noopener noreferrer">פתח אימות OpenAI</a>' if safe_oauth_url else ''}
        {f'<div class="device-code" dir="ltr">{safe_device_code}</div>' if safe_device_code else ''}
        <form method="post" action="/device-check" data-loading="בודק אם חיבור OpenAI הושלם.">
          <input type="hidden" name="token" value="{safe_token}">
          <input type="hidden" name="slug" value="{safe_oauth_slug}">
          <div class="row">
            <input id="device_smoke" name="smoke" type="checkbox" value="1" checked>
            <label for="device_smoke">להריץ smoke בסוף אחרי האתחול הסופי</label>
          </div>
          <button type="submit">בדוק חיבור OpenAI</button>
        </form>
      </div>
"""

    telegram_block = f"""
      <div class="step-card">
        <div class="step-kicker">שלב 4 מתוך 4</div>
        <h2>אישור Telegram Pairing</h2>
        <p class="hint">שלח <span dir="ltr">/start</span> לבוט של הלקוח, העתק את הקוד שהתקבל, והדבק אותו כאן. ה־slug כבר נלקח מהשלב הראשון: <span dir="ltr">{safe_slug}</span>.</p>
        <form method="post" action="/telegram-approve" data-loading="מאשר pairing. האתחול יבוצע רק בסוף.">
          <input type="hidden" name="token" value="{safe_token}">
          <input type="hidden" name="slug" value="{safe_slug}">
          <label for="pairing_code">Telegram pairing code</label>
          <input id="pairing_code" name="pairing_code" type="text" autocomplete="off" placeholder="XXXXXXX" required>
          <button type="submit">אשר pairing</button>
        </form>
      </div>
"""

    complete_block = f"""
      <div class="step-card complete">
        <div class="step-kicker">הושלם</div>
        <h2>ההתקנה הושלמה</h2>
        <p class="hint">לקוח <span dir="ltr">{safe_slug}</span> מוכן לפתיחה בדפדפן. אם הוויזרד רץ במצב חד־פעמי, שכבת ההתקנה הזמנית תימחק אוטומטית בעוד כמה שניות.</p>
        {f'<a class="button-link primary" href="{safe_public_url}" target="_blank" rel="noopener noreferrer">פתח את OpenClaw</a>' if safe_public_url else ''}
      </div>
"""

    env_block = f"""
      <div class="step-card">
        <div class="step-kicker">שלב אחרון</div>
        <h2>מפתחות ENV ללקוח</h2>
        <p class="hint">אפשר להוסיף עכשיו Meta API Token ועוד מפתחות שהלקוח צריך. הם יישמרו בקובץ <span dir="ltr">.env</span> של הפרויקט וייטענו באתחול הסופי.</p>
        <form method="post" action="/env-save" data-loading="שומר מפתחות ומבצע אתחול סופי אחד לקונטיינר.">
          <input type="hidden" name="token" value="{safe_token}">
          <input type="hidden" name="slug" value="{safe_slug}">
          <label for="meta_api_token">Meta API Token</label>
          <input id="meta_api_token" name="meta_api_token" type="password" autocomplete="off" placeholder="EAAB...">
          <label for="extra_env">מפתחות נוספים</label>
          <textarea id="extra_env" name="extra_env" autocomplete="off" spellcheck="false" placeholder="KEY=value&#10;ANOTHER_TOKEN=value"></textarea>
          <div class="row">
            <input id="final_smoke" name="smoke" type="checkbox" value="1" checked>
            <label for="final_smoke">להריץ smoke אחרי האתחול הסופי</label>
          </div>
          <button type="submit">שמור וסיים</button>
          <button class="secondary" type="submit" name="skip_env" value="1">דלג וסיים</button>
        </form>
      </div>
"""

    if step == "oauth" and safe_oauth_url:
        main_block = oauth_block
    elif step == "device":
        main_block = device_block
    elif step == "telegram":
        main_block = telegram_block
    elif step == "env":
        main_block = env_block
    elif step == "complete":
        main_block = complete_block
    else:
        main_block = create_block

    body = f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenClaw Client Provisioning</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f6f7f9; color: #111827; }}
    main {{ max-width: 820px; margin: 32px auto; padding: 0 18px; }}
    section {{ background: white; border: 1px solid #d9dee7; border-radius: 8px; padding: 22px; box-shadow: 0 10px 24px rgba(15, 23, 42, .06); }}
    h1 {{ margin: 0 0 18px; font-size: 24px; }}
    h2 {{ margin: 0 0 10px; font-size: 18px; }}
    label {{ display: block; font-weight: 650; margin: 16px 0 6px; }}
    input[type="text"], input[type="password"], textarea {{ box-sizing: border-box; width: 100%; min-height: 42px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; font-size: 16px; direction: ltr; text-align: left; }}
    textarea {{ min-height: 120px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    input:focus {{ border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, .14); outline: none; }}
    .row {{ display: flex; gap: 12px; align-items: center; margin: 14px 0; }}
    .row label {{ margin: 0; font-weight: 500; }}
    .mode-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 8px 0 10px; }}
    .mode-grid label {{ margin: 0; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; font-weight: 600; cursor: pointer; }}
    button, .button-link {{ display: inline-flex; align-items: center; justify-content: center; margin-top: 18px; min-height: 44px; border: 0; border-radius: 6px; background: #14532d; color: white; padding: 0 18px; font-size: 16px; font-weight: 700; cursor: pointer; text-decoration: none; }}
    .button-link.primary, button[type="submit"] {{ min-width: 180px; }}
    button.secondary {{ background: #334155; }}
    .msg {{ margin: 14px 0; padding: 12px; border-radius: 6px; background: #ecfdf5; border: 1px solid #86efac; white-space: pre-wrap; direction: rtl; }}
    .step-card {{ margin: 18px 0 0; padding: 18px; border-radius: 8px; background: #ffffff; border: 1px solid #d9dee7; }}
    .step-card.complete {{ background: #ecfdf5; border-color: #86efac; }}
    .step-kicker {{ color: #2563eb; font-size: 13px; font-weight: 750; margin-bottom: 6px; }}
    .callback-panel {{ border-color: #93c5fd; background: #eff6ff; }}
    .device-code {{ display: inline-flex; align-items: center; justify-content: center; min-height: 46px; margin: 12px 0 0; padding: 0 18px; border: 1px solid #93c5fd; border-radius: 6px; background: #eff6ff; color: #1e3a8a; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 20px; font-weight: 800; letter-spacing: 0; }}
    .advanced, .debug {{ margin-top: 16px; }}
    .advanced summary, .debug summary {{ cursor: pointer; color: #334155; font-weight: 650; }}
    pre {{ margin: 16px 0 0; padding: 14px; border-radius: 6px; background: #0f172a; color: #e2e8f0; overflow: auto; direction: ltr; text-align: left; font-size: 13px; }}
    .hint {{ color: #475569; font-size: 14px; line-height: 1.5; }}
    .api-key-field[data-hidden="1"] {{ display: none; }}
    .loading-overlay {{ position: fixed; inset: 0; display: none; align-items: center; justify-content: center; padding: 20px; background: rgba(15, 23, 42, .46); z-index: 9999; }}
    .loading-overlay[data-open="1"] {{ display: flex; }}
    .loading-card {{ width: min(420px, 100%); background: #fff; border-radius: 8px; padding: 22px; border: 1px solid #d9dee7; box-shadow: 0 24px 60px rgba(15, 23, 42, .24); text-align: center; }}
    .spinner {{ width: 34px; height: 34px; border: 4px solid #dbeafe; border-top-color: #2563eb; border-radius: 50%; margin: 0 auto 14px; animation: spin 1s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @media (max-width: 680px) {{ .mode-grid {{ grid-template-columns: 1fr; }} }}
  </style>
  <script>
    function showLoading(text) {{
      const overlay = document.querySelector('#loading-overlay');
      const label = document.querySelector('#loading-text');
      if (!overlay || !label) return;
      label.textContent = text || 'טוען...';
      overlay.dataset.open = '1';
    }}
    function syncAuthMode() {{
      const method = document.querySelector('input[name="auth_method"]:checked')?.value || 'oauth';
      const apiWrap = document.querySelector('.api-key-field');
      const apiInput = document.querySelector('#openai_api_key');
      if (!apiWrap || !apiInput) return;
      const hidden = method !== 'api_key';
      apiWrap.dataset.hidden = hidden ? '1' : '0';
      apiInput.required = !hidden;
    }}
    document.addEventListener('DOMContentLoaded', () => {{
      document.querySelectorAll('input[name="auth_method"]').forEach(el => el.addEventListener('change', syncAuthMode));
      syncAuthMode();
      document.querySelectorAll('form[data-loading]').forEach(form => {{
        form.addEventListener('submit', () => showLoading(form.dataset.loading));
      }});
      const oauthButton = document.querySelector('#open-oauth-button');
      const callbackPanel = document.querySelector('#callback-panel');
      if (oauthButton && callbackPanel) {{
        oauthButton.addEventListener('click', () => {{
          showLoading('פותח את OpenAI. אחרי ההתחברות חזור לכאן עם כתובת ה־callback.');
          setTimeout(() => {{
            const overlay = document.querySelector('#loading-overlay');
            if (overlay) overlay.dataset.open = '0';
            callbackPanel.hidden = false;
            callbackPanel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
          }}, 900);
        }});
      }}
    }});
  </script>
</head>
<body>
  <div id="loading-overlay" class="loading-overlay" aria-live="polite" aria-busy="true">
    <div class="loading-card">
      <div class="spinner"></div>
      <div id="loading-text">טוען...</div>
    </div>
  </div>
  <main>
    <section>
      <h1>פתיחת לקוח OpenClaw</h1>
      <p class="hint">הטופס רץ מקומית על ה־VPS ומפעיל סקריפטים רגילים בלבד. מפתחות וקישורי callback לא עוברים דרך AI.</p>
      {message_html}
      {main_block}
      {debug_html}
    </section>
  </main>
</body>
</html>
"""
    return body.encode("utf-8")


def command_output(proc: subprocess.CompletedProcess[str]) -> str:
    return (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")


def validate_no_newline(*values: str) -> bool:
    return not any(ch in "".join(values) for ch in ("\n", "\r"))


def parse_extra_env(text_value: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw_line in text_value.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"ENV line must use KEY=value format: {line}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not ENV_KEY_RE.match(key):
            raise ValueError(f"Invalid ENV key: {key}")
        if key in RESERVED_ENV_KEYS:
            raise ValueError(f"Reserved ENV key cannot be changed from the wizard: {key}")
        if "\n" in value or "\r" in value:
            raise ValueError(f"ENV value cannot contain newlines: {key}")
        env[key] = value
    return env


def extract_device_auth(output: str) -> tuple[str, str]:
    clean_output = ANSI_RE.sub("", output).replace("\r", "\n")
    urls = DEVICE_LABEL_URL_RE.findall(clean_output) or DEVICE_URL_RE.findall(clean_output)
    auth_url = ""
    for url in urls:
        lowered = url.lower()
        if "auth.openai.com" in lowered and "device" in lowered:
            auth_url = url.rstrip(" .,:;)")
            break
    if not auth_url:
        for url in urls:
            lowered = url.lower()
            if "openai" in lowered or "device" in lowered or "auth" in lowered:
                auth_url = url.rstrip(" .,:;)")
                break
    if not auth_url and urls:
        auth_url = urls[0].rstrip(" .,:;)")

    code = ""
    code_match = DEVICE_LABEL_CODE_RE.search(clean_output)
    if code_match:
        code = code_match.group(1).strip(" .,:;").upper()

    return auth_url, code


class ProvisionHandler(BaseHTTPRequestHandler):
    server: "ProvisionServer"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def send_html(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def schedule_cleanup(self, slug: str) -> None:
        cleanup_command = self.server.cleanup_command
        if not cleanup_command:
            return

        def run_cleanup() -> None:
            time.sleep(5)
            subprocess.Popen(
                [cleanup_command, slug],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        threading.Thread(target=run_cleanup, daemon=True).start()

    def valid_token(self, provided: str | None) -> bool:
        return bool(provided) and secrets.compare_digest(provided, self.server.admin_token)

    def project_dir(self, slug: str) -> Path:
        return Path(self.server.docker_root) / project_name(slug)

    def state_dir(self, slug: str) -> Path:
        return self.project_dir(slug) / "oauth"

    def find_container(self, slug: str) -> str:
        project = project_name(slug)
        for name_filter in (f"name={project}-openclaw-1", f"name={project}"):
            proc = subprocess.run(
                ["docker", "ps", "--filter", name_filter, "--format", "{{.Names}}"],
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
            )
            names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            if names:
                return names[0]
        return ""

    def client_port(self, slug: str) -> str:
        env_path = self.project_dir(slug) / ".env"
        if not env_path.exists():
            return ""
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("PORT="):
                return line.split("=", 1)[1].strip()
        return ""

    def client_public_url(self, slug: str) -> str:
        env_path = self.project_dir(slug) / ".env"
        if not env_path.exists():
            return ""
        host = ""
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("TRAEFIK_HOST="):
                host = line.split("=", 1)[1].strip()
                break
        if not host:
            return ""
        return f"https://{project_name(slug)}.{host}/"

    def upsert_client_env(self, slug: str, updates: dict[str, str]) -> tuple[int, str]:
        if not SLUG_RE.match(slug):
            raise RuntimeError("Invalid client slug.")

        env_path = self.project_dir(slug) / ".env"
        if not env_path.exists():
            raise RuntimeError(f"Client .env not found: {env_path}")

        existing_lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
        update_keys = set(updates)
        new_lines: list[str] = []
        replaced: set[str] = set()
        for line in existing_lines:
            match = re.match(r"^([A-Z][A-Z0-9_]*)=", line)
            if match and match.group(1) in update_keys:
                key = match.group(1)
                new_lines.append(f"{key}={updates[key]}")
                replaced.add(key)
            else:
                new_lines.append(line)

        missing = [key for key in updates if key not in replaced]
        if missing:
            if new_lines and new_lines[-1].strip():
                new_lines.append("")
            new_lines.append("# Client-specific integration secrets")
            for key in missing:
                new_lines.append(f"{key}={updates[key]}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        env_path.chmod(0o600)

        summary = "=== Client ENV update ===\n"
        summary += "Updated keys: " + ", ".join(sorted(updates)) + "\n"
        summary += "Client restart deferred until final wizard step.\n"
        return 0, redact(summary, list(updates.values()))

    def finalize_client(self, slug: str, run_smoke: bool) -> tuple[int, str]:
        restart_code, restart_output = self.restart_client(slug)
        combined = "=== Final client restart ===\n" + restart_output
        status_code = restart_code
        if status_code == 0 and run_smoke:
            container = self.find_container(slug)
            if not container:
                return 1, combined + f"\nNo running container found for {project_name(slug)} after restart."
            smoke_proc = subprocess.run(
                [
                    "docker",
                    "exec",
                    container,
                    "openclaw",
                    "agent",
                    "--agent",
                    "main",
                    "--session-id",
                    f"smoke-final-{slug}",
                    "-m",
                    "Reply exactly OK_OPENCLAW_FINAL",
                    "--json",
                ],
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
            )
            combined += "\n\n=== Final agent smoke ===\n" + command_output(smoke_proc)
            if smoke_proc.returncode != 0:
                combined += (
                    f"\n\nFinal smoke exit code: {smoke_proc.returncode}. "
                    "The client restart completed; smoke failures are reported as warnings."
                )
        return status_code, combined

    def restart_client(self, slug: str) -> tuple[int, str]:
        container = self.find_container(slug)
        if not container:
            return 1, f"No running container found for {project_name(slug)}"

        perm_code, perm_output = self.fix_client_permissions(slug)
        combined = perm_output

        project_dir = self.project_dir(slug)
        compose_file = project_dir / "docker-compose.yml"
        if compose_file.exists():
            pull_proc = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "--project-directory", str(project_dir), "pull", "openclaw"],
                text=True,
                capture_output=True,
                timeout=240,
                check=False,
            )
            combined += "\n\n=== Client container image pull ===\n" + command_output(pull_proc)

            up_proc = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(compose_file),
                    "--project-directory",
                    str(project_dir),
                    "up",
                    "-d",
                    "--force-recreate",
                    "openclaw",
                ],
                text=True,
                capture_output=True,
                timeout=240,
                check=False,
            )
            combined += "\n\n=== Client container recreate ===\n" + command_output(up_proc)
            if up_proc.returncode != 0:
                return max(perm_code, up_proc.returncode), combined
        else:
            combined += "\n\n=== Client container restart ===\n"
            proc = subprocess.run(
                ["docker", "restart", container],
                text=True,
                capture_output=True,
                timeout=120,
                check=False,
            )
            combined += command_output(proc)
            if proc.returncode != 0:
                return max(perm_code, proc.returncode), combined

        self.fix_client_permissions(slug)

        port = self.client_port(slug)
        if port:
            for _ in range(60):
                health = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://127.0.0.1:{port}/health"],
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                if health.stdout.strip() == "200":
                    combined += f"\nHealth after restart: 200 on port {port}"
                    return perm_code, combined
                time.sleep(1)
            combined += f"\nHealth after restart did not return 200 on port {port} within timeout."
            return 1, combined

        return perm_code, combined

    def fix_client_permissions(self, slug: str) -> tuple[int, str]:
        container = self.find_container(slug)
        if not container:
            return 1, f"=== Client data permissions ===\nNo running container found for {project_name(slug)}"

        proc = subprocess.run(
            [
                "docker",
                "exec",
                "-u",
                "0",
                container,
                "sh",
                "-lc",
                (
                    "mkdir -p /data/.openclaw/logs /data/.openclaw/agents/main/agent;"
                    "chown -R 1000:1000 /data/.openclaw /data/openclaw-codex-oauth-chat.sh 2>/dev/null || true;"
                    "chmod -R u+rwX /data/.openclaw 2>/dev/null || true;"
                    "find /data/.openclaw -type d -exec chmod 700 {} + 2>/dev/null || true;"
                    "find /data/.openclaw -type f -name '*auth*' -exec chmod 600 {} + 2>/dev/null || true"
                ),
            ],
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        combined = "=== Client data permissions ===\n" + command_output(proc)
        return proc.returncode, combined

    def openai_codex_profile_id(self, container: str) -> str:
        proc = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "python3",
                "-c",
                (
                    "import json;"
                    "p='/data/.openclaw/agents/main/agent/auth-profiles.json';"
                    "d=json.load(open(p));"
                    "profiles=d.get('profiles') or {};"
                    "ids=[k for k,v in profiles.items() if (v.get('provider') if isinstance(v,dict) else '')=='openai-codex' or k.startswith('openai-codex:')];"
                    "print(ids[0] if ids else '')"
                ),
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        return proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else ""

    def set_openai_codex_auth_order(self, slug: str) -> tuple[int, str]:
        container = self.find_container(slug)
        if not container:
            return 1, f"No running container found for {project_name(slug)}"

        profile_id = self.openai_codex_profile_id(container)
        if not profile_id:
            return 1, "No openai-codex OAuth profile found for this client."

        proc = subprocess.run(
            ["docker", "exec", container, "openclaw", "models", "auth", "order", "set", "--provider", "openai-codex", profile_id],
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        combined = "=== OpenAI Codex auth order ===\n" + command_output(proc)
        return proc.returncode, redact(combined, [profile_id])

    def approve_telegram_pairing(self, slug: str, pairing_code: str) -> tuple[int, str]:
        if not PAIRING_CODE_RE.match(pairing_code):
            raise RuntimeError("Telegram pairing code must be 4-40 letters/numbers/dashes/underscores.")

        container = self.find_container(slug)
        if not container:
            raise RuntimeError(f"No running container found for {project_name(slug)}")

        approve_proc = subprocess.run(
            ["docker", "exec", container, "openclaw", "pairing", "approve", "telegram", pairing_code],
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        combined = "=== Telegram pairing approve ===\n" + command_output(approve_proc)
        status_code = approve_proc.returncode

        if status_code == 0:
            order_code, order_output = self.set_openai_codex_auth_order(slug)
            combined += "\n\n" + order_output
            if order_code != 0:
                combined += "\nAuth order was not updated; continuing without restart."
            combined += "\nClient restart deferred until final wizard step."
            status_code = max(status_code, order_code)

        return status_code, redact(combined, [pairing_code])

    def install_oauth_helper(self, slug: str) -> None:
        helper_src = Path(self.server.oauth_helper)
        if not helper_src.exists():
            raise RuntimeError(f"OAuth helper not found: {helper_src}")

        data_dir = self.project_dir(slug) / "data"
        if not data_dir.exists():
            raise RuntimeError(f"OpenClaw data dir not found: {data_dir}")

        helper_dst = data_dir / "openclaw-codex-oauth-chat.sh"
        shutil.copyfile(helper_src, helper_dst)
        helper_dst.chmod(0o700)

    def stop_previous_oauth(self, state_dir: Path) -> None:
        for pid_file in (state_dir / "openai-codex-oauth.pid", state_dir / "openai-codex-device-code.pid"):
            if not pid_file.exists():
                continue
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
            except ValueError:
                pid_file.unlink(missing_ok=True)
                continue
            try:
                os.kill(pid, 0)
            except OSError:
                pid_file.unlink(missing_ok=True)
                continue
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                pass
            time.sleep(0.4)

    def start_oauth(self, slug: str) -> tuple[str, str]:
        self.install_oauth_helper(slug)
        container = self.find_container(slug)
        if not container:
            raise RuntimeError(f"No running container found for {project_name(slug)}")

        state_dir = self.state_dir(slug)
        state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.stop_previous_oauth(state_dir)

        log_path = state_dir / "openai-codex-oauth.log"
        status_path = state_dir / "openai-codex-oauth.status"
        pid_path = state_dir / "openai-codex-oauth.pid"
        for path in (log_path, status_path):
            path.unlink(missing_ok=True)

        cmd = (
            f"docker exec {shlex.quote(container)} bash /data/openclaw-codex-oauth-chat.sh start "
            f">{shlex.quote(str(log_path))} 2>&1; "
            f"printf '%s\\n' \"$?\" > {shlex.quote(str(status_path))}"
        )
        proc = subprocess.Popen(["bash", "-lc", cmd], start_new_session=True)
        pid_path.write_text(str(proc.pid) + "\n", encoding="utf-8")
        pid_path.chmod(0o600)

        output = ""
        for _ in range(90):
            if log_path.exists():
                output = log_path.read_text(encoding="utf-8", errors="replace")
                match = OAUTH_URL_RE.search(output)
                if match:
                    return match.group(0), output
            if status_path.exists():
                break
            time.sleep(0.5)

        if log_path.exists():
            output = log_path.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError("OAuth URL was not produced.\n\n" + output[-4000:])

    def start_device_code(self, slug: str) -> tuple[str, str, str]:
        self.install_oauth_helper(slug)
        container = self.find_container(slug)
        if not container:
            raise RuntimeError(f"No running container found for {project_name(slug)}")

        state_dir = self.state_dir(slug)
        state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.stop_previous_oauth(state_dir)

        log_path = state_dir / "openai-codex-device-code.log"
        status_path = state_dir / "openai-codex-device-code.status"
        pid_path = state_dir / "openai-codex-device-code.pid"
        for path in (log_path, status_path):
            path.unlink(missing_ok=True)

        cmd = (
            f"docker exec {shlex.quote(container)} bash /data/openclaw-codex-oauth-chat.sh device-code "
            f">{shlex.quote(str(log_path))} 2>&1; "
            f"printf '%s\\n' \"$?\" > {shlex.quote(str(status_path))}"
        )
        proc = subprocess.Popen(["bash", "-lc", cmd], start_new_session=True)
        pid_path.write_text(str(proc.pid) + "\n", encoding="utf-8")
        pid_path.chmod(0o600)

        output = ""
        auth_url = ""
        device_code = ""
        for _ in range(90):
            if log_path.exists():
                output = log_path.read_text(encoding="utf-8", errors="replace")
                auth_url, device_code = extract_device_auth(output)
                if auth_url and device_code:
                    return auth_url, device_code, output
                if status_path.exists():
                    break
            time.sleep(0.5)

        if log_path.exists():
            output = log_path.read_text(encoding="utf-8", errors="replace")
            auth_url, device_code = extract_device_auth(output)
        if auth_url and device_code:
            return auth_url, device_code, output
        if auth_url:
            raise RuntimeError("Device-code auth URL was produced, but the verification code was not found yet.\n\n" + output[-4000:])
        raise RuntimeError("Device-code auth URL was not produced.\n\n" + output[-4000:])

    def check_device_code(self, slug: str) -> tuple[int | None, str, str, str]:
        state_dir = self.state_dir(slug)
        log_path = state_dir / "openai-codex-device-code.log"
        status_path = state_dir / "openai-codex-device-code.status"
        output = ""
        if log_path.exists():
            output = log_path.read_text(encoding="utf-8", errors="replace")
        if not status_path.exists():
            auth_url, device_code = extract_device_auth(output)
            return None, output or "Device-code auth is still running.", auth_url, device_code

        raw_status = status_path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw_status.isdigit():
            auth_url, device_code = extract_device_auth(output)
            return 1, output + f"\nUnexpected device-code status: {raw_status}", auth_url, device_code

        status_code = int(raw_status)
        if status_code == 0:
            order_code, order_output = self.set_openai_codex_auth_order(slug)
            output += "\n\n" + order_output
            if order_code == 0:
                output += "\nClient restart deferred until final wizard step."
            auth_url, device_code = extract_device_auth(output)
            return max(status_code, order_code), output, auth_url, device_code
        auth_url, device_code = extract_device_auth(output)
        return status_code, output, auth_url, device_code

    def finish_oauth(self, slug: str, callback_url: str, run_smoke: bool) -> tuple[int, str]:
        if not CALLBACK_RE.match(callback_url):
            raise RuntimeError("Callback URL must start with http://localhost:<port>/auth/callback?...")

        self.install_oauth_helper(slug)
        container = self.find_container(slug)
        if not container:
            raise RuntimeError(f"No running container found for {project_name(slug)}")

        finish_proc = subprocess.run(
            ["docker", "exec", container, "bash", "/data/openclaw-codex-oauth-chat.sh", "finish", callback_url],
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        combined = command_output(finish_proc)

        state_dir = self.state_dir(slug)
        status_path = state_dir / "openai-codex-oauth.status"
        log_path = state_dir / "openai-codex-oauth.log"
        for _ in range(120):
            if status_path.exists():
                break
            time.sleep(0.5)

        if log_path.exists():
            combined += "\n\n=== OAuth start log tail ===\n" + log_path.read_text(encoding="utf-8", errors="replace")[-4000:]

        status_code = finish_proc.returncode
        if status_path.exists():
            raw_status = status_path.read_text(encoding="utf-8", errors="replace").strip()
            combined += f"\n\nOAuth start exit code: {raw_status}"
            if raw_status.isdigit():
                start_status_code = int(raw_status)
                if start_status_code != 0:
                    # OpenClaw may keep the interactive OAuth command alive after
                    # the callback has already saved the profile. Recreating the
                    # client can then kill that lingering process. Treat it as a
                    # warning when the profile is present.
                    if finish_proc.returncode == 0 and self.openai_codex_profile_id(container):
                        combined += (
                            "\nOAuth start returned a non-zero code after the auth profile was saved; "
                            "continuing because OAuth completion is confirmed."
                        )
                    else:
                        status_code = max(status_code, start_status_code)
        else:
            combined += "\n\nOAuth start process has not exited yet."

        if status_code == 0:
            order_code, order_output = self.set_openai_codex_auth_order(slug)
            combined += "\n\n" + order_output
            status_code = max(status_code, order_code)

        if status_code == 0:
            combined += "\nClient restart deferred until final wizard step."
            if run_smoke:
                combined += "\nSmoke check deferred until the final restart."

        return status_code, redact(combined, [callback_url])

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        token = params.get("token", [""])[0]
        if not self.valid_token(token):
            self.send_html(b"Forbidden", status=403)
            return
        self.send_html(html_page(self.server.admin_token))

    def form_fields(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/create":
            self.handle_create()
            return
        if parsed.path == "/oauth-finish":
            self.handle_oauth_finish()
            return
        if parsed.path == "/device-check":
            self.handle_device_check()
            return
        if parsed.path == "/telegram-approve":
            self.handle_telegram_approve()
            return
        if parsed.path == "/env-save":
            self.handle_env_save()
            return
        self.send_html(b"Not found", status=404)

    def handle_env_save(self) -> None:
        fields = self.form_fields()
        if not self.valid_token(fields.get("token")):
            self.send_html(b"Forbidden", status=403)
            return

        slug = slugify(fields.get("slug", ""))
        smoke = fields.get("smoke") == "1"
        if not SLUG_RE.match(slug):
            self.send_html(html_page(self.server.admin_token, "שם לקוח לא תקין.", step="create"))
            return

        if fields.get("skip_env") == "1":
            code, output = self.finalize_client(slug, smoke)
            if code != 0:
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"לקוח `{slug}` נשמר, אבל האתחול הסופי נכשל עם exit code {code}",
                        output,
                        step="env",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    ),
                    status=500,
                )
                return
            self.send_html(
                html_page(
                    self.server.admin_token,
                    f"לקוח `{slug}` הושלם ללא מפתחות ENV נוספים.",
                    output,
                    step="complete",
                    slug=slug,
                    public_url=self.client_public_url(slug),
                )
            )
            self.schedule_cleanup(slug)
            return

        meta_api_token = fields.get("meta_api_token", "").strip()
        extra_env = fields.get("extra_env", "")
        try:
            updates = parse_extra_env(extra_env)
            if meta_api_token:
                if not validate_no_newline(meta_api_token):
                    raise ValueError("Meta API Token cannot contain newlines.")
                updates["META_API_TOKEN"] = meta_api_token
            if not updates:
                code, output = self.finalize_client(slug, smoke)
                if code != 0:
                    self.send_html(
                        html_page(
                            self.server.admin_token,
                            f"לקוח `{slug}` נשמר, אבל האתחול הסופי נכשל עם exit code {code}",
                            output,
                            step="env",
                            slug=slug,
                            public_url=self.client_public_url(slug),
                        ),
                        status=500,
                    )
                    return
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"לקוח `{slug}` הושלם ללא מפתחות ENV נוספים.",
                        output,
                        step="complete",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    )
                )
                self.schedule_cleanup(slug)
                return

            code, output = self.upsert_client_env(slug, updates)
            if code == 0:
                final_code, final_output = self.finalize_client(slug, smoke)
                output += "\n\n" + final_output
                if final_code != 0:
                    self.send_html(
                        html_page(
                            self.server.admin_token,
                            f"מפתחות ENV עבור `{slug}` נשמרו, אבל האתחול הסופי נכשל עם exit code {final_code}",
                            output,
                            step="env",
                            slug=slug,
                            public_url=self.client_public_url(slug),
                        ),
                        status=500,
                    )
                    return
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"מפתחות ENV עבור `{slug}` נשמרו.",
                        output,
                        step="complete",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    )
                )
                self.schedule_cleanup(slug)
                return
            self.send_html(
                html_page(
                    self.server.admin_token,
                    f"מפתחות ENV עבור `{slug}` נשמרו, אבל אתחול הקונטיינר נכשל עם exit code {code}",
                    output,
                    step="env",
                    slug=slug,
                    public_url=self.client_public_url(slug),
                ),
                status=500,
            )
        except Exception as exc:
            self.send_html(
                html_page(
                    self.server.admin_token,
                    "שמירת מפתחות ENV נכשלה.",
                    redact(str(exc), [meta_api_token]),
                    step="env",
                    slug=slug,
                    public_url=self.client_public_url(slug),
                ),
                status=400,
            )

    def handle_telegram_approve(self) -> None:
        fields = self.form_fields()
        if not self.valid_token(fields.get("token")):
            self.send_html(b"Forbidden", status=403)
            return

        slug = slugify(fields.get("slug", ""))
        pairing_code = fields.get("pairing_code", "").strip()
        if not SLUG_RE.match(slug):
            self.send_html(html_page(self.server.admin_token, "שם לקוח לא תקין.", step="create"))
            return
        if not pairing_code or not validate_no_newline(pairing_code):
            self.send_html(html_page(self.server.admin_token, "קוד pairing לא תקין.", step="telegram", slug=slug, public_url=self.client_public_url(slug)))
            return

        try:
            code, output = self.approve_telegram_pairing(slug, pairing_code)
            if code == 0:
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"Telegram pairing עבור `{slug}` הצליח. עכשיו אפשר להוסיף מפתחות ENV ללקוח.",
                        output,
                        step="env",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    )
                )
                return
            self.send_html(
                html_page(
                    self.server.admin_token,
                    f"Telegram pairing עבור `{slug}` נכשל עם exit code {code}",
                    output,
                    step="telegram",
                    slug=slug,
                    public_url=self.client_public_url(slug),
                )
            )
        except Exception as exc:
            self.send_html(
                html_page(
                    self.server.admin_token,
                    "Telegram pairing נכשל.",
                    redact(str(exc), [pairing_code]),
                    step="telegram",
                    slug=slug,
                    public_url=self.client_public_url(slug),
                ),
                status=500,
            )

    def handle_oauth_finish(self) -> None:
        fields = self.form_fields()
        if not self.valid_token(fields.get("token")):
            self.send_html(b"Forbidden", status=403)
            return

        slug = slugify(fields.get("slug", ""))
        callback_url = fields.get("callback_url", "").strip()
        smoke = fields.get("smoke") == "1"
        if not SLUG_RE.match(slug):
            self.send_html(html_page(self.server.admin_token, "שם לקוח לא תקין.", step="create"))
            return

        try:
            code, output = self.finish_oauth(slug, callback_url, smoke)
            if code == 0:
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"חיבור OAuth עבור `{slug}` הצליח. עכשיו אשר את ה־Telegram pairing.",
                        output,
                        step="telegram",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    )
                )
                return
            self.send_html(
                html_page(
                    self.server.admin_token,
                    f"חיבור OAuth עבור `{slug}` נכשל עם exit code {code}",
                    output,
                    step="oauth" if self.state_dir(slug).exists() else "create",
                    slug=slug,
                    oauth_slug=slug,
                    public_url=self.client_public_url(slug),
                )
            )
        except Exception as exc:
            self.send_html(
                html_page(
                    self.server.admin_token,
                    "חיבור OAuth נכשל.",
                    redact(str(exc), [callback_url]),
                    step="create",
                    slug=slug,
                    public_url=self.client_public_url(slug),
                ),
                status=500,
            )

    def handle_device_check(self) -> None:
        fields = self.form_fields()
        if not self.valid_token(fields.get("token")):
            self.send_html(b"Forbidden", status=403)
            return

        slug = slugify(fields.get("slug", ""))
        if not SLUG_RE.match(slug):
            self.send_html(html_page(self.server.admin_token, "שם לקוח לא תקין.", step="create"))
            return

        try:
            code, output, auth_url, device_code = self.check_device_code(slug)
            if code is None:
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"חיבור Device Code עבור `{slug}` עדיין ממתין לאישור.",
                        step="device",
                        oauth_slug=slug,
                        oauth_url=auth_url,
                        device_code=device_code,
                        public_url=self.client_public_url(slug),
                    )
                )
                return
            if code == 0:
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"חיבור OpenAI עבור `{slug}` הצליח. עכשיו אשר את ה־Telegram pairing.",
                        output,
                        step="telegram",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    )
                )
                return
            self.send_html(
                html_page(
                    self.server.admin_token,
                    f"חיבור Device Code עבור `{slug}` נכשל עם exit code {code}",
                    step="device",
                    oauth_slug=slug,
                    oauth_url=auth_url,
                    device_code=device_code,
                    public_url=self.client_public_url(slug),
                ),
                status=500,
            )
        except Exception as exc:
            self.send_html(
                html_page(
                    self.server.admin_token,
                    "בדיקת Device Code נכשלה.",
                    str(exc),
                    step="device",
                    oauth_slug=slug,
                    public_url=self.client_public_url(slug),
                ),
                status=500,
            )

    def handle_create(self) -> None:
        fields = self.form_fields()
        if not self.valid_token(fields.get("token")):
            self.send_html(b"Forbidden", status=403)
            return

        client_name = fields.get("client_name", "")
        slug = slugify(client_name)
        auth_method = fields.get("auth_method", "oauth")
        openai_api_key = fields.get("openai_api_key", "").strip()
        telegram_bot_token = fields.get("telegram_bot_token", "").strip()
        start = fields.get("start") == "1"
        smoke = fields.get("smoke") == "1"
        dry_run = fields.get("dry_run") == "1"

        if not SLUG_RE.match(slug):
            self.send_html(html_page(self.server.admin_token, "שם הלקוח לא תקין אחרי ניקוי. השתמש באנגלית/מספרים/מקפים.", step="create"))
            return
        if auth_method not in {"oauth", "device_code", "api_key"}:
            self.send_html(html_page(self.server.admin_token, "שיטת חיבור מודל לא תקינה.", step="create"))
            return
        if not telegram_bot_token:
            self.send_html(html_page(self.server.admin_token, "חסר Telegram bot token.", step="create"))
            return
        if auth_method == "api_key" and not openai_api_key:
            self.send_html(html_page(self.server.admin_token, "חסר OpenAI API key.", step="create"))
            return
        if not validate_no_newline(openai_api_key, telegram_bot_token):
            self.send_html(html_page(self.server.admin_token, "המפתחות לא יכולים לכלול ירידת שורה.", step="create"))
            return
        if auth_method in {"oauth", "device_code"} and not start and not dry_run:
            self.send_html(html_page(self.server.admin_token, "חיבור OpenAI דורש להפעיל את הקונטיינר כדי להריץ auth בתוך הלקוח.", step="create"))
            return

        temp_dir = Path(tempfile.mkdtemp(prefix="openclaw-client-env-"))
        env_path = temp_dir / f"{slug}.env"
        sensitive_values = [openai_api_key, telegram_bot_token]
        try:
            env_lines = [f"TELEGRAM_BOT_TOKEN={telegram_bot_token}"]
            if auth_method == "api_key":
                env_lines.insert(0, f"OPENAI_API_KEY={openai_api_key}")
            env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
            env_path.chmod(0o600)

            cmd = [
                self.server.provision_cmd,
                "--slug",
                slug,
                "--client-env",
                str(env_path),
            ]
            if dry_run:
                cmd.append("--dry-run")
            else:
                cmd.extend(["--apply", "--backup-now"])
                if start:
                    cmd.append("--start")
                    if smoke and auth_method == "api_key":
                        cmd.append("--smoke")

            proc = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=self.server.timeout,
                check=False,
            )
            combined = redact(command_output(proc), sensitive_values)
            if proc.returncode != 0:
                self.send_html(html_page(self.server.admin_token, f"לקוח `{slug}`: נכשל עם exit code {proc.returncode}", combined, step="create", slug=slug))
                return

            if auth_method == "oauth" and not dry_run:
                try:
                    oauth_url, oauth_output = self.start_oauth(slug)
                    combined += "\n\n=== OAuth start ===\n" + oauth_output
                    self.send_html(
                        html_page(
                            self.server.admin_token,
                            f"לקוח `{slug}` נוצר. פתח את לינק ה־OAuth ואז הדבק את ה־callback.",
                            combined,
                            step="oauth",
                            slug=slug,
                            oauth_slug=slug,
                            oauth_url=oauth_url,
                            public_url=self.client_public_url(slug),
                        )
                    )
                    return
                except Exception as exc:
                    combined += "\n\n=== OAuth start failed ===\n" + redact(str(exc), sensitive_values)
                    self.send_html(html_page(self.server.admin_token, f"לקוח `{slug}` נוצר, אבל התחלת OAuth נכשלה.", combined, step="create", slug=slug), status=500)
                    return

            if auth_method == "device_code" and not dry_run:
                try:
                    device_url, device_code, device_output = self.start_device_code(slug)
                    combined += "\n\n=== Device-code auth start ===\n" + device_output
                    self.send_html(
                        html_page(
                            self.server.admin_token,
                            f"לקוח `{slug}` נוצר. השלם את חיבור OpenAI עם Device Code.",
                            step="device",
                            slug=slug,
                            oauth_slug=slug,
                            oauth_url=device_url,
                            device_code=device_code,
                            public_url=self.client_public_url(slug),
                        )
                    )
                    return
                except Exception as exc:
                    combined += "\n\n=== Device-code auth start failed ===\n" + redact(str(exc), sensitive_values)
                    self.send_html(html_page(self.server.admin_token, f"לקוח `{slug}` נוצר, אבל התחלת Device Code נכשלה.", combined, step="create", slug=slug), status=500)
                    return

            status = "הצליח" if proc.returncode == 0 else f"נכשל עם exit code {proc.returncode}"
            if auth_method == "api_key" and not dry_run:
                self.send_html(
                    html_page(
                        self.server.admin_token,
                        f"לקוח `{slug}` נוצר עם API key. עכשיו אשר את ה־Telegram pairing.",
                        combined,
                        step="telegram",
                        slug=slug,
                        public_url=self.client_public_url(slug),
                    )
                )
            else:
                self.send_html(html_page(self.server.admin_token, f"לקוח `{slug}`: {status}", combined, step="complete" if not dry_run else "create", slug=slug, public_url=self.client_public_url(slug)))
        except subprocess.TimeoutExpired as exc:
            combined = redact((exc.stdout or "") + "\n" + (exc.stderr or ""), sensitive_values)
            self.send_html(html_page(self.server.admin_token, "הפעולה נתקעה ועברה timeout.", combined, step="create", slug=slug), status=500)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class ProvisionServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler,
        admin_token: str,
        provision_cmd: str,
        docker_root: str,
        oauth_helper: str,
        cleanup_command: str,
        timeout: int,
    ):
        super().__init__(server_address, handler)
        self.admin_token = admin_token
        self.provision_cmd = provision_cmd
        self.docker_root = docker_root
        self.oauth_helper = oauth_helper
        self.cleanup_command = cleanup_command
        self.timeout = timeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Local admin form for Hostinger OpenClaw client provisioning")
    parser.add_argument("--bind", default=DEFAULT_BIND)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--token-file", default=DEFAULT_TOKEN_FILE)
    parser.add_argument("--provision-cmd", default=DEFAULT_PROVISION_CMD)
    parser.add_argument("--docker-root", default=DEFAULT_DOCKER_ROOT)
    parser.add_argument("--oauth-helper", default=DEFAULT_OAUTH_HELPER)
    parser.add_argument("--cleanup-command", default=DEFAULT_CLEANUP_COMMAND)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    token_file = Path(args.token_file)
    token = load_or_create_token(token_file)
    provision_cmd = shutil.which(args.provision_cmd) or args.provision_cmd
    if not Path(provision_cmd).exists() and not shutil.which(provision_cmd):
        raise SystemExit(f"Provision command not found: {args.provision_cmd}")

    server = ProvisionServer(
        (args.bind, args.port),
        ProvisionHandler,
        token,
        provision_cmd,
        args.docker_root,
        args.oauth_helper,
        args.cleanup_command,
        args.timeout,
    )
    print(f"Listening on http://{args.bind}:{args.port}/?token={token}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
