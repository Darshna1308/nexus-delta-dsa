// NEXUS DELTA — data-driven 3D scenes (Three.js). Bundled to static/nd3d.js with esbuild (see tools/3d/build.sh).
// Every scene draws only values passed in from results.json / app_artifacts.json. No invented numbers.
import * as THREE from "three";
import { SVGLoader } from "three/examples/jsm/loaders/SVGLoader.js";

const P = { ivory: 0xF6F3EC, paper: 0xFBF9F4, land: 0xEDE6D8, side: 0xC9BBA0, border: 0xB7A98F, navy: 0x16324F, teal: 0x2F5D62,
            terracotta: 0xC87941, green: 0x5F8065, gold: 0xD9A441, charcoal: 0x17212B, grey: 0x68737D, line: 0xD8D1C3 };
const DEC = { "FUND": P.green, "FUND WITH REFRAME": P.terracotta, "TIED": P.gold, "MONITOR": P.gold, "DEPRIORITISE": P.grey };
const ACTION = { "FUND": "Prioritize", "FUND WITH REFRAME": "Investigate · reframe", "TIED": "Investigate", "MONITOR": "Investigate", "DEPRIORITISE": "Maintain" };
const hex = (c) => "#" + c.toString(16).padStart(6, "0");
const reduced = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const esc = (s) => String(s).replace(/[&<>"]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));

function webglOK() {
  try { const c = document.createElement("canvas"); return !!(window.WebGLRenderingContext && (c.getContext("webgl2") || c.getContext("webgl"))); }
  catch (e) { return false; }
}

const CSS = `
.nd3 { position:relative; width:100%; height:100%; font-family:'IBM Plex Sans',system-ui,sans-serif; color:#17212B; overflow:hidden; }
.nd3 canvas { display:block; width:100%; height:100%; outline:none; cursor:grab; touch-action:pan-y; }
.nd3 canvas:active { cursor:grabbing; }
.nd3 .lbl { position:absolute; left:0; top:0; pointer-events:none; white-space:nowrap; font-size:11px; color:#17212B; transform:translate(-50%,-100%);
  background:rgba(251,249,244,.86); border:1px solid #DDD5C6; padding:1px 6px; border-radius:3px; transition:opacity .25s; }
.nd3 .lbl.city { font-size:10.5px; color:#2F5D62; }
.nd3 .lbl.cap { font-weight:600; font-size:11px; }
.nd3 .lbl.axis { background:none; border:none; color:#68737D; font-size:10.5px; }
.nd3 .mono, .nd3 .num { font-family:'IBM Plex Mono',ui-monospace,monospace; }
.nd3 .bar { position:absolute; left:12px; right:12px; top:10px; display:flex; flex-wrap:wrap; gap:6px; z-index:3; }
.nd3 .bar button { font:500 12px 'IBM Plex Sans',sans-serif; color:#16324F; background:rgba(251,249,244,.92); border:1px solid #CFC6B5; border-radius:999px;
  padding:4px 11px; cursor:pointer; transition:background .2s, border-color .2s, color .2s; }
.nd3 .bar button:hover { border-color:#16324F; }
.nd3 .bar button:focus-visible { outline:2px solid #C87941; outline-offset:2px; }
.nd3 .bar button[aria-pressed="true"] { background:#16324F; color:#F6F3EC; border-color:#16324F; }
.nd3 .bar button .dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:6px; vertical-align:1px; }
.nd3 .panel { position:absolute; right:12px; bottom:12px; width:min(300px, calc(100% - 24px)); background:rgba(251,249,244,.95); border:1px solid #D8D1C3;
  border-radius:6px; padding:12px 14px; font-size:12.5px; line-height:1.45; z-index:3; transition:opacity .35s, transform .35s; }
.nd3 .panel.top { top:44px; bottom:auto; }
.nd3 .panel.hide { opacity:0; transform:translateY(6px); pointer-events:none; }
.nd3 .panel h4 { margin:0 0 8px 0; font-size:14px; font-weight:600; color:#16324F; }
.nd3 .panel .row { display:flex; justify-content:space-between; gap:10px; padding:3px 0; border-bottom:1px solid #ECE6DA; }
.nd3 .panel .row span:first-child { color:#68737D; }
.nd3 .panel .dec { margin-top:8px; display:flex; align-items:center; gap:8px; }
.nd3 .tag { display:inline-block; font-size:10.5px; font-weight:600; letter-spacing:.06em; padding:2px 8px; border-radius:3px; color:#fff; }
.nd3 .conf { margin-top:8px; padding:7px 9px; border-left:3px solid #C87941; background:#FAEEE3; font-size:12px; color:#6B3A15; }
.nd3 .legend { position:absolute; left:12px; bottom:12px; font-size:11px; color:#68737D; background:rgba(251,249,244,.85); padding:5px 8px; border-radius:4px; z-index:2; max-width:55%; }
.nd3 .tip { position:absolute; pointer-events:none; z-index:4; background:#16324F; color:#F6F3EC; font-size:11.5px; padding:5px 8px; border-radius:4px; transform:translate(10px,10px); opacity:0; transition:opacity .15s; }
.nd3 .hint { position:absolute; right:14px; top:44px; font-size:10.5px; color:#68737D; z-index:2; }
.nd3 .fallback { padding:16px; font-size:13px; }
.nd3 .fallback table { border-collapse:collapse; width:100%; } .nd3 .fallback td, .nd3 .fallback th { border-bottom:1px solid #DDD5C6; padding:5px 6px; text-align:left; }
@media (max-width:640px) { .nd3 .panel { width:calc(100% - 24px); } .nd3 .legend { display:none; } .nd3 .hint { display:none; } }
@media (prefers-reduced-motion: reduce) { .nd3 * { transition:none !important; } }
`;

function el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

// ---------------------------------------------------------------- stage: renderer, camera, drag-rotate, parallax, idle, labels, picking
function stage(root, opt) {
  if (!document.getElementById("nd3css")) { const s = el("style"); s.id = "nd3css"; s.textContent = CSS; document.head.appendChild(s); }
  root.classList.add("nd3");
  if (!webglOK()) { root.innerHTML = `<div class="fallback">${opt.fallback || "3D view unavailable on this device."}</div>`; return null; }
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const canvas = renderer.domElement; canvas.tabIndex = 0; canvas.setAttribute("role", "img"); canvas.setAttribute("aria-label", opt.aria || "3D chart");
  root.appendChild(canvas);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(opt.fov || 34, 1, 0.1, 200);
  const base = new THREE.Vector3(...(opt.cam || [0, 6, 9])); const target = new THREE.Vector3(...(opt.target || [0, 0, 0]));
  camera.position.copy(base); camera.lookAt(target);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xD9CFBD, 1.05));
  const sun = new THREE.DirectionalLight(0xffffff, 1.35); sun.position.set(-4, 9, 6); scene.add(sun);
  const fill = new THREE.DirectionalLight(0xFFF3E0, 0.35); fill.position.set(6, 3, -4); scene.add(fill);
  const world = new THREE.Group(); scene.add(world);
  const layer = el("div"); layer.style.cssText = "position:absolute;inset:0;pointer-events:none;z-index:1"; root.appendChild(layer);
  const tip = el("div", "tip"); root.appendChild(tip);
  const st = { yaw: opt.yaw || 0, pitch: 0, tYaw: opt.yaw || 0, tPitch: 0, px: 0, py: 0, drag: false, lastX: 0, lastY: 0, lastInteract: -1e9, visible: true, labels: [], pick: [], hover: null };
  const R = reduced();
  function resize() { const w = root.clientWidth || 600, h = root.clientHeight || 400; renderer.setSize(w, h, false); camera.aspect = w / h; camera.fov = (opt.fov || 34) * (w < 560 ? 1.25 : 1); camera.updateProjectionMatrix(); }
  resize(); new ResizeObserver(resize).observe(root);
  new IntersectionObserver((e) => { st.visible = e[0].isIntersecting; }).observe(root);
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  function hit(ev) {
    const r = canvas.getBoundingClientRect(); ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera); const h = ray.intersectObjects(st.pick, false); return h.length ? h[0].object : null;
  }
  let down = null;
  canvas.addEventListener("pointerdown", (e) => { st.drag = true; st.lastX = e.clientX; st.lastY = e.clientY; down = [e.clientX, e.clientY]; st.lastInteract = performance.now(); canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointerup", (e) => {
    st.drag = false; if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 5) { const o = hit(e); if (o && o.userData.onClick) o.userData.onClick(); }
    down = null;
  });
  canvas.addEventListener("pointermove", (e) => {
    const r = canvas.getBoundingClientRect(); st.px = ((e.clientX - r.left) / r.width) * 2 - 1; st.py = ((e.clientY - r.top) / r.height) * 2 - 1;
    if (st.drag) {
      st.tYaw += (e.clientX - st.lastX) * 0.006; st.tPitch = Math.max(-0.35, Math.min(0.25, st.tPitch + (e.clientY - st.lastY) * 0.003));
      st.lastX = e.clientX; st.lastY = e.clientY; st.lastInteract = performance.now(); return;
    }
    const o = hit(e); canvas.style.cursor = o && o.userData.onClick ? "pointer" : "grab";
    if (o && o.userData.tip) { tip.innerHTML = o.userData.tip(); tip.style.left = (e.clientX - r.left) + "px"; tip.style.top = (e.clientY - r.top) + "px"; tip.style.opacity = 1; }
    else tip.style.opacity = 0;
  });
  canvas.addEventListener("pointerleave", () => { tip.style.opacity = 0; st.px = 0; st.py = 0; });
  canvas.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") st.tYaw -= 0.15; else if (e.key === "ArrowRight") st.tYaw += 0.15; else return;
    st.lastInteract = performance.now(); e.preventDefault();
  });
  function label(text, cls) { const d = el("div", "lbl " + (cls || ""), text); layer.appendChild(d); const L = { d, p: new THREE.Vector3(), obj: null, show: true }; st.labels.push(L); return L; }
  const v = new THREE.Vector3();
  const updates = [];
  function frame(t) {
    requestAnimationFrame(frame);
    if (!st.visible || document.hidden) return;
    const idle = !R && performance.now() - st.lastInteract > 7000;
    const sway = idle ? Math.sin(t * 0.00009) * 0.12 : 0;
    st.yaw += (st.tYaw + sway - st.yaw) * 0.08; st.pitch += (st.tPitch - st.pitch) * 0.08;
    world.rotation.y = st.yaw; world.rotation.x = st.pitch;
    const par = R ? 0 : 0.25; camera.position.set(base.x + st.px * par, base.y - st.py * par * 0.6, base.z); camera.lookAt(target);
    for (const u of updates) u(t);
    renderer.render(scene, camera);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    for (const L of st.labels) {
      if (!L.show) { L.d.style.opacity = 0; continue; }
      v.copy(L.p); if (L.obj) L.obj.localToWorld(v); else world.localToWorld(v); v.project(camera);
      if (v.z > 1) { L.d.style.opacity = 0; continue; }
      L.d.style.opacity = 1; L.d.style.transform = `translate(${(v.x * 0.5 + 0.5) * w}px, ${(-v.y * 0.5 + 0.5) * h}px) translate(-50%,-100%)`;
    }
  }
  requestAnimationFrame(frame);
  return { THREE, renderer, scene, camera, world, st, label, updates, tip, root, layer, R };
}

