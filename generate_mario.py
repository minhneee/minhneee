import os
import json
import urllib.request
import random

def fetch_contributions(username, token):
    query = """
    query($userName:String!) {
      user(login: $userName){
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'userName': username}}).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    except Exception as e:
        print(f"Error fetching data from GitHub API: {e}")
        return []


# ─────────────────────────────────────────────
# SPRITE DEFINITIONS (pixel art in text form)
# ─────────────────────────────────────────────
MARIO_PIXELS = [
    "  RRRRR   ",
    " RRRRRRRRR",
    " BBOOOS   ",
    " BOSSSSOOO",
    " BOSSSSOO ",
    "  BOSSOO  ",
    "  RROORRR ",
    " RRROORRRR",
    " RRRORRRRR",
    " SRRRRRYSS",
    " SSS  SSS ",
    "BBBB  BBBB",
]
MARIO_COLORS = {
    'R': '#e52521', 'S': '#ffcca6',
    'B': '#8B4513', 'O': '#2038ec', 'Y': '#f8d820'
}

GOOMBA_PIXELS = [
    "  BBBBB  ",
    " BBBBBBB ",
    " BEEBEBBB",
    "BBEEBBBEE",
    " BEEBEBBB",
    "BBBBBBBBB",
    " BBBBBBB ",
    "  BB  BB ",
]
GOOMBA_COLORS = {'B': '#8B4513', 'E': '#000000', 'e': '#FFFFFF'}

QUESTION_PIXELS = [
    "OOOOOOOOOO",
    "O        O",
    "O   QQ   O",
    "O  QQQQQ O",
    "O    QQ  O",
    "O   QQ   O",
    "O        O",
    "O   QQ   O",
    "O        O",
    "OOOOOOOOOO",
]
QUESTION_COLORS = {'O': '#c84c0c', 'Q': '#f8d820', ' ': '#e89040'}

COIN_PIXELS = [
    " YYY ",
    "YYYYYY",
    "YOOOOY",
    "YOOOOY",
    "YOOOOY",
    "YYYYYY",
    " YYY ",
]
COIN_COLORS = {'Y': '#f8d820', 'O': '#d8a000'}

STAR_PIXELS = [
    "  Y  ",
    "YYYYY",
    " YYY ",
    "  Y  ",
    " Y Y ",
]
STAR_COLORS = {'Y': '#f8d820'}


def make_sprite_svg(sprite_id, pixels, colors, scale):
    """Returns the <g id="sprite_id">...</g> SVG string."""
    lines = [f'  <g id="{sprite_id}">']
    for row_idx, row in enumerate(pixels):
        for col_idx, ch in enumerate(row):
            if ch in colors:
                x = col_idx * scale
                y = row_idx * scale
                lines.append(
                    f'    <rect x="{x:.1f}" y="{y:.1f}" '
                    f'width="{scale}" height="{scale}" '
                    f'fill="{colors[ch]}" />'
                )
    lines.append('  </g>')
    return "\n".join(lines)


# ─────────────────────────────────────────────
# MAIN SVG GENERATOR
# ─────────────────────────────────────────────
def generate_mario_github_svg(filename="mario_contribution.svg"):
    username = os.environ.get("GITHUB_ACTOR", "User")
    token    = os.environ.get("GITHUB_TOKEN")

    weeks_data = fetch_contributions(username, token) if token else []

    # ── Layout constants ──────────────────────────────────────────
    CELL    = 10          # contribution cell size
    GAP     = 4           # gap between cells
    STEP    = CELL + GAP  # total step per column
    ROWS    = 7
    COLS    = len(weeks_data) if weeks_data else 53

    GRID_X  = 50          # left offset for the grid
    TOP_PAD = 50          # sky above the grid
    SPRITE_SCALE = 1.5    # Mario pixel scale

    # Derived positions
    GRID_W   = COLS * STEP
    GRID_H   = ROWS * STEP
    GROUND_Y = TOP_PAD + GRID_H          # y of ground surface
    HEIGHT   = GROUND_Y + 35             # total SVG height

    FLAG_X   = GRID_X + GRID_W + 20
    CASTLE_X = FLAG_X + 45
    WIDTH    = CASTLE_X + 75

    MARIO_H  = len(MARIO_PIXELS) * SPRITE_SCALE   # sprite height in px
    MARIO_W  = max(len(r) for r in MARIO_PIXELS) * SPRITE_SCALE

    # Duration of the full animation loop (seconds)
    DURATION = 28

    level_map = {
        'NONE':             'empty',
        'FIRST_QUARTILE':   'lvl1',
        'SECOND_QUARTILE':  'lvl2',
        'THIRD_QUARTILE':   'lvl3',
        'FOURTH_QUARTILE':  'lvl4',
    }

    # ── Collect contribution data ─────────────────────────────────
    # For each column, find highest (topmost) filled row + coins
    col_data = []       # list of (highest_row 0-based, [coin_rows])
    for week in weeks_data:
        highest = ROWS
        coin_rows = []
        for row_idx, day in enumerate(week['contributionDays']):
            lvl = level_map.get(day.get('contributionLevel', 'NONE'), 'empty')
            if lvl != 'empty' and row_idx < highest:
                highest = row_idx
            if lvl == 'lvl4':
                coin_rows.append(row_idx)
        col_data.append((highest, coin_rows))

    # Fallback demo data when no API data
    if not weeks_data:
        demo = []
        for c in range(53):
            h = ROWS if c % 5 == 0 else (c % ROWS)
            coins = [h] if c % 7 == 0 and h < ROWS else []
            demo.append((h, coins))
        col_data = demo
        COLS = 53

    # ── Build Mario's path ─────────────────────────────────────────
    # Path points: list of (x, y) where y is the BOTTOM of Mario feet
    pipe_x    = 8
    pipe_top  = GROUND_Y - 32
    start_x   = pipe_x + 12
    start_y   = pipe_top - MARIO_H   # Mario appears above pipe

    path_points = [(start_x, start_y)]

    # Obstacles we'll place: goombas and question blocks
    obstacles  = []   # (x, y, kind)  kind = 'goomba'|'qblock'
    coins_info = []   # (cx, cy, t_appear, t_collect)

    QBLOCK_SIZE = 10
    
    # Decide obstacle positions – every ~8 weeks if empty stretch
    empty_run = 0

    for col_idx in range(COLS):
        highest_row, coin_rows = col_data[col_idx]
        col_x  = GRID_X + col_idx * STEP

        # Mario's target y: stand on top of highest block (or ground)
        if highest_row < ROWS:
            target_y = TOP_PAD + highest_row * STEP - MARIO_H
        else:
            target_y = GROUND_Y - MARIO_H   # ground level

        prev_x, prev_y = path_points[-1]

        # ── Question blocks above lvl4 columns ──
        if coin_rows and (not obstacles or col_x - obstacles[-1][0] > 30):
            qb_y = TOP_PAD + min(coin_rows) * STEP - QBLOCK_SIZE - 20
            obstacles.append((col_x + CELL // 2, qb_y, 'qblock'))
            # Coin that pops from the block
            coins_info.append({
                'x': col_x + CELL // 2 - 4,
                'y': qb_y - 12,
                'col': col_idx,
            })

        # ── Goomba on ground-level empty columns ──
        if highest_row == ROWS and empty_run > 2 and \
                (not obstacles or col_x - obstacles[-1][0] > 50):
            goomba_h = len(GOOMBA_PIXELS) * SPRITE_SCALE
            obstacles.append((col_x, GROUND_Y - goomba_h, 'goomba'))
            empty_run = 0

        # Jump if height changes significantly
        if abs(target_y - prev_y) > 5:
            mid_x = prev_x + (col_x - prev_x) / 2
            apex_y = min(prev_y, target_y) - 22
            path_points.append((mid_x, apex_y))

        path_points.append((col_x, target_y))

        if highest_row == ROWS:
            empty_run += 1
        else:
            empty_run = 0

    # ── End path: jump to flagpole, slide, enter castle ──
    flag_top  = TOP_PAD - 15
    flag_pole = FLAG_X

    px, py = path_points[-1]
    # Jump arc to flagpole top
    path_points.append(((px + flag_pole) / 2, py - 35))
    path_points.append((flag_pole - 4, flag_top + 8))
    # Slide down pole
    path_points.append((flag_pole - 4, GROUND_Y - MARIO_H))
    # Walk into castle
    path_points.append((CASTLE_X + 18, GROUND_Y - MARIO_H))

    # ── Compute timing per path point ─────────────────────────────
    # Assign time [0..1] proportional to x-distance
    distances = [0.0]
    for i in range(1, len(path_points)):
        dx = path_points[i][0] - path_points[i-1][0]
        dy = path_points[i][1] - path_points[i-1][1]
        distances.append(distances[-1] + (dx**2 + dy**2)**0.5)
    total_dist = distances[-1] or 1
    times = [d / total_dist for d in distances]

    def t_at_x(target_x):
        """Interpolate time fraction when Mario's x == target_x."""
        for i in range(1, len(path_points)):
            x0, _ = path_points[i-1]
            x1, _ = path_points[i]
            if x0 <= target_x <= x1:
                frac = (target_x - x0) / (x1 - x0 + 0.001)
                return times[i-1] + frac * (times[i] - times[i-1])
        return times[-1]

    # ── Build keyTimes/keyValues strings for animateMotion ────────
    kx = ";".join(f"{x:.1f}" for x, y in path_points)
    ky = ";".join(f"{y:.1f}" for x, y in path_points)
    kt = ";".join(f"{t:.4f}" for t in times)

    # ── Compute coin timing ───────────────────────────────────────
    for ci in coins_info:
        ci['t_show']    = t_at_x(ci['x'])
        ci['t_collect'] = min(1.0, ci['t_show'] + 0.04)

    # Flag drop timing
    t_flag_arrive = t_at_x(flag_pole)
    t_flag_done   = min(1.0, t_flag_arrive + 0.06)
    t_castle      = min(1.0, t_flag_done + 0.08)

    # ── START BUILDING SVG ────────────────────────────────────────
    svg = []

    # Header
    svg.append(f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
               f'xmlns="http://www.w3.org/2000/svg" '
               f'style="font-family:monospace;">')

    # ── CSS styles ────────────────────────────────────────────────
    svg.append("""<style>
  .bg     { fill: #5c94fc; }
  .empty  { fill: rgba(255,255,255,0.12); rx:2; ry:2; }
  .lvl1   { fill: #0e4429; rx:2; ry:2; }
  .lvl2   { fill: #006d32; rx:2; ry:2; }
  .lvl3   { fill: #26a641; rx:2; ry:2; }
  .lvl4   { fill: #39d353; rx:2; ry:2; }
  .ground { fill: #5C3317; }
  .ground-stripe { fill: #7a4520; }
  .brick  { fill: #c84c0c; stroke:#000; stroke-width:0.4; }
  .pipe   { fill: #00a800; stroke:#000; stroke-width:0.6; }
  .pipe-top { fill: #00d000; stroke:#000; stroke-width:0.6; }
</style>""")

    # ── Sprite defs ───────────────────────────────────────────────
    svg.append('<defs>')
    svg.append(make_sprite_svg('spr_mario',    MARIO_PIXELS,    MARIO_COLORS,    SPRITE_SCALE))
    svg.append(make_sprite_svg('spr_goomba',   GOOMBA_PIXELS,   GOOMBA_COLORS,   SPRITE_SCALE))
    svg.append(make_sprite_svg('spr_question', QUESTION_PIXELS, QUESTION_COLORS, SPRITE_SCALE * 0.95))
    svg.append(make_sprite_svg('spr_coin',     COIN_PIXELS,     COIN_COLORS,     1.4))
    svg.append(make_sprite_svg('spr_star',     STAR_PIXELS,     STAR_COLORS,     1.5))
    svg.append('</defs>')

    # ── Background sky ───────────────────────────────────────────
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" class="bg"/>')

    # Drifting clouds (pure SVG, no external assets)
    cloud_shapes = [
        # (rel positions of ellipses: cx, cy, rx, ry)
        [(0,0,22,12),(20,-8,18,10),(-18,-6,16,9),(2,10,28,10)],
        [(0,0,18,9),(15,-6,14,8),(-14,-5,13,7),(2,8,22,8)],
        [(0,0,26,13),(22,-9,20,11),(-20,-7,18,10),(3,11,30,11)],
    ]
    cloud_colors = ['#ffffffcc','#f0f0f0cc']
    cloud_y_positions = [8, 22, 14]
    cloud_speeds      = [35, 50, 45]
    cloud_start_xs    = [WIDTH*0.1, WIDTH*0.55, WIDTH*0.35]

    for i, (shape, cy, spd, sx) in enumerate(
        zip(cloud_shapes, cloud_y_positions, cloud_speeds, cloud_start_xs)
    ):
        svg.append(f'<g opacity="0.85">')
        svg.append(f'  <animateTransform attributeName="transform" type="translate"'
                   f' from="{sx} 0" to="{-120} 0"'
                   f' dur="{spd}s" repeatCount="indefinite" begin="{i*-spd/3:.1f}s"/>')
        for cx, ely, rx, ry in shape:
            svg.append(f'  <ellipse cx="{cx}" cy="{cy + ely}" rx="{rx}" ry="{ry}" '
                       f'fill="{cloud_colors[i % 2]}" stroke="#ccc" stroke-width="0.3"/>')
        svg.append('</g>')

    # ── Ground ────────────────────────────────────────────────────
    svg.append(f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="{HEIGHT - GROUND_Y}" class="ground"/>')
    # Brick stripe on ground
    brick_h = 7
    bw = 28
    for bx in range(0, WIDTH, bw):
        svg.append(f'<rect x="{bx}" y="{GROUND_Y}" width="{bw - 1}" height="{brick_h}" class="brick"/>')
    for bx in range(bw//2, WIDTH, bw):
        svg.append(f'<rect x="{bx}" y="{GROUND_Y + brick_h}" width="{bw - 1}" height="{brick_h}" class="brick"/>')

    # Bushes
    bush_positions = list(range(20, WIDTH - 60, 110))
    random.seed(42)
    for bx in bush_positions:
        bh = random.choice([14, 18, 12])
        bw2 = random.choice([30, 42, 25])
        svg.append(f'<ellipse cx="{bx + bw2//2}" cy="{GROUND_Y - bh//2}" rx="{bw2//2}" ry="{bh//2}" '
                   f'fill="#00a800" opacity="0.9"/>')
        svg.append(f'<ellipse cx="{bx + bw2//2 - bw2//4}" cy="{GROUND_Y - bh//2 - 4}" rx="{bw2//3}" ry="{bh//3}" '
                   f'fill="#00c800" opacity="0.9"/>')
        svg.append(f'<ellipse cx="{bx + bw2//2 + bw2//4}" cy="{GROUND_Y - bh//2 - 3}" rx="{bw2//3}" ry="{bh//3}" '
                   f'fill="#00c800" opacity="0.9"/>')

    # ── Start warp pipe ───────────────────────────────────────────
    svg.append(f'<rect x="{pipe_x}" y="{pipe_top + 10}" width="26" height="{GROUND_Y - pipe_top - 10}" class="pipe"/>')
    svg.append(f'<rect x="{pipe_x - 3}" y="{pipe_top}" width="32" height="12" class="pipe-top"/>')
    # Shading
    svg.append(f'<rect x="{pipe_x + 4}" y="{pipe_top + 10}" width="4" height="{GROUND_Y - pipe_top - 10}" fill="#00d000" opacity="0.3"/>')

    # ── Contribution grid cells ───────────────────────────────────
    svg.append(f'<!-- contribution grid -->')
    for col_idx, week in enumerate(weeks_data if weeks_data else []):
        cx = GRID_X + col_idx * STEP
        for row_idx, day in enumerate(week['contributionDays']):
            lvl = level_map.get(day.get('contributionLevel', 'NONE'), 'empty')
            cy = TOP_PAD + row_idx * STEP
            rx = 2
            svg.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="{rx}" ry="{rx}" class="{lvl}"/>')

    if not weeks_data:
        # Demo grid for visual testing
        random.seed(7)
        for col_idx in range(53):
            cx = GRID_X + col_idx * STEP
            for row_idx in range(7):
                lvl = random.choice(['empty', 'empty', 'lvl1', 'lvl2', 'lvl3', 'lvl4'])
                cy = TOP_PAD + row_idx * STEP
                svg.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" ry="2" class="{lvl}"/>')

    # ── Static obstacles & blocks ─────────────────────────────────
    for ox, oy, kind in obstacles:
        if kind == 'goomba':
            # Goomba with idle bounce animation
            svg.append(f'<g transform="translate({ox},{oy})">')
            svg.append(f'  <use href="#spr_goomba">')
            svg.append(f'    <animateTransform attributeName="transform" type="translate"'
                       f' values="0,0;0,-3;0,0" dur="0.6s" repeatCount="indefinite"/>')
            svg.append(f'  </use>')
            svg.append(f'</g>')
        elif kind == 'qblock':
            # Question block with bump animation
            svg.append(f'<g transform="translate({ox},{oy})">')
            svg.append(f'  <use href="#spr_question">')
            svg.append(f'    <animateTransform attributeName="transform" type="translate"'
                       f' values="0,0;0,-2;0,0" dur="0.4s" repeatCount="indefinite"/>')
            svg.append(f'  </use>')
            svg.append(f'</g>')

    # ── Coins that pop & get collected ────────────────────────────
    for ci in coins_info:
        ts  = ci['t_show']
        tc  = ci['t_collect']
        cx  = ci['x']
        cy  = ci['y']

        # Coin is visible before Mario arrives; it flies up then disappears
        svg.append(f'<g>')
        svg.append(f'  <!-- coin at ({cx:.0f},{cy:.0f}) ts={ts:.3f} tc={tc:.3f} -->')
        # Translate: coin pops up 14px when Mario hits it
        svg.append(f'  <animateTransform attributeName="transform" type="translate"'
                   f' values="{cx},{cy};{cx},{cy};{cx},{cy - 14};{cx},{cy - 14}"'
                   f' keyTimes="0;{ts:.4f};{tc:.4f};1"'
                   f' dur="{DURATION}s" repeatCount="indefinite"/>')
        # Opacity: visible, then gone when collected
        svg.append(f'  <use href="#spr_coin">')
        svg.append(f'    <animate attributeName="opacity"'
                   f' values="1;1;0;0"'
                   f' keyTimes="0;{ts:.4f};{tc:.4f};1"'
                   f' dur="{DURATION}s" repeatCount="indefinite"/>')
        # Spin: coin rotates on collection
        svg.append(f'    <animateTransform attributeName="transform" type="scale"'
                   f' values="1,1;1,1;0.1,1;0.1,1"'
                   f' keyTimes="0;{ts:.4f};{tc:.4f};1"'
                   f' dur="{DURATION}s" repeatCount="indefinite" additive="sum"/>')
        svg.append(f'  </use>')
        svg.append(f'</g>')

    # Scattered bonus stars in the sky (twinkling)
    star_xs = [60, 180, 310, 450, 580, 710, 820]
    star_ys = [6, 12, 8, 14, 5, 10, 7]
    for i, (sx, sy) in enumerate(zip(star_xs, star_ys)):
        delay = i * 0.7
        svg.append(f'<g transform="translate({sx},{sy})">')
        svg.append(f'  <use href="#spr_star" opacity="0.0">')
        svg.append(f'    <animate attributeName="opacity" values="0;0.8;0" dur="3s" begin="{delay}s" repeatCount="indefinite"/>')
        svg.append(f'    <animateTransform attributeName="transform" type="scale" values="0.5;1;0.5" dur="3s" begin="{delay}s" repeatCount="indefinite"/>')
        svg.append(f'  </use>')
        svg.append(f'</g>')

    # ── Flagpole ──────────────────────────────────────────────────
    flag_pole_h = GROUND_Y - flag_top
    svg.append(f'<rect x="{flag_pole}" y="{flag_top}" width="3" height="{flag_pole_h}" fill="#e0e0e0" stroke="#888" stroke-width="0.5"/>')
    svg.append(f'<circle cx="{flag_pole + 1.5}" cy="{flag_top}" r="5" fill="#f8d820" stroke="#a06000"/>')

    # Flag that drops when Mario arrives
    flag_drop_dist = flag_pole_h - 18
    svg.append(f'<g id="flag">')
    svg.append(f'  <animateTransform attributeName="transform" type="translate"'
               f' values="0,0;0,0;0,{flag_drop_dist};0,{flag_drop_dist}"'
               f' keyTimes="0;{t_flag_arrive:.4f};{t_flag_done:.4f};1"'
               f' dur="{DURATION}s" repeatCount="indefinite"/>')
    svg.append(f'  <polygon points="{flag_pole - 18},{flag_top + 3} {flag_pole},{flag_top + 3} {flag_pole},{flag_top + 18}" fill="#00a800" stroke="#004400" stroke-width="0.5"/>')
    svg.append(f'</g>')

    # ── Castle ────────────────────────────────────────────────────
    cx0 = CASTLE_X
    cy0 = GROUND_Y - 45
    # Main body
    svg.append(f'<rect x="{cx0}" y="{cy0}" width="60" height="{GROUND_Y - cy0}" fill="#c84c0c" stroke="#000" stroke-width="0.8"/>')
    # Battlements
    for bx in [0, 10, 20, 30, 40, 50]:
        svg.append(f'<rect x="{cx0 + bx}" y="{cy0 - 10}" width="8" height="12" fill="#c84c0c" stroke="#000" stroke-width="0.8"/>')
    # Windows
    svg.append(f'<rect x="{cx0 + 8}" y="{cy0 + 6}" width="10" height="10" fill="#f8d820" stroke="#000" stroke-width="0.5" rx="1"/>')
    svg.append(f'<rect x="{cx0 + 42}" y="{cy0 + 6}" width="10" height="10" fill="#f8d820" stroke="#000" stroke-width="0.5" rx="1"/>')
    # Door (arched)
    svg.append(f'<path d="M {cx0 + 22} {GROUND_Y} L {cx0 + 22} {cy0 + 24} A 8 8 0 0 1 {cx0 + 38} {cy0 + 24} L {cx0 + 38} {GROUND_Y} Z" fill="#000"/>')
    # Castle flag
    svg.append(f'<rect x="{cx0 + 28}" y="{cy0 - 22}" width="2" height="16" fill="#888"/>')
    svg.append(f'<polygon points="{cx0 + 30},{cy0 - 22} {cx0 + 42},{cy0 - 16} {cx0 + 30},{cy0 - 10}" fill="#e52521"/>')

    # ── "LEVEL CLEAR!" text ───────────────────────────────────────
    text_x = flag_pole - 55
    text_y = flag_top - 8
    svg.append(f'<text x="{text_x}" y="{text_y}" font-family="monospace" font-weight="bold"'
               f' font-size="14" fill="#f8d820" stroke="#000" stroke-width="1.2" opacity="0">')
    svg.append(f'  LEVEL CLEAR!')
    t_text_end = min(1.0, t_flag_done + 0.04)
    svg.append(f'  <animate attributeName="opacity"'
               f' values="0;0;1;1;1;0"'
               f' keyTimes="0;{t_flag_done:.4f};{t_text_end:.4f};0.9;0.97;1"'
               f' dur="{DURATION}s" repeatCount="indefinite"/>')
    svg.append(f'</text>')

    # ── Mario's animated motion ───────────────────────────────────
    # Build animateMotion path
    # Using values= with x;y pairs via separate animate on a <g>
    # We'll use <animateMotion> with calcMode="linear" for smoother arcs

    svg.append('<!-- MARIO -->')
    svg.append('<g id="mario-runner">')
    svg.append(f'  <animate attributeName="x"'
               f' values="{kx}"'
               f' keyTimes="{kt}"'
               f' dur="{DURATION}s" repeatCount="indefinite" calcMode="spline"'
               f' keySplines="' + ";".join(["0.4 0 0.6 1"] * (len(path_points)-1)) + '"/>')
    svg.append(f'  <animate attributeName="y"'
               f' values="{ky}"'
               f' keyTimes="{kt}"'
               f' dur="{DURATION}s" repeatCount="indefinite" calcMode="spline"'
               f' keySplines="' + ";".join(["0.4 0 0.6 1"] * (len(path_points)-1)) + '"/>')

    # Mario sprite inside group – use animateTransform for position
    # Actually since SVG <animate> on x/y of a <g> doesn't work in all renderers,
    # use animateMotion with an explicit path string
    svg.append('</g>')

    # Build SVG path string from path_points
    if path_points:
        path_d = f"M {path_points[0][0]:.1f} {path_points[0][1]:.1f}"
        for i in range(1, len(path_points)):
            x0, y0 = path_points[i-1]
            x1, y1 = path_points[i]
            # Use quadratic bezier for jumps (when y changes a lot)
            if abs(y1 - y0) > 5:
                cpx = x0 + (x1 - x0) * 0.5
                cpy = min(y0, y1) - 18
                path_d += f" Q {cpx:.1f} {cpy:.1f} {x1:.1f} {y1:.1f}"
            else:
                path_d += f" L {x1:.1f} {y1:.1f}"

    svg.append(f'<path id="mp" d="{path_d}" fill="none" stroke="none"/>')
    svg.append(f'<use href="#spr_mario">')
    svg.append(f'  <animateMotion dur="{DURATION}s" repeatCount="indefinite" rotate="0" calcMode="spline"'
               f' keyTimes="{kt}"'
               f' keySplines="' + ";".join(["0.3 0 0.7 1"] * (len(path_points)-1)) + '">')
    svg.append(f'    <mpath href="#mp"/>')
    svg.append(f'  </animateMotion>')
    svg.append(f'</use>')

    # ── Score counter HUD ─────────────────────────────────────────
    svg.append(f'<text x="10" y="14" font-family="monospace" font-size="10" fill="#f8d820" font-weight="bold">MARIO</text>')
    svg.append(f'<text x="10" y="24" font-family="monospace" font-size="10" fill="#ffffff">x{len(coins_info):02d} coins</text>')
    svg.append(f'<text x="{WIDTH//2 - 20}" y="14" font-family="monospace" font-size="10" fill="#f8d820" font-weight="bold">WORLD</text>')
    svg.append(f'<text x="{WIDTH//2 - 12}" y="24" font-family="monospace" font-size="10" fill="#ffffff">1-1</text>')
    svg.append(f'<text x="{WIDTH - 65}" y="14" font-family="monospace" font-size="10" fill="#f8d820" font-weight="bold">TIME</text>')
    svg.append(f'<text x="{WIDTH - 58}" y="24" font-family="monospace" font-size="10" fill="#ffffff">  400</text>')

    svg.append('</svg>')

    content = "\n".join(svg)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK  Generated {filename}  ({len(content):,} bytes, "
          f"{COLS} weeks, {len(coins_info)} coins, {len(obstacles)} obstacles)")


if __name__ == "__main__":
    generate_mario_github_svg()
