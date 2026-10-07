# Deploying NEXUS DELTA

## 0. Run locally first (2 minutes)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                                    # opens http://localhost:8501
python test_app.py                                      # optional: 157 automated checks
```
Demo accounts are created automatically on first load (SIMULATED data):
`demo_candidate`, `demo_employee`, `demo_org` — password `Demo#2026pw`. Guided demo: `http://localhost:8501/?demo=1`.

## 1. Push to GitHub
1. github.com → **New repository** → name `nexus-delta` → Public → do **not** add a README/.gitignore → Create.
2. In this folder:
```bash
git remote add origin https://github.com/<your-username>/nexus-delta.git
git branch -M main
git push -u origin main
```
When asked for a password, paste a **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens → Fine-grained → repo *Contents: Read and write*).
3. Teammates: repo → Settings → Collaborators → add Anwesha and Saamyaraj.

## 2. Deploy on Streamlit Community Cloud (free)
1. share.streamlit.io → sign in with GitHub → **Create app** → *Deploy a public app from GitHub*.
2. Repository `<your-username>/nexus-delta`, branch `main`, main file `app.py`.
3. **Advanced settings → Python version: 3.13** (the saved model was trained with scikit-learn 1.9.1 on 3.13).
4. **Secrets** — paste (generate your own key with the command in `.streamlit/secrets.toml.example`):
```toml
NEXUS_VAULT_KEY = "your-base64-32-byte-key"
```
5. Deploy. First build takes ~3–5 min. `packages.txt` installs Tesseract for image OCR.
6. Custom URL: App → Settings → General → set subdomain, e.g. `nexus-delta-dsa.streamlit.app`.

### Know this before judging day
- Streamlit Cloud's disk is **wiped on restart/sleep**. Accounts and culture responses created live will disappear; the SIMULATED demo org is recreated automatically. A production deployment would point `vault.py` at a managed database (Postgres/MySQL) — the encryption layer does not change.
- Apps sleep after inactivity. **Open the URL 10 minutes before you present** and click through once.
- Keep `NEXUS_VAULT_KEY` the same between deploys; with a new key, old ciphertext cannot be decrypted (by design).
- Backup plan: run locally on the laptop (`streamlit run app.py`) — the app is fully offline.

## 3. Optional
- Voice ("Hear this role"): `pip install vosk` and set `NEXUS_VOSK_MODEL=/path/to/vosk-model-small-en-in-0.4` (offline). Not available on Streamlit Cloud by default; text fallback always works.
- Rebuild analytics: put the four organiser files in `data/` and run `notebooks/01…07` in order (or in Colab). They regenerate `out/`.
- SAS: `nexus_delta_sas_mirror.sas` is an unexecuted template mirroring notebook logic.