function tween(updates, get, set, to, ms) { // eased value animation used for heights / opacity
  const from = get(); const t0 = performance.now(); const dur = reduced() ? 0 : ms;
  const fn = () => { const k = dur ? Math.min(1, (performance.now() - t0) / dur) : 1; const e = 1 - Math.pow(1 - k, 3); set(from + (to - from) * e); if (k >= 1) updates.splice(updates.indexOf(fn), 1); };
  updates.push(fn);
}

function evidencePanel(c, extra) {
  const col = hex(DEC[c.verdict] || P.grey);
  return `<h4>${esc(c.label)}</h4>
    <div class="row"><span>Internal effect (Cliff's δ)</span><span class="num">${c.delta >= 0 ? "+" : ""}${c.delta.toFixed(2)}</span></div>
    <div class="row"><span>Market association (OR, S5–S6)</span><span class="num">${c.or_lo.toFixed(2)}–${c.or_hi.toFixed(2)}</span></div>
    <div class="row"><span>Headroom (juniors below 5.0)</span><span class="num">${c.headroom.toFixed(0)}%</span></div>
    ${c.p_beat ? `<div class="row"><span>Bootstrap win-rate vs runner-up</span><span class="num">${(c.p_beat * 100).toFixed(1)}%</span></div>` : ""}
    <div class="dec"><span class="tag" style="background:${col}">${esc(c.verdict)}</span><span style="color:#68737D;font-size:12px">${esc(ACTION[c.verdict] || "")}</span></div>
    ${c.conflict ? `<div class="conf"><b>Evidence conflict detected.</b> Strong internal signal, market discount. The discount sits with MIS/reporting keywords; visualisation alone is neutral.</div>` : ""}
    ${extra || ""}`;
}

