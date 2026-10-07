"""ACCOUNTS — roles: CANDIDATE (student/professional), EMPLOYEE (joins an organisation with a single-use invite code), ORG (organisation admin). Guests need no account.
Anonymous by design: employee culture responses are stored without any user id (vault.culture_responses)."""
import re, time, secrets, sqlite3
import vault

ROLES = ("CANDIDATE", "EMPLOYEE", "ORG")
_U = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def _ok_pw(pw):
    if len(pw or "") < 8: return "Password must be at least 8 characters."
    if pw.lower() == pw or not any(c.isdigit() for c in pw): return "Use upper- and lower-case letters and at least one digit."
    return None


def register(username, pw, role, org_name=None, invite=None):
    username = (username or "").strip()
    if not _U.match(username): return None, "Username: 3–32 letters, digits, . _ -"
    if role not in ROLES: return None, "Unknown account type."
    e = _ok_pw(pw)
    if e: return None, e
    con = vault.db()
    try:
        org_id = None
        if role == "ORG":
            org_name = (org_name or "").strip()
            if len(org_name) < 2: return None, "Enter your organisation name."
            try: org_id = con.execute("INSERT INTO orgs(name,created) VALUES(?,?)", (org_name, time.time())).lastrowid
            except sqlite3.IntegrityError: return None, "That organisation is already registered."
        elif role == "EMPLOYEE":
            row = con.execute("SELECT id,org_id FROM invites WHERE code_hash=? AND used=0", (vault.code_hash(invite or ""),)).fetchone()
            if not row: return None, "Invalid or already-used invite code. Ask your organisation for a new one."
            org_id = row["org_id"]
        salt, h = vault.hash_password(pw)
        try: uid = con.execute("INSERT INTO users(username,role,org_id,salt,pwhash,created) VALUES(?,?,?,?,?,?)", (username, role, org_id, salt, h, time.time())).lastrowid
        except sqlite3.IntegrityError: return None, "That username is taken."
        if role == "EMPLOYEE": con.execute("UPDATE invites SET used=1 WHERE id=?", (row["id"],))
        con.commit()
        return dict(id=uid, username=username, role=role, org_id=org_id), None
    finally: con.close()


def login(username, pw):
    con = vault.db()
    try:
        u = con.execute("SELECT * FROM users WHERE username=?", ((username or "").strip(),)).fetchone()
        if not u:
            vault.hash_password(pw or "x")   # equalise timing
            return None, "Wrong username or password."
        if u["locked_until"] > time.time(): return None, f"Too many attempts. Try again in {int(u['locked_until'] - time.time()) // 60 + 1} min."
        _, h = vault.hash_password(pw or "", u["salt"])
        if not secrets.compare_digest(h, u["pwhash"]):
            f = u["fails"] + 1; lock = time.time() + vault.LOCK_S if f >= vault.MAX_FAILS else 0
            con.execute("UPDATE users SET fails=?, locked_until=? WHERE id=?", (0 if lock else f, lock, u["id"])); con.commit()
            return None, "Wrong username or password."
        con.execute("UPDATE users SET fails=0, locked_until=0 WHERE id=?", (u["id"],)); con.commit()
        org = con.execute("SELECT name,published,simulated FROM orgs WHERE id=?", (u["org_id"],)).fetchone() if u["org_id"] else None
        return dict(id=u["id"], username=u["username"], role=u["role"], org_id=u["org_id"], org=org["name"] if org else None,
                    org_simulated=bool(org and org["simulated"]), ukey=vault.user_key(pw, u["salt"])), None
    finally: con.close()


def new_invite(org_id):
    code = "-".join(secrets.token_hex(2).upper() for _ in range(3)); con = vault.db()
    try: con.execute("INSERT INTO invites(org_id,code_hash,created) VALUES(?,?,?)", (org_id, vault.code_hash(code), time.time())); con.commit()
    finally: con.close()
    return code


def invite_stats(org_id):
    con = vault.db()
    try: r = con.execute("SELECT COUNT(*) n, COALESCE(SUM(used),0) u FROM invites WHERE org_id=?", (org_id,)).fetchone(); return dict(issued=r["n"], redeemed=r["u"])
    finally: con.close()


def save_private(user, kind, obj):
    con = vault.db()
    try:
        con.execute("DELETE FROM private_reports WHERE user_id=? AND kind=?", (user["id"], kind))
        con.execute("INSERT INTO private_reports(user_id,kind,blob,created) VALUES(?,?,?,?)", (user["id"], kind, vault.encrypt(obj, f"private:{user['id']}:{kind}", user["ukey"]), time.time())); con.commit()
    finally: con.close()


def load_private(user, kind):
    con = vault.db()
    try:
        r = con.execute("SELECT blob FROM private_reports WHERE user_id=? AND kind=?", (user["id"], kind)).fetchone()
        return vault.decrypt(r["blob"], f"private:{user['id']}:{kind}", user["ukey"]) if r else None
    finally: con.close()


def delete_private(user, kind=None):
    con = vault.db()
    try: con.execute("DELETE FROM private_reports WHERE user_id=?" + (" AND kind=?" if kind else ""), (user["id"], kind) if kind else (user["id"],)); con.commit()
    finally: con.close()
