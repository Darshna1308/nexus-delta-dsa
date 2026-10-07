# NEXUS DELTA — Team DSA (Chandigarh University · Build For Bharat 2.0)
Evidence-first capability intelligence. Offline; no remote API.

Run: `pip install -r requirements.txt && streamlit run app.py` — full deploy steps in **DEPLOY.md**.
Demo: open `/?demo=1`. Tests: `python test_app.py` (104 checks).
Notebooks 01–07 in `notebooks/` regenerate `out/` (results.json, taxonomy.json, app_artifacts.json, model).
Optional voice: set NEXUS_VOSK_MODEL or NEXUS_WHISPER_MODEL. OCR needs tesseract.
SAS file is an unexecuted template. Work DNA, EQ and role profiles are PROPOSED/SIMULATED, not validated.

## Accounts, encryption and culture ratings
- Sign in / create account / continue as guest. Roles: Candidate, Employee (joins with a single-use invite code), Organisation admin.
- Demo data is created automatically on first load (or `python seed_demo.py`): SIMULATED demo accounts (demo_candidate / demo_employee / demo_org, password `Demo#2026pw`) and a SIMULATED organisation.
- Employees rate their workplace (CULTURE page). Answers are AES-256-GCM encrypted, stored with no user id, and shown only in aggregate once 5+ employees respond; the organisation chooses whether to publish.
- Candidates can compare their Work DNA with an organisation's employee-reported profile.
- Set `NEXUS_VAULT_KEY` (base64, 32 bytes) in production; `NEXUS_VAULT_DIR` moves the store. TLS must come from the host.
- Optional EQ stays optional; a saved copy is encrypted with a key derived from the user's password.

## Layout
`app.py` pages · `ui.py` styling · `decision_engine.py` verdicts · `career.py` · `jd_scanner.py` · `work_dna.py` · `eq.py` (optional) · `culture.py` · `auth.py` · `vault.py` (encryption) · `out/` results from notebooks · `notebooks/` 01–07 · `tools/` dev scripts · `docs/` approach note.

Team DSA — Anwesha Kar · Darshna Parihar · Saamyaraj Baidya · Chandigarh University · Build For Bharat 2.0

## Visual system (v4)
- Palette: warm ivory workspace, deep indigo structure, muted teal for evidence, terracotta for action/attention, muted green for FUND/growth, antique gold only for rare high-value insight.
- Typography: IBM Plex Sans (text) and IBM Plex Mono (δ, OR, percentages, counts), served locally from `static/fonts` (SIL OFL).
- 3D (Three.js, bundled locally in `static/nd3d.js`, no CDN): India capability map (home), evidence landscape (Capabilities), salary-band landscape (Insights), development path (Career), evidence pipeline (Evidence). Every scene is drawn only from results.json / app_artifacts.json; a table fallback renders when WebGL is unavailable; idle motion stops under prefers-reduced-motion.
- India outline: @svg-maps/india (CC BY 4.0, Victor Cazanave), showing India's full official boundary. City figures come from notebook 08.
- Rebuild the 3D bundle after editing `tools/3d/nd3d.src.js`: `cd tools/3d && npm install three@0.186.1 esbuild && ./build.sh`.