// ---------------------------------------------------------------- 1. India capability map
export async function india(root, D) {
  const caps = D.caps, cities = D.cities;
  const fb = `<b>Data-role postings by city</b><table><tr><th>City</th><th>Postings</th><th>≥ 10 LPA</th></tr>${cities.map((c) => `<tr><td>${esc(c.name)}</td><td>${c.n}</td><td>${c.pct10.toFixed(0)}%</td></tr>`).join("")}</table>`;
  const S = stage(root, { cam: [0.4, 9.6, 7.9], target: [0.4, 0.0, 0.35], fov: 34, fallback: fb, aria: "3D map of India: data-role postings by city and capability evidence" });
  if (!S) return;
  const { world, label, updates } = S;
  const svgText = await (await fetch(D.svg)).text();
  const data = new SVGLoader().parse(svgText);
  const s = 0.0105, W = 612, H = 696, depth = 9;
  const map = new THREE.Group(); map.rotation.x = -Math.PI / 2; map.position.set(-W / 2 * s, 0, -H / 2 * s); map.scale.set(s, -s, s); world.add(map);
  const top = new THREE.MeshStandardMaterial({ color: P.land, roughness: 0.92, metalness: 0, side: THREE.DoubleSide });
  const side = new THREE.MeshStandardMaterial({ color: P.side, roughness: 0.95, metalness: 0, side: THREE.DoubleSide });
  const lineMat = new THREE.LineBasicMaterial({ color: P.border, transparent: true, opacity: 0.8 });
  for (const path of data.paths) {
    for (const sh of SVGLoader.createShapes(path)) {
      const g = new THREE.ExtrudeGeometry(sh, { depth, bevelEnabled: false, curveSegments: 2 });
      map.add(new THREE.Mesh(g, [top, side]));
      const pts = sh.getPoints(2).map((p) => new THREE.Vector3(p.x, p.y, -0.6));
      const ln = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), lineMat); map.add(ln);
    }
  }
  // svg mesh is in local coords (x, y_svg, z=depth*-1 up after flip) -> world: X=(x-306)*s, Y=depth*s, Z=(y-348)*s
  const mer = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
  const toSvg = (lon, lat) => [(lon - 68.11) * 20.8826, (mer(37.08) - mer(lat)) * 1200.45];
  const topY = depth * s;
  const maxN = Math.max(...cities.map((c) => c.n));
  const pillars = [];
  const pg = new THREE.CylinderGeometry(0.075, 0.075, 1, 18); pg.translate(0, 0.5, 0);
  for (const c of cities) {
    const [x, y] = toSvg(c.lon, c.lat);
    const m = new THREE.Mesh(pg, new THREE.MeshStandardMaterial({ color: P.teal, roughness: 0.6 }));
    m.position.set((x - W / 2) * s, topY, (y - H / 2) * s); m.scale.y = 0.001; world.add(m);
    const h0 = 0.18 + 1.6 * Math.sqrt(c.n / maxN);
    m.userData = { c, h: h0, tip: () => `<b>${esc(c.name)}</b><br><span class="num">${c.n.toLocaleString("en-IN")}</span> data-role postings<br><span class="num">${c.pct10.toFixed(1)}%</span> at ≥ 10 LPA${S.sel ? `<br>${esc(S.sel.label)}: <span class="num">${c.caps[S.sel.key].toFixed(1)}%</span> of postings` : ""}` };
    S.st.pick.push(m); pillars.push(m);
    const L = label(esc(c.name), "city"); L.obj = m; L.p.set(0, 1.04, 0); L.show = c.n >= 400;
    tween(updates, () => m.scale.y, (v) => (m.scale.y = v), h0, 900);
  }
  // capability nodes: an arc above the subcontinent, each linked to its three highest-demand cities (n >= 100)
  const capGroup = new THREE.Group(); world.add(capGroup);
  const sg = new THREE.SphereGeometry(0.16, 24, 16);
  const links = new THREE.Group(); world.add(links);
  const nodes = {};
  caps.forEach((c, i) => {
    // an arc over the Bay of Bengal, east of the peninsula
    const pos = new THREE.Vector3(2.15 + 0.35 * Math.sin(i * 0.8), 1.15, 0.35 + i * 0.6);
    const mat = new THREE.MeshStandardMaterial({ color: DEC[c.verdict] || P.grey, roughness: 0.45, metalness: 0.05 });
    const m = new THREE.Mesh(sg, mat); m.position.copy(pos); capGroup.add(m);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.012, 8, 48), new THREE.MeshBasicMaterial({ color: P.navy, transparent: true, opacity: 0 }));
    ring.position.copy(pos); ring.rotation.x = Math.PI / 2; capGroup.add(ring);
    m.userData = { onClick: () => select(c.key), tip: () => `<b>${esc(c.label)}</b><br>${esc(c.verdict)} · click for evidence` };
    S.st.pick.push(m); nodes[c.key] = { m, ring, pos };
    const L = label(esc(c.short || c.label), "cap"); L.p.copy(pos).add(new THREE.Vector3(0, 0.36, 0));
  });
  // UI: chips, panel, legend
  const bar = el("div", "bar"); root.appendChild(bar);
  const mk = (key, text, color) => { const b = el("button", "", `${color ? `<span class="dot" style="background:${color}"></span>` : ""}${esc(text)}`); b.setAttribute("aria-pressed", "false"); b.onclick = () => select(key); bar.appendChild(b); return b; };
  const chips = { all: mk("all", "All data-role postings") };
  caps.forEach((c) => (chips[c.key] = mk(c.key, c.short || c.label, hex(DEC[c.verdict] || P.grey))));
  const panel = el("div", "panel hide"); panel.setAttribute("aria-live", "polite"); root.appendChild(panel);
  const legend = el("div", "legend"); root.appendChild(legend);
  root.appendChild(el("div", "hint", "Drag to rotate · click a capability"));
  function select(key) {
    S.st.lastInteract = performance.now();
    Object.entries(chips).forEach(([k, b]) => b.setAttribute("aria-pressed", String(k === key)));
    while (links.children.length) links.remove(links.children[0]);
    Object.values(nodes).forEach((n) => { n.ring.material.opacity = 0; n.m.scale.setScalar(1); });
    if (key === "all") {
      S.sel = null; panel.classList.add("hide");
      legend.innerHTML = `Pillar height = data-role postings per city (n = ${cities.reduce((a, c) => a + c.n, 0).toLocaleString("en-IN")} city mentions; a posting may list several cities).`;
      pillars.forEach((m) => { m.material.color.setHex(P.teal); tween(updates, () => m.scale.y, (v) => (m.scale.y = v), m.userData.h, 600); });
      return;
    }
    const c = caps.find((x) => x.key === key); S.sel = c; const n = nodes[key];
    n.ring.material.opacity = 0.9; n.m.scale.setScalar(1.25);
    const col = DEC[c.verdict] || P.grey;
    const mx = Math.max(...cities.map((x) => x.caps[key]));
    pillars.forEach((m) => { const share = m.userData.c.caps[key]; m.material.color.setHex(col); tween(updates, () => m.scale.y, (v) => (m.scale.y = v), 0.12 + 1.7 * (share / mx), 600); });
    const topC = cities.filter((x) => x.n >= 100).sort((a, b) => b.caps[key] - a.caps[key]).slice(0, 3);
    for (const tc of topC) {
      const pm = pillars.find((p) => p.userData.c === tc); const end = pm.position.clone().add(new THREE.Vector3(0, 0.1 + 1.7 * (tc.caps[key] / mx), 0));
      const mid = n.pos.clone().lerp(end, 0.5).add(new THREE.Vector3(0, 0.6, 0));
      const curve = new THREE.QuadraticBezierCurve3(n.pos.clone(), mid, end);
      links.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(32)), new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.7 })));
    }
    legend.innerHTML = `Pillar height = share of each city's data-role postings that ask for ${esc(c.label)}. Lines link to the three highest-demand cities (n ≥ 100).`;
    panel.innerHTML = evidencePanel(c, `<div style="margin-top:8px;font-size:12px;color:#68737D">Highest demand: ${topC.map((x) => `${esc(x.name)} <span class="num">${x.caps[key].toFixed(1)}%</span>`).join(" · ")}</div>`);
    panel.classList.remove("hide");
  }
  select(D.initial || "all");
}

