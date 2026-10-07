"""JD Scanner: text extraction (paste / PDF / image-OCR), taxonomy tagging, experience & level parsing, T2 salary-band distribution,
work-style cue lexicon (PROPOSED), and the offline Hear pipeline (STT → transcript → deterministic intent parser). Every external dependency is optional."""
import io, os, re, shutil, wave
import numpy as np, pandas as pd

MIN_CHARS = 40
BANDS = ["0–3", "3–6", "6–10", "10–15", "15–25", "25–50"]


# ----------------------------------------------------------------------------- extraction
def ocr_available() -> bool:
    try:
        import pytesseract, PIL  # noqa
        return shutil.which("tesseract") is not None
    except Exception:
        return False


def extract_text(data: bytes, filename: str) -> dict:
    """returns dict(text, method, warning). Never raises."""
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            rd = PdfReader(io.BytesIO(data)); txt = "\n".join((p.extract_text() or "") for p in rd.pages[:15]).strip()
            if len(txt) < MIN_CHARS:
                return dict(text=txt, method="pdf-text-layer", warning="This PDF has no readable text layer (probably a scan). Upload it as an image, or paste the text.")
            return dict(text=txt, method="pdf-text-layer", warning=None)
        if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")):
            if not ocr_available():
                return dict(text="", method="ocr-unavailable", warning="Local OCR (Tesseract) is not available in this environment. Paste the job description text instead — everything else works.")
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(data)).convert("L")
            txt = pytesseract.image_to_string(img).strip()
            return dict(text=txt, method="local-ocr", warning=None if len(txt) >= MIN_CHARS else "OCR found very little text. Try a sharper/larger image or paste the text.")
        return dict(text="", method="unsupported", warning="Unsupported file type. Use PDF, PNG or JPG — or paste the text.")
    except Exception as e:
        return dict(text="", method="error", warning=f"Could not read that file ({type(e).__name__}). Paste the text instead.")


# ----------------------------------------------------------------------------- parsing
def _first_title(text: str) -> str:
    for ln in text.splitlines():
        ln = ln.strip(" \t-•*:#")
        if 3 <= len(ln) <= 90 and not re.match(r"(?i)^(job description|about|roles?|responsibilit|requirements?)\b", ln): return ln
    return "Untitled role"


