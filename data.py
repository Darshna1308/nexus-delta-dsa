"""Data access: everything the app shows comes from results.json / taxonomy.json / app_artifacts.json / saved model. Cached; never recomputes the analytics."""
import json, os
from dataclasses import dataclass, field
import streamlit as st
import config


def _dir(): return os.environ.get("NEXUS_DATA_DIR", config.DATA_DIR)   # read at call time so tests / deployments can redirect
def _path(name): return os.path.join(_dir(), name)


@st.cache_data(show_spinner=False)
def _load_json(path: str, mtime: float):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json(name: str):
    """returns (obj | None, error | None)"""
    p = _path(name)
    if not os.path.exists(p): return None, f"{name} not found in '{_dir()}/'"
    try: return _load_json(p, os.path.getmtime(p)), None
    except Exception as e: return None, f"{name} could not be read ({type(e).__name__})"


@st.cache_resource(show_spinner=False)
def _load_model(path: str, mtime: float):
    import joblib
    return joblib.load(path)


def load_model():
    p = _path("jd_scanner_m2.joblib")
    if not os.path.exists(p): return None, "jd_scanner_m2.joblib not found"
    try: return _load_model(p, os.path.getmtime(p)), None
    except Exception as e: return None, f"scanner model could not be loaded ({type(e).__name__}: version mismatch?)"


@dataclass
class Bundle:
    results: dict = field(default_factory=dict)
    taxonomy: dict = field(default_factory=dict)
    artifacts: dict = field(default_factory=dict)
    model: object = None
    errors: dict = field(default_factory=dict)

    @property
    def ok_results(self): return bool(self.results) and "matrix" in self.results
    @property
    def ok_taxonomy(self): return bool(self.taxonomy) and "TAX" in self.taxonomy
    @property
    def ok_model(self): return self.model is not None
    @property
    def ok_roles(self): return bool(self.artifacts.get("roles"))


def get_bundle() -> Bundle:
    b = Bundle()
    for attr, name in (("results", "results.json"), ("taxonomy", "taxonomy.json"), ("artifacts", "app_artifacts.json")):
        obj, err = load_json(name)
        setattr(b, attr, obj or {})
        if err: b.errors[attr] = err
    b.model, err = load_model()
    if err: b.errors["model"] = err
    if "results" not in b.errors and not b.ok_results: b.errors["results"] = "results.json is present but incomplete (no evidence matrix)"
    return b
