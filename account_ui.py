"""Login gate, account bar and the CULTURE page (employee rating + organisation scorecard + candidate browse)."""
import streamlit as st
import ui, auth, vault, culture as CU, work_dna as W, charts
from config import C
S = st.session_state

ROLE_NAME = {"CANDIDATE": "Candidate", "EMPLOYEE": "Employee", "ORG": "Organisation admin", "GUEST": "Guest"}
SEC_LAYERS = [("Passwords", "scrypt + per-user salt; 5 failed attempts lock the account for 5 minutes.", "teal"),
              ("Data at rest", "AES-256-GCM per record, fresh nonce, row bound to its organisation (AAD).", "teal"),
              ("Master key", "Held outside the database: NEXUS_VAULT_KEY or a 0600 key file.", "teal"),
              ("Private reports", "A saved EQ report is encrypted with a key derived from your password — the operator cannot read it.", "teal"),
              ("Anonymity", "Culture answers are stored with no user id; organisations see nothing until 5 responses exist (k-anonymity).", "teal"),
              ("Invite codes", "Single-use, stored only as HMAC. Employees are verified by the organisation that invited them.", "teal"),
              ("Transport", "TLS comes from the host (Streamlit Cloud / reverse proxy) — not implemented in the app.", "amber")]


def _bars(v, w=10): n = int(round(v * w / 5)); return "█" * n + "░" * (w - n)
def user(): return S.get("user")
def role(): return (S.user["role"] if S.get("user") else "GUEST")
def logged_in(): return bool(S.get("user")) or bool(S.get("guest"))


def logout(): [S.pop(k, None) for k in ("user", "guest")]; S.update(page="HOME")


def login_page():
    ui.md("<div style='height:8px'></div>")
    with st.container(key="body"):
        L, R = st.columns([1.15, 1], gap="large")
        with L:
            ui.hero("NEXUS DELTA · SIGN IN", "Know what to build.<br>Know what to learn.<br>Know where you can thrive.", "Evidence-first capability intelligence — with an <b>encrypted, anonymous</b> way for employees to rate their own workplace.")
            ui.md("".join(f"<div style='margin:5px 0;font-size:12.5px'>{ui.chip(t, c)} &nbsp;{ui.esc(d)}</div>" for t, d, c in SEC_LAYERS[:6]))
        with R, st.container(key="card_login"):
            tab = st.segmented_control("Mode", ["SIGN IN", "CREATE ACCOUNT", "GUEST"], key="auth_tab", default="SIGN IN", required=True, label_visibility="collapsed", width="stretch")
            if tab == "SIGN IN":
                f = st.form("f_login", border=False, clear_on_submit=False)
                with f:
                    st.text_input("Username", key="li_user"); st.text_input("Password", type="password", key="li_pw")
                def do():
                    u, e = auth.login(S.li_user, S.li_pw); S.auth_msg = e
                    if u: S.user = u; S.pop("guest", None); S.page = "HOME"
                with f: st.form_submit_button("SIGN IN ›", key="li_go", type="primary", on_click=do, width="stretch")
                ui.md("<div class='nd-sub'>Demo accounts (SIMULATED data): <b>demo_candidate</b>, <b>demo_employee</b>, <b>demo_org</b> — password <b>Demo#2026pw</b> (run <code>python seed_demo.py</code> once).</div>")
            elif tab == "CREATE ACCOUNT":
                kind = st.segmented_control("I am a", ["CANDIDATE", "EMPLOYEE", "ORG"], key="su_role", default="CANDIDATE", required=True, format_func=lambda x: {"CANDIDATE": "Candidate", "EMPLOYEE": "Employee", "ORG": "Organisation"}[x], width="stretch")
                f = st.form("f_signup", border=False)
                with f:
                    st.text_input("Username", key="su_user"); st.text_input("Password (8+ chars, mixed case, a digit)", type="password", key="su_pw")
                    if kind == "EMPLOYEE": st.text_input("Invite code from your organisation", key="su_code", placeholder="XXXX-XXXX-XXXX")
                    if kind == "ORG": st.text_input("Organisation name", key="su_org")
                def do():
                    u, e = auth.register(S.su_user, S.su_pw, S.su_role, org_name=S.get("su_org"), invite=S.get("su_code")); S.auth_msg = e
                    if u:
                        u2, e2 = auth.login(S.su_user, S.su_pw); S.auth_msg = e2
                        if u2: S.user = u2; S.pop("guest", None); S.page = "HOME"
                with f: st.form_submit_button("CREATE ACCOUNT ›", key="su_go", type="primary", on_click=do, width="stretch")
                ui.md("<div class='nd-sub'>Employees join only with a single-use invite code issued by their organisation — that is how “people who are hired” are verified.</div>")
            else:
                ui.md("<div class='nd-sub' style='margin:6px 0 10px 0'>Use every analysis screen without an account. Nothing is saved. Culture ratings of organisations are visible; submitting one needs an Employee account.</div>")
                st.button("CONTINUE AS GUEST ›", key="guest_go", type="primary", on_click=lambda: S.update(guest=True, page="HOME"), width="stretch")
            if S.get("auth_msg"): ui.err(S.auth_msg)
        ui.footer()


