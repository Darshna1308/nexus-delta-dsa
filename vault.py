"""ENCRYPTION + SECURE STORE for NEXUS DELTA (offline, local SQLite, no remote service).

Layers
  L1  Passwords ........ scrypt (n=2^14, r=8, p=1) + per-user 16-byte salt; constant-time compare; lockout after 5 failures.
  L2  Records at rest .. AES-256-GCM, fresh 96-bit nonce per record, AAD binds ciphertext to (table, org) so rows cannot be swapped.
  L3  Master key ....... NEXUS_VAULT_KEY (base64, 32 bytes) or an auto-generated 0600 key file. Never stored in the database.
  L4  Private reports .. a user's saved EQ report is encrypted with a key derived from THEIR password (scrypt→HKDF); the operator cannot read it.
  L5  Invite codes ..... stored only as HMAC-SHA256; single-use.
  L6  Anonymity ........ culture responses carry NO user reference (only org + cycle); org aggregates are released only when n >= K_MIN.
Transport (TLS) is provided by the hosting layer (Streamlit Cloud / reverse proxy) — stated, not implemented here.
"""
import os, json, base64, hmac, hashlib, secrets, sqlite3, time, stat
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

K_MIN = 5            # minimum responses before any organisation aggregate is shown (k-anonymity)
MAX_FAILS, LOCK_S = 5, 300


def vdir() -> Path:
    p = Path(os.environ.get("NEXUS_VAULT_DIR", Path(__file__).parent / "vault")); p.mkdir(parents=True, exist_ok=True); return p


def master_key() -> bytes:
    env = os.environ.get("NEXUS_VAULT_KEY")
    if env:
        k = base64.b64decode(env)
        if len(k) != 32: raise ValueError("NEXUS_VAULT_KEY must be 32 bytes, base64-encoded")
        return k
    f = vdir() / "master.key"
    if not f.exists():
        f.write_bytes(base64.b64encode(secrets.token_bytes(32))); os.chmod(f, stat.S_IRUSR | stat.S_IWUSR)
    return base64.b64decode(f.read_bytes())


def _sub(label: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=label).derive(master_key())


def encrypt(obj, aad: str, key: bytes = None) -> bytes:
    key = key or _sub(b"records-v1"); n = secrets.token_bytes(12)
    return b"\x01" + n + AESGCM(key).encrypt(n, json.dumps(obj, separators=(",", ":")).encode(), aad.encode())


def decrypt(blob: bytes, aad: str, key: bytes = None):
    key = key or _sub(b"records-v1")
    if blob[:1] != b"\x01": raise ValueError("unknown blob version")
    return json.loads(AESGCM(key).decrypt(blob[1:13], blob[13:], aad.encode()))


def hash_password(pw: str, salt: bytes = None):
    salt = salt or secrets.token_bytes(16)
    return salt, hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)


def user_key(pw: str, salt: bytes) -> bytes:
    """L4: key for the user's private data; derived from the password with a SEPARATE salt, so it is not recoverable from the stored hash."""
    raw = hashlib.scrypt(pw.encode(), salt=b"uk" + salt, n=2 ** 14, r=8, p=1, dklen=32)
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"user-private-v1").derive(raw)


def code_hash(code: str) -> str: return hmac.new(_sub(b"invite-v1"), code.strip().upper().encode(), hashlib.sha256).hexdigest()


def db() -> sqlite3.Connection:
    c = sqlite3.connect(vdir() / "nexus_secure.db"); c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS orgs(id INTEGER PRIMARY KEY, name TEXT UNIQUE, published INTEGER DEFAULT 0, simulated INTEGER DEFAULT 0, created REAL);
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, role TEXT, org_id INTEGER, salt BLOB, pwhash BLOB, fails INTEGER DEFAULT 0, locked_until REAL DEFAULT 0, submitted_cycle TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS invites(id INTEGER PRIMARY KEY, org_id INTEGER, code_hash TEXT UNIQUE, used INTEGER DEFAULT 0, created REAL);
    CREATE TABLE IF NOT EXISTS culture_responses(id INTEGER PRIMARY KEY, org_id INTEGER, cycle TEXT, blob BLOB);
    CREATE TABLE IF NOT EXISTS private_reports(id INTEGER PRIMARY KEY, user_id INTEGER, kind TEXT, blob BLOB, created REAL);
    """)
    return c