// ---------------------------------------------------------------- 2. Evidence landscape: X = Cliff's δ, Z = market OR, height = headroom
export function landscape(root, D) {
  const caps = D.caps;
  const fb = `<table><tr><th>Capability</th><th>δ</th><th>OR</th><th>Headroom</th><th>Decision</th></tr>${caps.map((c) => `<tr><td>${esc(c.label)}</td><td>${c.delta.toFixed(2)}</td><td>${c.or_lo.toFixed(2)}–${c.or_hi.toFixed(2)}</td><td>${c.headroom.toFixed(0)}%</td><td>${esc(c.verdict)}</td></tr>`).join("")}</table>`;
  const S = stage(root, { cam: [0.6, 5.6, 7.6], target: [0, 0.4, 0], fov: 36, yaw: -0.25, fallback: fb, aria: "3D evidence landscape: internal effect against market association" });
  if (!S) return;
  const { world, label, updates } = S;
  const X = (d) => (d / 0.7) * 6 - 3, Z = (o) => -((o - 0.6) / (1.7 - 0.6)) * 5 + 2.5, Hh = (h) => (h / 100) * 2.4;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 5.4), new THREE.MeshStandardMaterial({ color: P.paper, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -0.01; world.add(floor);
  const quad = (x0, x1, z0, z1, color, op) => { const g = new THREE.PlaneGeometry(Math.abs(x1 - x0), Math.abs(z1 - z0)); const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: op })); m.rotation.x = -Math.PI / 2; m.position.set((x0 + x1) / 2, 0.002, (z0 + z1) / 2); world.add(m); return m; };
  const conflictQ = quad(X(0.33), X(0.7), Z(1.0), Z(0.6), P.terracotta, 0.10);
  quad(X(0.33), X(0.7), Z(1.7), Z(1.0), P.green, 0.08);
  const grid = new THREE.Group(); world.add(grid);
  const gm = new THREE.LineBasicMaterial({ color: P.line });
  for (let d = 0; d <= 0.7001; d += 0.1) grid.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(X(d), 0, Z(0.6)), new THREE.Vector3(X(d), 0, Z(1.7))]), gm));
  for (let o = 0.6; o <= 1.7001; o += 0.1) grid.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(X(0), 0, Z(o)), new THREE.Vector3(X(0.7), 0, Z(o))]), gm));
  const ref = new THREE.LineDashedMaterial({ color: P.navy, dashSize: 0.12, gapSize: 0.08 });
  const l1 = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(X(0.33), 0.004, Z(0.6)), new THREE.Vector3(X(0.33), 0.004, Z(1.7))]), ref); l1.computeLineDistances(); world.add(l1);
  const l2 = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(X(0), 0.004, Z(1)), new THREE.Vector3(X(0.7), 0.004, Z(1))]), ref); l2.computeLineDistances(); world.add(l2);
  const ax = (t, x, z) => { const L = label(t, "axis"); L.p.set(x, 0, z); };
  for (const d of [0, 0.2, 0.4, 0.6]) ax(`<span class="num">${d.toFixed(1)}</span>`, X(d), Z(0.6) + 0.35);
  for (const o of [0.7, 1.0, 1.3, 1.6]) ax(`<span class="num">${o.toFixed(1)}</span>`, X(0) - 0.3, Z(o));
  ax("Internal effect (Cliff's δ) →", X(0.2), Z(0.6) + 0.8); ax("Market odds ratio ↑", X(0) - 0.55, Z(1.45));
  ax("OR = 1", X(0.7) + 0.35, Z(1)); ax("δ = 0.33", X(0.33), Z(0.6) + 0.8);
  const qL = label("CONFLICT ZONE", "axis"); qL.p.set((X(0.33) + X(0.7)) / 2, 0, Z(0.65)); qL.d.style.color = "#C87941"; qL.d.style.fontWeight = 600;
  const nodes = {};
  const sg = new THREE.SphereGeometry(0.2, 28, 18);
  for (const c of caps) {
    const col = DEC[c.verdict] || P.grey, x = X(c.delta), z = Z(c.or_s5), h = Hh(c.headroom);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 1, 8), new THREE.MeshStandardMaterial({ color: P.navy })); stem.position.set(x, 0, z); stem.geometry.translate(0, 0.5, 0); stem.scale.y = 0.001; world.add(stem);
    const ci = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.02, Math.abs(Z(c.ci_lo) - Z(c.ci_hi))), new THREE.MeshStandardMaterial({ color: col, transparent: true, opacity: 0.55 }));
    ci.position.set(x, 0.01, (Z(c.ci_lo) + Z(c.ci_hi)) / 2); world.add(ci);
    const m = new THREE.Mesh(sg, new THREE.MeshStandardMaterial({ color: col, roughness: 0.4 })); m.position.set(x, 0, z); world.add(m);
    tween(updates, () => stem.scale.y, (v) => (stem.scale.y = v), h, 900); tween(updates, () => m.position.y, (v) => (m.position.y = v), h, 900);
    m.userData = { onClick: () => select(c.key), tip: () => `<b>${esc(c.label)}</b><br>δ <span class="num">${c.delta.toFixed(2)}</span> · OR <span class="num">${c.or_s5.toFixed(2)}</span> · headroom <span class="num">${c.headroom.toFixed(0)}%</span>` };
    S.st.pick.push(m);
    const L = label(esc(c.short || c.label), "cap"); L.obj = m; L.p.set(0, 0.34, 0);
    nodes[c.key] = { m, c };
  }
  const bar = el("div", "bar"); root.appendChild(bar);
  const chips = {}; caps.forEach((c) => { const b = el("button", "", `<span class="dot" style="background:${hex(DEC[c.verdict] || P.grey)}"></span>${esc(c.short || c.label)}`); b.setAttribute("aria-pressed", "false"); b.onclick = () => select(c.key); bar.appendChild(b); chips[c.key] = b; });
  const panel = el("div", "panel top hide"); panel.setAttribute("aria-live", "polite"); root.appendChild(panel);
  const legend = el("div", "legend", "Height = headroom · floor bar = 95% CI of the market odds ratio (S5) · colour = decision"); root.appendChild(legend);
  root.appendChild(el("div", "hint", "Drag to rotate · select Storytelling to see the conflict")); root.querySelector(".hint").style.top = "auto"; root.querySelector(".hint").style.bottom = "14px";
  function select(key) {
    S.st.lastInteract = performance.now();
    Object.entries(chips).forEach(([k, b]) => b.setAttribute("aria-pressed", String(k === key)));
    Object.values(nodes).forEach((n) => n.m.scale.setScalar(n.c.key === key ? 1.3 : 1));
    const c = caps.find((x) => x.key === key);
    conflictQ.material.opacity = c.conflict ? 0.22 : 0.10;
    panel.innerHTML = evidencePanel(c); panel.classList.remove("hide");
  }
  if (D.initial) select(D.initial);
}

