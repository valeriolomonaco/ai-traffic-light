"""Parametric 3D-printable case for the AI Traffic Light (flat rectangular design).

The lamp is a flat box. On its top face a glowing ring of light frames the OLED screen:
the LED ring sits just under a white diffuser ring, and the screen sits behind the ring,
seen through its hole. The ESP32 board lies beside them, upside down on the floor with its
pins pointing up, so the jumper wires plug in from above. The box is only as deep as the
jumper plugs need.

Four printed parts:
  tray      dark plastic: floor, walls, USB opening, rails for the board, posts for the holder
  holder    dark plastic: screen underneath, LED ring on top, light shield between them
  top       dark plastic: the top plate, with a round hole for the diffuser
  diffuser  white or natural plastic: the glowing ring, it drops into the hole in the top

Usage:
  python -m pip install manifold3d numpy playwright   (playwright only for the preview images)
  python -m playwright install chromium
  python make_case.py      # writes stl/*.stl, previews/*.png and checks that nothing collides

Measure YOUR parts with a caliper and change the numbers below before printing.
Sizes vary by a few millimetres between sellers. All values are in millimetres.
"""

import json
import pathlib
import sys
import tempfile

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

SEG = 128  # smoothness of round shapes

# ---------------- parts you buy (measure these) ----------------
RING_OD, RING_ID, RING_T = 50.0, 36.0, 3.5        # 12-LED WS2812B ring: outer, inner, thickness
OLED_PCB = (27.3, 27.8, 1.6)                       # screen module board: width, height, thickness
OLED_GLASS = (26.7, 19.3, 1.5)                     # glass on the front of the module
OLED_GLASS_DY = -2.5                               # glass centre offset from board centre, away from the pins
BOARD = (28.3, 51.5, 1.6)                          # ESP32 DevKit V1: width, length, thickness
BOARD_UNDER = 3.4                                  # tallest part on the component side (ESP32 module)
HEADER_PITCH_X = 25.4                              # distance between the two pin rows
PLUG_H = 14.0                                      # height of a jumper wire's black plug
PIN_BASE = 2.5                                     # plastic strip at the base of the pins

# ---------------- case settings ----------------
WALL = 2.0          # side walls
FLOOR = 2.0         # floor thickness
CORNER_R = 6.0      # rounded corners of the box
FIT = 0.3           # gap between parts that slide together; raise to 0.4 if your print is tight
TOP_T = 1.6         # top plate and diffuser thickness: thinner diffuser lets more light through
DIFFUSE_GAP = 4.0   # air gap between LEDs and diffuser: more gap gives a softer glow
WIRE_ROOM = 6.0     # space above the board's plugs for the wires to bend
SHIELD_WALL = 1.5   # light-shield tube wall
HOLDER_T = 3.0      # holder plate thickness
USB_SLOT = (13.0, 10.0)   # width, height of the cable opening

# ---------------- derived layout ----------------
HOLDER_R = RING_OD / 2 + 2.0                          # holder plate radius
BOARD_ZONE = BOARD[0] + 2 * (FIT + 1.2) + 1.0         # width needed for the board and its rails
INNER_X = 2 * HOLDER_R + 4.5 + BOARD_ZONE + 2.0       # inside length of the box
INNER_Y = max(2 * HOLDER_R, BOARD[1]) + 4.0           # inside width of the box
OUT_X, OUT_Y = INNER_X + 2 * WALL, INNER_Y + 2 * WALL
RING_X = -INNER_X / 2 + 3.5 + HOLDER_R                # centre of the ring and screen (clear of the top's lip)
BOARD_X = INNER_X / 2 - BOARD_ZONE / 2                # centre of the board
BOARD_Y = INNER_Y / 2 - 1.0 - BOARD[1] / 2            # board pushed towards the USB wall (+y)

