"""Creates DEMO accounts and a SIMULATED organisation so judges can see the full flow. Everything here is flagged SIMULATED in the DB and in the UI.
python seed_demo.py   (idempotent)"""
import random, time, vault, auth, culture

DEMO = {"demo_candidate": ("Demo#2026pw", "CANDIDATE"), "demo_org": ("Demo#2026pw", "ORG"), "demo_employee": ("Demo#2026pw", "EMPLOYEE")}
ORG = "DemoCorp Analytics (SIMULATED)"

def run():
    con = vault.db()
    if con.execute("SELECT 1 FROM orgs WHERE name=?", (ORG,)).fetchone(): con.close(); return "exists"
    con.close()
    u, e = auth.register("demo_org", DEMO["demo_org"][0], "ORG", org_name=ORG); assert not e, e
    con = vault.db(); con.execute("UPDATE orgs SET simulated=1, published=1 WHERE id=?", (u["org_id"],)); con.commit(); con.close()
    codes = [auth.new_invite(u["org_id"]) for _ in range(9)]
    auth.register("demo_candidate", DEMO["demo_candidate"][0], "CANDIDATE")
    rnd = random.Random(7); base = dict(communication=3, collaboration=4, work_ethic=4, autonomy=4, adaptability=3, ambiguity=3, pace=4, structure=3, feedback=3, empathy=3, intensity=4,
                                        safety=3, fairness=3, growth=4, leadership=3, recognition=3, boundaries=2)
    for i, c in enumerate(codes[:8]):   # 8 SIMULATED employees (one more code stays unused for a live demo)
        name = "demo_employee" if i == 0 else f"sim_employee_{i}"; usr, e = auth.register(name, "Demo#2026pw", "EMPLOYEE", invite=c); assert not e, e
        ans = {k: max(1, min(5, v + rnd.choice([-1, 0, 0, 1]))) for k, v in base.items()}
        # demo_employee deliberately has NOT submitted yet, so the live flow can be shown
        if i: culture.submit(dict(id=usr["id"], role="EMPLOYEE", org_id=usr["org_id"]), ans)
    return "seeded"

if __name__ == "__main__": print(run())