// ---------------------------------------------------------------- 3. Market landscape: roles x salary bands, height = share of postings
export function market(root, D) {
  const roles = D.roles, bands = D.bands;
  const fb = `<table><tr><th>Role</th>${bands.map((b) => `<th>${b}</th>`).join("")}</tr>${roles.map((r) => `<tr><td>${esc(r.name)}</td>${r.share.map((v) => `<td>${(v * 100).toFixed(0)}%</td>`).join("")}</tr>`).join("")}</table>`;
  const S = stage(root, { cam: [0, 6.6, 7.4], target: [0.3, 0.3, 0.2], fov: 34, yaw: 0.42, fallback: fb, aria: "3D salary-band landscape by role" });
  if (!S) return;
  const { world, label, updates } = S;
  const nx = bands.length, nz = roles.length, gx = 0.95, gz = 0.95;
  const shades = [0xD7E2E0, 0xB4CAC8, 0x8AABA8, 0x5E8A88, 0x3E6E70, 0x2F5D62];
  const bg = new THREE.BoxGeometry(0.62, 1, 0.62); bg.translate(0, 0.5, 0);
  roles.forEach((r, zi) => {
    r.share.forEach((v, xi) => {
      const m = new THREE.Mesh(bg, new THREE.MeshStandardMaterial({ color: shades[xi], roughness: 0.75 }));
      m.position.set((xi - (nx - 1) / 2) * gx, 0, (zi - (nz - 1) / 2) * gz); m.scale.y = 0.001; world.add(m);
      tween(updates, () => m.scale.y, (h) => (m.scale.y = h), Math.max(0.02, v * 4.6), 800 + xi * 60);
      m.userData = { tip: () => `<b>${esc(r.name)}</b> · ${esc(bands[xi])} LPA<br><span class="num">${(v * 100).toFixed(1)}%</span> of <span class="num">${r.n}</span> postings` };
      S.st.pick.push(m);
    });
    const L = label(`${esc(r.name)} <span class="num" style="color:#68737D">n=${r.n}</span>`, "axis"); L.p.set(-(nx / 2) * gx - 0.35, 0, (zi - (nz - 1) / 2) * gz); L.d.style.transform = ""; 
  });
  bands.forEach((b, xi) => { const L = label(`<span class="num">${esc(b)}</span>`, "axis"); L.p.set((xi - (nx - 1) / 2) * gx, 0, (nz / 2) * gz + 0.25); });
  const base = new THREE.Mesh(new THREE.PlaneGeometry(nx * gx + 0.6, nz * gz + 0.6), new THREE.MeshStandardMaterial({ color: P.paper })); base.rotation.x = -Math.PI / 2; base.position.y = -0.005; world.add(base);
  const lg = el("div", "legend", "Bar height = share of each role's postings in a salary band (LPA). Darker = higher band. Hover a bar for the value."); lg.style.top = "12px"; lg.style.bottom = "auto"; root.appendChild(lg);
  root.appendChild(el("div", "hint", "Drag to rotate"));
}