def parse_jd(text: str, tax: dict, overrides: dict = None) -> dict:
    """overrides: optional user-corrected fields (title, exp_min, exp_max, loc_tier, seniority, role_family)."""
    t = (text or "").strip(); low = t.lower(); ov = overrides or {}
    warnings = []
    if len(t) < MIN_CHARS: return dict(ok=False, warnings=["Not enough text to scan (need at least ~40 characters)."], text=t)
    TAX = tax.get("TAX", {}) if tax else {}
    title = ov.get("title") or _first_title(t)
    m = re.search(r"(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", low)
    if m: e0, e1 = float(m.group(1)), float(m.group(2))
    else:
        m = re.search(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", low)
        e0, e1 = (float(m.group(1)), float(m.group(1)) + 3) if m else (None, None)
    if e0 is None: warnings.append("No experience range found — assumed 2–5 years."); e0, e1 = 2.0, 5.0
    e0, e1 = ov.get("exp_min", e0), ov.get("exp_max", e1)
    seniority = ov.get("seniority")
    if not seniority:
        seniority = "mid"
        for pat, lab in tax.get("SEN", []) if tax else []:
            if re.search(pat, title.lower()): seniority = lab; break
    role_family = ov.get("role_family")
    if not role_family:
        role_family = "other"
        for pat, lab in tax.get("RF", []) if tax else []:
            if re.search(pat, (title + " " + low[:300]).lower()): role_family = lab; break
    loc = ov.get("loc_tier")
    if not loc:
        if tax and re.search(tax.get("T1", "$^"), low): loc = "Tier1"
        elif tax and re.search(tax.get("FOREIGN", "$^"), low): loc = "International"
        else: loc = "Tier1"; warnings.append("No location found — assumed a Tier-1 metro (ASSUMED).")
    flags = {k: int(bool(re.search(p, (title + " " + low).lower()))) for k, p in TAX.items()}
    flags["story"] = int(flags.get("viz", 0) or flags.get("mis", 0))
    is_data = bool(re.search(tax.get("DATA_ROLE_W", "data|analy"), low)) if tax else True
    if not is_data: warnings.append("This does not look like a data/analytics role — tags and the salary band may not be meaningful.")
    if not any(flags.get(k) for k in ("big_data", "maths_stats", "coding", "ai_ml", "viz", "mis")): warnings.append("No capability keywords matched the taxonomy.")
    return dict(ok=True, text=t, title=title, exp_min=e0, exp_max=e1, seniority=seniority, role_family=role_family, loc_tier=loc, flags=flags, is_data=is_data, warnings=warnings)


def required_weights(parsed: dict) -> dict:
    """capability weights for the technical-fit index: tagged capability → 1.0, otherwise a small floor."""
    f = parsed.get("flags", {})
    return {k: (1.0 if f.get(k) else 0.1) for k in ("big_data", "maths_stats", "coding", "ai_ml", "story")}


def salary_distribution(parsed: dict, model):
    """P(band) from the selected T2 model, or None (model missing / error)."""
    if model is None or not parsed.get("ok"): return None
    f = parsed["flags"]; t = (parsed["title"] + " " + parsed["text"][:600]).lower()
    row = dict(job_desig=parsed["title"], text=t, exp_min=parsed["exp_min"], exp_max=parsed["exp_max"], exp_span=parsed["exp_max"] - parsed["exp_min"],
               seniority=parsed["seniority"], loc_tier=parsed["loc_tier"], role_family=parsed["role_family"], jobtype_missing=1, trunc_skills=0, desc_missing=0,
               **{f"{k}_w": int(f.get(k, 0)) for k in ("big_data", "maths_stats", "coding", "ai_ml", "viz", "mis")})
    try:
        return model.predict_proba(pd.DataFrame([row]))[0]
    except Exception:
        return None


# ----------------------------------------------------------------------------- work-style cue lexicon (PROPOSED)
WORK_LEXICON = {   # dim -> (cues that raise the demand, cues that lower it)
    "ambiguity": (r"fast-?paced|ambigu|changing priorit|dynamic environment|start-?up|evolving|undefined|figure out|fluid|greenfield|wear many hats", r"well-?defined|clearly defined|defined processes|clear roadmap|stable environment"),
    "pace": (r"fast-?paced|tight deadline|deadline|urgent|aggressive timeline|time-?bound|rapid|quick turnaround|sprint", r""),
    "structure": (r"\bprocess(es)?\b|documentation|complian|governance|\bsop\b|standard operating|audit|methodolog|framework", r"ambigu|start-?up|unstructured"),
    "collaboration": (r"cross-?functional|collaborat|stakeholder|team player|work(ing)? with teams|partner with|team", r"individual contributor|work independently"),
    "communication": (r"communicat|present|storytelling|client-?facing|written and verbal|articulate|stakeholder", r""),
    "autonomy": (r"independent|self-?starter|ownership|own the|self-?driven|end-?to-?end|drive", r"under (the )?supervision|guidance of|assist"),
    "feedback": (r"feedback|code review|review|mentor|performance", r""),
    "work_ethic": (r"attention to detail|accountab|quality|rigou?r|deliver|commit|reliab", r""),
    "adaptability": (r"adapt|flexib|learn quickly|fast learner|multi-?task|versatil|new technolog", r""),
    "empathy": (r"customer|client|empath|user needs|coach|mentor|people", r""),
    "intensity": (r"on-?call|24x7|24/7|weekend|shift|long hours|night|travel|overtime", r""),
}


def work_signals(text: str) -> dict:
    """dim → dict(value 1-5, up=[terms], down=[terms], signal=bool). 3.0 = no signal. PROPOSED — not validated."""
    low = (text or "").lower(); out = {}
    for dim, (up, down) in WORK_LEXICON.items():
        u = sorted({m.group(0) for m in re.finditer(up, low)}) if up else []
        d = sorted({m.group(0) for m in re.finditer(down, low)}) if down else []
        val = float(np.clip(3.0 + 0.7 * min(len(u), 3) - 0.7 * min(len(d), 3), 1.0, 5.0))
        out[dim] = dict(value=round(val, 1), up=u[:4], down=d[:4], signal=bool(u or d))
    return out


# ----------------------------------------------------------------------------- HEAR: offline STT + deterministic intent parser
def stt_status() -> dict:
    vm, wm = os.environ.get("NEXUS_VOSK_MODEL"), os.environ.get("NEXUS_WHISPER_MODEL")
    try:
        import vosk  # noqa
        if vm and os.path.isdir(vm): return dict(available=True, engine="vosk", reason="")
    except Exception: pass
    try:
        import faster_whisper  # noqa
        if wm and os.path.isdir(wm): return dict(available=True, engine="faster-whisper", reason="")
    except Exception: pass
    return dict(available=False, engine=None, reason="No offline speech model is installed in this environment. Type your question below — the same intent parser runs on typed text.")


def _to_pcm16k(wav_bytes: bytes) -> bytes:
    with wave.open(io.BytesIO(wav_bytes)) as w:
        n, ch, sw, fr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate(); raw = w.readframes(n)
    if sw != 2: raise ValueError("expected 16-bit PCM wav")
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if ch > 1: a = a.reshape(-1, ch).mean(axis=1)
    if fr != 16000 and len(a):
        x = np.linspace(0, len(a) - 1, int(len(a) * 16000 / fr)); a = np.interp(x, np.arange(len(a)), a)
    return a.astype(np.int16).tobytes()


def transcribe(wav_bytes: bytes) -> dict:
    """returns dict(ok, text, confidence, engine, message). Never raises. Audio is processed in memory and not stored."""
    st = stt_status()
    if not st["available"]: return dict(ok=False, text="", confidence=0.0, engine=None, message=st["reason"])
    try:
        pcm = _to_pcm16k(wav_bytes)
        if st["engine"] == "vosk":
            import vosk, json
            rec = vosk.KaldiRecognizer(vosk.Model(os.environ["NEXUS_VOSK_MODEL"]), 16000); rec.SetWords(True); rec.AcceptWaveform(pcm)
            res = json.loads(rec.FinalResult()); words = res.get("result", [])
            conf = float(np.mean([w.get("conf", 0.0) for w in words])) if words else 0.0
            return dict(ok=bool(res.get("text")), text=res.get("text", ""), confidence=conf, engine="vosk", message="")
        from faster_whisper import WhisperModel
        segs, _ = WhisperModel(os.environ["NEXUS_WHISPER_MODEL"], device="cpu", compute_type="int8").transcribe(np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0, language="en")
        segs = list(segs); txt = " ".join(s.text.strip() for s in segs)
        conf = float(np.exp(np.mean([s.avg_logprob for s in segs]))) if segs else 0.0
        return dict(ok=bool(txt), text=txt, confidence=conf, engine="faster-whisper", message="")
    except Exception as e:
        return dict(ok=False, text="", confidence=0.0, engine=st["engine"], message=f"Speech recognition failed ({type(e).__name__}). Type your question instead.")


CAP_WORDS = {"maths_stats": r"math|statistic|stats", "story": r"storytell|dashboard|visuali[sz]|reporting|\bmis\b", "ai_ml": r"\bai\b|\bml\b|machine learning|artificial", "coding": r"cod(e|ing)|programming|python", "big_data": r"big data|hadoop|spark"}
ROLE_WORDS = {"Data Scientist": r"data scien", "Data Analyst": r"data analy", "ML Engineer": r"\bml\b|machine learning engineer", "Data Engineer": r"data engineer", "Analytics Consultant": r"consultant"}
LOW_CONF = 0.80


def parse_intent(text: str) -> dict:
    """deterministic keyword grammar — no model, no remote call."""
    t = (text or "").lower().strip()
    if not t: return dict(understood=False, intent=None, page=None, slots={}, message="Nothing to interpret.")
    cap = next((k for k, p in CAP_WORDS.items() if re.search(p, t)), None)
    role = next((k for k, p in ROLE_WORDS.items() if re.search(p, t)), None)
    if re.search(r"scan|decode|job description|\bjd\b", t): return dict(understood=True, intent="scan_role", page="JD SCANNER", slots={}, message="Opening the JD Scanner.")
    if re.search(r"work dna|work style|friction|sustainab|fit the way|burn", t): return dict(understood=True, intent="work_dna", page="WORK DNA", slots={}, message="Opening Work DNA.")
    if re.search(r"learn next|develop next|become|i want to|student|career|my skills", t): return dict(understood=True, intent="career", page="CAREER INTELLIGENCE", slots={"role": role} if role else {}, message="Opening Career Intelligence" + (f" for {role}." if role else "."))
    if re.search(r"provenance|source|sample size|method|how sure|uncertain|limitation|evidence page", t) and not cap: return dict(understood=True, intent="evidence", page="EVIDENCE", slots={}, message="Opening the Evidence page.")
    if cap and re.search(r"fund|invest|verdict|should we|worth|evidence|why|conflict|headroom|signal|market", t): return dict(understood=True, intent="capability_verdict", page="CAPABILITY INTELLIGENCE", slots={"capability": cap}, message="Opening the evidence for that capability.")
    if re.search(r"conflict|disagree|headroom|invest|capabilit|fund|biggest|top signal", t): return dict(understood=True, intent="capability_overview", page="CAPABILITY INTELLIGENCE", slots={"capability": cap} if cap else {}, message="Opening Capability Intelligence.")
    return dict(understood=False, intent=None, page=None, slots={}, message="I couldn't match that to a NEXUS DELTA question. Try: “Should we fund Maths and Statistics?”, “What should I learn next as a data scientist?” or “Scan this job description”.")