def account_chip():
    """small line in the top-right corner."""
    if S.get("user"): return f"{ui.esc(S.user['username'])} · {ROLE_NAME[S.user['role']]}" + (f" · {ui.esc(S.user['org'][:14])}" if S.user.get("org") else "")
    return "Guest session"


def _scale(txt, key, lo, hi):
    c = st.columns([3, 2.2], vertical_alignment="center")
    c[0].markdown(f"<div style='font-size:13px'>{ui.esc(txt)}<div class='nd-sub'>1 — {ui.esc(lo)} · 5 — {ui.esc(hi)}</div></div>", unsafe_allow_html=True)
    with c[1]: st.segmented_control(txt, [1, 2, 3, 4, 5], key=key, label_visibility="collapsed")


def _scorecard(agg, name, simulated, key):
    badge = ui.chip("SIMULATED DEMO ORGANISATION", "grey") if simulated else ""
    ui.md(f"<div style='margin:4px 0 8px 0'>{ui.chip('SELF-REPORTED', 'blue')} {badge} <span class='nd-sub'>{CU.STATUS}</span></div>")
    c = st.columns(3)
    with c[0]: ui.stat("CULTURE RATING", f"{agg['rating']}<span style='font-size:16px'>/100</span>", f"mean of 6 health items · n = {agg['n']} · {agg['cycle']}")
    with c[1]: ui.stat("BEST-RATED", ", ".join(f"{k}" for k, _ in sorted([(CU.HEALTH_LABEL[d], agg['items'][d]['mean']) for d, *_ in CU.HEALTH], key=lambda x: -x[1])[:2]), small=True)
    with c[2]:
        low, hi = CU.discussion_areas(agg, 2); ui.stat("DISCUSSION AREAS", ", ".join(k for k, _ in low), "lowest-rated — questions to ask, not a verdict", small=True)
    ui.md("<div class='nd-label' style='margin-top:10px'>CULTURE HEALTH (mean · 95% CI · 1–5, higher is better)</div>" + "<table class='nd-tbl'><tr><th>Item</th><th>Mean</th><th>95% CI</th><th></th></tr>" + "".join(
        f"<tr><td>{ui.esc(CU.HEALTH_LABEL[d])}</td><td>{agg['items'][d]['mean']:.2f}</td><td>[{agg['items'][d]['lo']:.2f}, {agg['items'][d]['hi']:.2f}]</td><td style='font-family:monospace'>{_bars(agg['items'][d]['mean'])}</td></tr>" for d, *_ in CU.HEALTH) + "</table>")
    ui.md("<div class='nd-label' style='margin-top:10px'>HOW THE WORK ACTUALLY IS (reported Work DNA of the job)</div>" + "<table class='nd-tbl'><tr><th>Dimension</th><th>Mean</th><th>95% CI</th></tr>" + "".join(
        f"<tr><td>{ui.esc(W.ROLE_DIM_LABEL[d])}</td><td>{agg['items'][d]['mean']:.2f}</td><td>[{agg['items'][d]['lo']:.2f}, {agg['items'][d]['hi']:.2f}]</td></tr>" for d in CU.JOB_DIMS) + "</table>")


def page_culture(b, go):
    r = role()
    with st.container(key="body"):
        ui.header("How does it actually feel to work there?", "Rated anonymously by verified employees. Compared with your Work DNA — never used to rate or screen individuals.", "CULTURE · EMPLOYEE-REPORTED · PROPOSED INSTRUMENT")
        if r == "EMPLOYEE": _employee(go)
        elif r == "ORG": _org(go)
        else: _browse(go)
        with st.expander("HOW THIS IS PROTECTED"):
            ui.md("".join(f"<div style='margin:5px 0;font-size:12.5px'>{ui.chip(t, c)} &nbsp;{ui.esc(d)}</div>" for t, d, c in SEC_LAYERS))
            ui.md("<div class='nd-note'><b>Limits, stated honestly:</b> an organisation could issue invite codes to non-employees (so the response rate = redeemed codes / responses is shown); a small team can still be guessable even above n = 5; responses cannot be edited because they are unlinkable by design; the instrument is not validated; the local SQLite store is a prototype of a managed database.</div>")
        ui.footer()