// ---------------------------------------------------------------- 4. Development path: priority tiers as ascending steps
export function path(root, D) {
  const steps = D.steps;
  const fb = `<ol>${steps.map((s) => `<li><b>${esc(s.cap)}</b> — ${esc(s.tier)}</li>`).join("")}</ol>`;
  const S = stage(root, { cam: [0, 5.2, 8.6], target: [0, 0.9, 0], fov: 34, yaw: 0, fallback: fb, aria: "3D development path of priority tiers" });
  if (!S) return;
  const { world, label, updates } = S;
  const n = steps.length; const curve = new THREE.CatmullRomCurve3(steps.map((_, i) => new THREE.Vector3(-4.2 + (8.4 * i) / Math.max(1, n - 1), 0, Math.sin(i * 1.1) * 0.7)));
  const road = new THREE.Mesh(new THREE.TubeGeometry(curve, 80, 0.035, 8, false), new THREE.MeshStandardMaterial({ color: P.border })); world.add(road);
  const cols = { "HIGH PRIORITY": P.terracotta, "STRATEGIC": P.teal, "STRENGTHEN": P.gold, "MAINTAIN": P.green, "LOW EVIDENCE": P.grey };
  steps.forEach((s, i) => {
    const p = curve.getPoint(i / Math.max(1, n - 1)); const h = 0.18 + i * 0.26;   // the path climbs: step 1 first
    const col = cols[s.tier] || P.teal;
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.68, 1, 40), new THREE.MeshStandardMaterial({ color: col, roughness: 0.75 }));
    m.geometry.translate(0, 0.5, 0); m.position.copy(p); m.scale.y = 0.001; world.add(m);
    tween(updates, () => m.scale.y, (v) => (m.scale.y = v), h, 700 + i * 120);
    m.userData = { tip: () => `<b>${esc(s.cap)}</b> · ${esc(s.tier)}<br>${esc(s.why || "")}` }; S.st.pick.push(m);
    const L = label(`<span style="color:#68737D;font-size:10px">${i + 1} · ${esc(s.tier)}</span><br><b>${esc(s.cap)}</b>`, "cap"); L.obj = m; L.p.set(0, 1.05, 0);
  });
  root.appendChild(el("div", "legend", "Climb from the left: step 1 is what to develop first. Colour = priority tier. Hover a step for the reason."));
}