Z_PCB = FLOOR + BOARD_UNDER                           # underside of the board
Z_BOARD_PLUGS_TOP = Z_PCB + BOARD[2] + PIN_BASE + PLUG_H
HOLDER_Z = FLOOR + 0.5 + PLUG_H + PIN_BASE + OLED_PCB[2]   # underside of the holder: room for the screen plugs
Z_RING = HOLDER_Z + HOLDER_T
Z_TOP_UNDER = max(Z_RING + RING_T + DIFFUSE_GAP, Z_BOARD_PLUGS_TOP + WIRE_ROOM)
HEIGHT = Z_TOP_UNDER + TOP_T
SHIELD_OD = RING_ID - 2 * FIT - 0.2
SHIELD_ID = SHIELD_OD - 2 * SHIELD_WALL
DIFF_R_OUT = RING_OD / 2 + 1.0                        # diffuser outer radius (the glowing band)
DIFF_FLANGE_R = DIFF_R_OUT + 1.2
FLANGE_T = 0.8


def cyl(h, r, z=0.0, r2=None, x=0.0, y=0.0):
    return Manifold.cylinder(h, r, r if r2 is None else r2, SEG).translate((x, y, z))


def box(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    """Box centred on x, y, starting at height z."""
    return Manifold.cube((sx, sy, sz), True).translate((x, y, z + sz / 2))


def rounded(sx, sy, r, h, z=0.0):
    cs = CrossSection.square((sx - 2 * r, sy - 2 * r), True).offset(r, JoinType.Round, 2.0, SEG)
    return Manifold.extrude(cs, h).translate((0, 0, z))


# ---------------- printed parts ----------------
def make_tray():
    shell = rounded(OUT_X, OUT_Y, CORNER_R, Z_TOP_UNDER) - rounded(INNER_X, INNER_Y, CORNER_R - WALL, Z_TOP_UNDER, FLOOR)
    rails = Manifold()
    for sx in (-1, 1):
        rails += box(1.2, 36.0, BOARD_UNDER + BOARD[2] + 1.0,
                     BOARD_X + sx * (BOARD[0] / 2 + FIT + 0.6), BOARD_Y, FLOOR)
    posts = Manifold()
    for ang in (30, 150, 270):
        a = np.radians(ang)
        px, py = RING_X + 23.0 * np.cos(a), 23.0 * np.sin(a)
        posts += cyl(HOLDER_Z - FLOOR, 3.0, FLOOR, x=px, y=py) + cyl(2.0, 1.4, HOLDER_Z, x=px, y=py)
    usb = box(USB_SLOT[0], WALL * 4, FLOOR + USB_SLOT[1], BOARD_X, INNER_Y / 2 + WALL / 2, -0.5)   # notch from the bottom edge
    return shell + rails + posts - usb


def make_holder():
    disc = cyl(HOLDER_T, HOLDER_R, HOLDER_Z, x=RING_X)
    shield = cyl(Z_TOP_UNDER - FLANGE_T - Z_RING, SHIELD_OD / 2, Z_RING, x=RING_X) - cyl(HEIGHT, SHIELD_ID / 2, HOLDER_Z - 1, x=RING_X)
    gw, gh, _ = OLED_GLASS
    window = box(gw + 2 * FIT, gh + 2 * FIT, HOLDER_T + 1, RING_X, OLED_GLASS_DY, HOLDER_Z - 0.5)
    pocket = box(OLED_PCB[0] + 2 * FIT, OLED_PCB[1] + 2 * FIT, 0.6, RING_X, 0, HOLDER_Z - 0.01)
    r_mid = (RING_OD + RING_ID) / 4
    wire_slot = box(5.0, 14.0, HOLDER_T + 1, RING_X + r_mid, 0, HOLDER_Z - 0.5)   # ring wires, towards the board
    holes = Manifold()
    for ang in (30, 150, 270):
        a = np.radians(ang)
        holes += cyl(HOLDER_T + 1, 1.4 + FIT / 2, HOLDER_Z - 0.5, x=RING_X + 23.0 * np.cos(a), y=23.0 * np.sin(a))
    return disc + shield - window - pocket - wire_slot - holes


def make_top():
    plate = rounded(OUT_X, OUT_Y, CORNER_R, TOP_T, Z_TOP_UNDER)
    lip = rounded(INNER_X - 2 * FIT, INNER_Y - 2 * FIT, CORNER_R - WALL - FIT, 3.0, Z_TOP_UNDER - 3.0) - \
        rounded(INNER_X - 2 * FIT - 2.4, INNER_Y - 2 * FIT - 2.4, max(CORNER_R - WALL - FIT - 1.2, 0.5), 4.0, Z_TOP_UNDER - 3.5)
    hole = cyl(TOP_T + 1, DIFF_R_OUT + FIT, Z_TOP_UNDER - 0.5, x=RING_X)
    return plate + lip - hole


def make_diffuser():
    band = cyl(TOP_T, DIFF_R_OUT, Z_TOP_UNDER, x=RING_X)
    flange = cyl(FLANGE_T, DIFF_FLANGE_R, Z_TOP_UNDER - FLANGE_T, x=RING_X)
    return band + flange - cyl(HEIGHT, SHIELD_ID / 2, 0, x=RING_X)


# ---------------- stand-ins for the bought parts (for checking only) ----------------
def make_dummies():
    ring = cyl(RING_T, RING_OD / 2, Z_RING, x=RING_X) - cyl(RING_T + 1, RING_ID / 2, Z_RING - 0.5, x=RING_X)
    pw, ph, pt = OLED_PCB
    oled_pcb = box(pw, ph, pt, RING_X, 0, HOLDER_Z - pt)
    oled_glass = box(*OLED_GLASS[:2], OLED_GLASS[2], RING_X, OLED_GLASS_DY, HOLDER_Z)
    oled_plugs = box(10.2, 2.6, PLUG_H, RING_X, ph / 2 - 1.5, HOLDER_Z - pt - PIN_BASE - PLUG_H)
    bw, bl, bt = BOARD
    board = box(bw, bl, bt, BOARD_X, BOARD_Y, Z_PCB) + box(18.0, 25.5, BOARD_UNDER, BOARD_X, BOARD_Y - 10, FLOOR)
    board_plugs = Manifold()
    for sx in (-1, 1):
        board_plugs += box(2.6, 38.1, PLUG_H, BOARD_X + sx * HEADER_PITCH_X / 2, BOARD_Y, Z_PCB + bt + PIN_BASE)
    usb_plug = box(11.0, 12.0, 7.5, BOARD_X, INNER_Y / 2 + 0.5 + 6.0, FLOOR + 1.9 - 3.75)   # the cable's plastic grip
    return {"LED ring": ring, "screen board": oled_pcb, "screen glass": oled_glass, "screen plugs": oled_plugs,
            "ESP32 board": board, "board plugs": board_plugs, "USB plug": usb_plug}


# ---------------- output ----------------
def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as f:
        f.write(b"AI Traffic Light case".ljust(80, b" "))
        f.write(np.uint32(len(t)).tobytes())
        f.write(rec.tobytes())


def check(parts, dummies):
    """Report every pair of parts that occupy the same space."""
    problems = []
    every = {**{f"printed {k}": v for k, v in parts.items()}, **dummies}
    names = list(every)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a.startswith("screen") and b.startswith("screen"):
                continue                       # the screen's own pieces touch by design
            vol = (every[a] ^ every[b]).volume()
            if vol > 0.5:
                problems.append(f"{a} overlaps {b} by {vol:.1f} mm3")
    return problems


def render(items, path, elev=22, azim=-60, title=None, cut_y=None):
    """Render with three.js in headless Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (skipping preview images: playwright is not installed)")
        return
    meshes = []
    for m, color, dz in items:
        if cut_y is not None:
            m = m - box(400, 200, 400, 0, cut_y - 100, -100)      # remove the half facing the viewer
        if m.is_empty():
            continue
        mesh = m.translate((0, 0, dz)).to_mesh()
        v = np.asarray(mesh.vert_properties)[:, :3].round(3)
        meshes.append({"v": v.ravel().tolist(), "t": np.asarray(mesh.tri_verts).ravel().tolist(), "c": color})
    html = RENDER_HTML.replace("__DATA__", json.dumps({"meshes": meshes, "elev": elev, "azim": azim,
                                                         "title": title or ""}))
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        page = b.new_page(viewport={"width": 860, "height": 600})
        page.goto(pathlib.Path(f.name).as_uri())
        page.wait_for_function("window.done === true", timeout=60000)
        page.screenshot(path=str(path))
        b.close()
    pathlib.Path(f.name).unlink()


RENDER_HTML = """<!doctype html><html><body style="margin:0;background:#fff;font-family:Segoe UI,Arial">
<div id="t" style="position:absolute;top:10px;width:100%;text-align:center;font-size:17px;color:#222"></div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"}}</script>
<script type="module">
import * as THREE from "three";
const D = __DATA__;
document.getElementById("t").textContent = D.title;
const r = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
r.setSize(860, 600); r.setClearColor(0xffffff); document.body.appendChild(r.domElement);
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 1.6));
const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(60, -90, 140); scene.add(sun);
const box = new THREE.Box3();
for (const m of D.meshes) {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(m.v, 3));
  g.setIndex(m.t);
  const ng = g.toNonIndexed(); ng.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({color:m.c, roughness:0.75, metalness:0.0, side:THREE.DoubleSide});
  const mesh = new THREE.Mesh(ng, mat); scene.add(mesh); box.expandByObject(mesh);
}
const c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3()).length();
const cam = new THREE.PerspectiveCamera(28, 860/600, 1, 5000);
const el = D.elev*Math.PI/180, az = D.azim*Math.PI/180, dist = s*2.0;
cam.up.set(0,0,1);
cam.position.set(c.x + dist*Math.cos(el)*Math.cos(az), c.y + dist*Math.cos(el)*Math.sin(az), c.z + dist*Math.sin(el));
cam.lookAt(c);
r.render(scene, cam);
window.done = true;
</script></body></html>"""


def main():
    here = pathlib.Path(__file__).resolve().parent
    (here / "stl").mkdir(exist_ok=True)
    (here / "previews").mkdir(exist_ok=True)
    parts = {"tray": make_tray(), "holder": make_holder(), "top": make_top(), "diffuser": make_diffuser()}
    dummies = make_dummies()
    for name, m in parts.items():
        write_stl(m, here / "stl" / f"{name}.stl")
        bb = m.bounding_box()
        print(f"{name:8} {bb[3]-bb[0]:5.1f} x {bb[4]-bb[1]:5.1f} x {bb[5]-bb[2]:5.1f} mm, "
              f"{m.volume()/1000:4.1f} cm3 of plastic")
    print(f"assembled box: {OUT_X:.0f} x {OUT_Y:.0f} x {HEIGHT:.1f} mm")

    problems = check(parts, dummies)
    print("collision check:", "OK, nothing overlaps" if not problems else "PROBLEMS")
    for p in problems:
        print("  ", p)

    dark, mid, white = "#34373c", "#55585e", "#f2f2ee"
    dcol = {"LED ring": "#2f7d3a", "screen board": "#1f4e8c", "screen glass": "#101418", "screen plugs": "#111111",
            "ESP32 board": "#22324a", "board plugs": "#111111", "USB plug": "#777777"}
    pcol = {"tray": dark, "holder": mid, "top": dark, "diffuser": white}
    no_usb = {k: v for k, v in dummies.items() if k != "USB plug"}
    assembled = [(m, pcol[k], 0) for k, m in parts.items()]
    inside = [(m, dcol[k], 0) for k, m in no_usb.items()]
    render(assembled, here / "previews" / "assembled.png", elev=32, azim=-62,
           title=f"Assembled: {OUT_X:.0f} x {OUT_Y:.0f} x {HEIGHT:.0f} mm")
    render(assembled + inside, here / "previews" / "section.png", elev=6, azim=-90, cut_y=0.0,
           title="Cut in half: screen and ring on the left, board on the right")
    lift = {"holder": 22, "top": 44, "diffuser": 56}
    up = {"LED ring", "screen board", "screen glass", "screen plugs"}
    render([(m, pcol[k], lift.get(k, 0)) for k, m in parts.items()]
           + [(m, dcol[k], 22 if k in up else 0) for k, m in no_usb.items()],
           here / "previews" / "exploded.png", elev=20, azim=-62, title="Exploded view")
    for name, m in parts.items():
        render([(m, pcol[name], 0)], here / "previews" / f"{name}.png", elev=35, azim=-62, title=name)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
