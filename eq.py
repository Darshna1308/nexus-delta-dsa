"""OPTIONAL EQ / people-skills self-assessment. PROPOSED, indicative only — not clinical, not validated, never used in fit scores, hiring or rejection.
Loaded only when the user asks for it. The SDS dataset is NOT an EQ score and is not used here."""
import numpy as np

DISCLAIMER = "Indicative self-assessment — not a clinical or validated diagnostic. It does not enter your technical fit, work-style fit or any hiring decision."
DIMS = ["Self-awareness", "Communication", "Perspective-taking", "Conflict handling", "Adaptability"]
ITEMS = [  # (dimension, text, reverse_scored)
    ("Self-awareness", "I can usually tell what I'm feeling and why, while it is happening.", False),
    ("Self-awareness", "I know which situations reliably make me less effective.", False),
    ("Self-awareness", "Other people are often surprised by how I react to things.", True),
    ("Communication", "I adjust how I explain things to suit the person I'm talking to.", False),
    ("Communication", "I check that others have understood me instead of assuming.", False),
    ("Communication", "I find it hard to say difficult things clearly.", True),
    ("Perspective-taking", "In a disagreement I can state the other person's view fairly.", False),
    ("Perspective-taking", "I ask what others need before proposing my own solution.", False),
    ("Perspective-taking", "I find it hard to see why someone would think differently from me.", True),
    ("Conflict handling", "I raise disagreements early and calmly.", False),
    ("Conflict handling", "I can stay constructive when someone criticises my work.", False),
    ("Conflict handling", "I avoid conflict even when it hurts the project.", True),
    ("Adaptability", "I adjust quickly when a colleague's plan changes mine.", False),
    ("Adaptability", "I stay productive when the team's way of working changes.", False),
    ("Adaptability", "Unexpected changes leave me stuck for a long time.", True),
]


def score(ans: dict) -> dict:
    """ans {item_index: 1..5} → {dimension: mean (reverse items flipped)}; bands: Developing < 2.75 ≤ Solid < 3.75 ≤ Strong."""
    acc = {}
    for i, v in ans.items():
        if v is None: continue
        d, _, rev = ITEMS[int(i)]; acc.setdefault(d, []).append(6 - float(v) if rev else float(v))
    out = {}
    for d, vs in acc.items():
        m = float(np.mean(vs)); out[d] = dict(value=m, band="Strong" if m >= 3.75 else ("Solid" if m >= 2.75 else "Developing"), n=len(vs))
    return out