// ---------------------------------------------------------------- 5. Evidence pipeline: datasets -> taxonomy -> signals -> decision
export function pipeline(root, D) {
  const fb = `<p>${D.nodes.map((n) => esc(n.label)).join(" → ")}</p>`;
  const S = stage(root, { cam: [0, 6.2, 8.2], target: [0, 0.2, 0], fov: 34, yaw: 0, fallback: fb, aria: "3D evidence pipeline" });
  if (!S) return;
  const { world, label, updates, R } = S;
  const pos = {}; const colOf = { data: P.side, hub: P.navy, signal: P.teal, decision: P.green };
  for (const nd of D.nodes) {
    const p = new THREE.Vector3(nd.x, 0, nd.z); pos[nd.id] = p;
    const geo = nd.kind === "hub" ? new THREE.CylinderGeometry(0.5, 0.5, 0.35, 6) : new THREE.BoxGeometry(nd.kind === "decision" ? 1.0 : 0.85, 0.3, 0.6);
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: colOf[nd.kind], roughness: 0.7 })); m.position.copy(p).add(new THREE.Vector3(0, 0.15, 0)); world.add(m);
    const L = label(`<b>${esc(nd.label)}</b>${nd.sub ? `<br><span class="num" style="color:#68737D">${esc(nd.sub)}</span>` : ""}`, "cap"); L.obj = m; L.p.set(0, 0.42, 0);
  }
  const dots = [];
  for (const [a, b] of D.links) {
    const p0 = pos[a].clone().add(new THREE.Vector3(0, 0.15, 0)), p1 = pos[b].clone().add(new THREE.Vector3(0, 0.15, 0));
    const mid = p0.clone().lerp(p1, 0.5).add(new THREE.Vector3(0, 0.5, 0)); const c = new THREE.QuadraticBezierCurve3(p0, mid, p1);
    world.add(new THREE.Mesh(new THREE.TubeGeometry(c, 40, 0.022, 6, false), new THREE.MeshStandardMaterial({ color: P.border })));
    if (!R) { const d = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 8), new THREE.MeshBasicMaterial({ color: P.terracotta })); world.add(d); dots.push({ d, c, o: Math.random() }); }
  }
  updates.push((t) => { for (const x of dots) x.d.position.copy(x.c.getPoint(((t * 0.00012) + x.o) % 1)); });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(9, 5), new THREE.MeshStandardMaterial({ color: P.paper })); floor.rotation.x = -Math.PI / 2; floor.position.y = -0.005; world.add(floor);
  root.appendChild(el("div", "legend", "Datasets never join row-by-row: they meet only at the capability taxonomy."));
}

window.ND3D = { india, landscape, market, path, pipeline };