def _browse(go):
    pubs = CU.published_orgs()
    if not pubs: ui.note("No organisation has published a culture scorecard yet (a scorecard appears only after 5 verified employees respond and the organisation opts in)."); return
    names = [p["name"] for p in pubs]; sel = st.segmented_control("Organisation", names, key="cu_org", default=names[0], required=True, label_visibility="collapsed")
    p = next(x for x in pubs if x["name"] == sel); _scorecard(p["agg"], p["name"], p["simulated"], "br")
    st.button("COMPARE THIS CULTURE WITH MY WORK DNA ›", key="cu_cmp", type="primary", on_click=go, args=("WORK DNA",), kwargs=dict(dna_role=f"{p['name']} · employee-reported", dna_tab="YOUR FIT"))


def _org(go):
    u = S.user; oid = u["org_id"]; n = CU.count(oid); st_ = auth.invite_stats(oid)
    c = st.columns(4)
    with c[0]: ui.stat("RESPONSES THIS CYCLE", f"{n}", f"{CU.cycle()} · need {CU.K_MIN} to unlock")
    with c[1]: ui.stat("INVITES ISSUED", f"{st_['issued']}", f"{st_['redeemed']} redeemed")
    with c[2]: ui.stat("RESPONSE RATE", f"{(100 * n / st_['redeemed']):.0f}%" if st_["redeemed"] else "—", "responses / redeemed invites (shown to candidates)")
    with c[3]: ui.stat("PUBLISHED", "YES" if CU.is_published(oid) else "NO", "opt-in only")
    with st.container(key="card_org_inv"):
        ui.md("<div class='nd-label'>INVITE EMPLOYEES</div><div class='nd-sub'>Each code works once and is stored only as an HMAC. Share it with a person you actually employ.</div>")
        st.button("GENERATE INVITE CODE", key="inv_new", on_click=lambda: S.update(last_code=auth.new_invite(oid)))
        if S.get("last_code"): ui.md(f"<div class='nd-val s' style='font-family:monospace;letter-spacing:.1em'>{S.last_code}</div><div class='nd-sub'>Shown once — copy it now.</div>")
    agg = CU.aggregate(oid)
    if agg["suppressed"]:
        ui.md(f"<div class='nd-warn'><b>PRIVACY GATE.</b> {agg['n']} of {agg['need']} responses. Nothing is shown — not even averages — until {agg['need']} employees have responded, so nobody can be singled out.</div>")
    else:
        _scorecard(agg, u["org"], u.get("org_simulated"), "org")
        pub = CU.is_published(oid)
        st.toggle("Publish this scorecard to candidates (aggregates only)", value=pub, key="cu_pub", on_change=lambda: CU.set_published(oid, S.cu_pub))
        ui.md("<div class='nd-note'>Use the discussion areas to start a conversation with your team. NEXUS DELTA never shows individual answers, never links an answer to a person, and does not rate employees.</div>")


def _employee(go):
    u = S.user; cyc = CU.cycle(); n = CU.count(u["org_id"], cyc)
    ui.md(f"<div class='nd-note'>You are rating <b>{ui.esc(u['org'])}</b> for {cyc}. Your answers are <b>encrypted (AES-256-GCM) and stored without your name or user id</b>. The organisation sees only group averages after {CU.K_MIN} people respond. You can submit once per quarter and cannot edit afterwards.</div>")
    if S.get("cu_done"): ui.md(f"<div class='nd-note' style='border-color:{C['teal']}'>{ui.esc(S.cu_done)}</div>")
    ui.md("<div class='nd-label' style='margin:12px 0 4px 0'>PART A · HOW THE WORK ACTUALLY IS</div>")
    for d, t, lo, hi in CU.JOB: _scale(t, f"cu_{d}", lo, hi)
    ui.md("<div class='nd-label' style='margin:14px 0 4px 0'>PART B · CULTURE HEALTH</div>")
    for d, t, lo, hi in CU.HEALTH: _scale(t, f"cu_{d}", lo, hi)
    def send():
        ok, msg = CU.submit(u, {i: S.get(f"cu_{i}") for i in CU._ids()})
        S.cu_done = msg if ok else None; S.cu_err = None if ok else msg
        if ok: [S.pop(f"cu_{i}", None) for i in CU._ids()]
    st.button("SUBMIT ANONYMOUSLY ›", key="cu_send", type="primary", on_click=send)
    if S.get("cu_err"): ui.err(S.cu_err)
    agg = CU.aggregate(u["org_id"], cyc)
    ui.md(f"<div class='nd-sub' style='margin-top:6px'>{n} response(s) so far this quarter.</div>")
    if not agg["suppressed"]:
        with st.expander("SEE YOUR ORGANISATION'S SCORECARD"): _scorecard(agg, u["org"], u.get("org_simulated"), "emp")
