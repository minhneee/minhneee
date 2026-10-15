import os
import json
import urllib.request
import re

def fetch_contributions(username, token=None):
    """
    Fetch contribution weeks for username.
    1. Try GraphQL if token provided.
    2. Try public contributions API.
    3. Fallback to cached minhneee contribution data.
    """
    if token:
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
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
        except Exception as e:
            print(f"GraphQL API error: {e}, falling back to public API...")

    # Fallback to public contributions API
    try:
        url = f"https://github-contributions-api.jogruber.de/v4/{username}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            days_raw = data.get('contributions', [])
            if days_raw:
                # Group days into weeks of 7
                # Take the last 53 * 7 days (last year)
                recent_days = days_raw[-371:] if len(days_raw) >= 371 else days_raw
                level_trans = {
                    0: 'NONE',
                    1: 'FIRST_QUARTILE',
                    2: 'SECOND_QUARTILE',
                    3: 'THIRD_QUARTILE',
                    4: 'FOURTH_QUARTILE'
                }
                weeks = []
                cur_week = []
                for d in recent_days:
                    lvl = level_trans.get(d.get('level', 0), 'NONE')
                    cur_week.append({'contributionLevel': lvl})
                    if len(cur_week) == 7:
                        weeks.append({'contributionDays': cur_week})
                        cur_week = []
                if cur_week:
                    weeks.append({'contributionDays': cur_week})
                return weeks
    except Exception as e:
        print(f"Public API error: {e}, using local cached dataset...")

    # Local fallback representing minhneee's active commit profile
    # 53 weeks x 7 days
    weeks = []
    active_cells = {
        (14, 6): 'SECOND_QUARTILE',
        (15, 0): 'SECOND_QUARTILE',
        (15, 6): 'SECOND_QUARTILE',
        (22, 3): 'SECOND_QUARTILE',
        (26, 4): 'SECOND_QUARTILE',
        (33, 0): 'THIRD_QUARTILE',
        (52, 4): 'FOURTH_QUARTILE',
    }
    for w in range(53):
        days = []
        for d in range(7):
            lvl = active_cells.get((w, d), 'NONE')
            days.append({'contributionLevel': lvl})
        weeks.append({'contributionDays': days})
    return weeks


# ─────────────────────────────────────────────
# SPRITE DEFINITIONS  (8-bit pixel art)
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
    """Generates an SVG <g id="..."> for pixel sprite."""
    lines = [f'  <g id="{sprite_id}">']
    for r_idx, row in enumerate(pixels):
        for c_idx, ch in enumerate(row):
            if ch in colors:
                x = c_idx * scale
                y = r_idx * scale
                lines.append(
                    f'    <rect x="{x:.1f}" y="{y:.1f}" '
                    f'width="{scale}" height="{scale}" '
                    f'fill="{colors[ch]}" />'
                )
    lines.append('  </g>')
    return "\n".join(lines)


# ─────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────
def generate_mario_github_svg(filename="mario_contribution.svg"):
    username = os.environ.get("GITHUB_ACTOR", "minhneee")
    token    = os.environ.get("GITHUB_TOKEN")

    weeks_data = fetch_contributions(username, token)

    # ── Dimensions & Grid layout ───────────────────────────────────
    CELL         = 10
    GAP          = 4
    STEP         = CELL + GAP
    ROWS         = 7
    COLS         = len(weeks_data) if weeks_data else 53
    GRID_X       = 50
    TOP_PAD      = 50
    SPRITE_SCALE = 1.5

    GRID_W   = COLS * STEP
    GRID_H   = ROWS * STEP
    GROUND_Y = TOP_PAD + GRID_H
    HEIGHT   = GROUND_Y + 35

    FLAG_X   = GRID_X + GRID_W + 20
    CASTLE_X = FLAG_X + 45
    WIDTH    = CASTLE_X + 75

    MARIO_H  = len(MARIO_PIXELS) * SPRITE_SCALE
    MARIO_W  = max(len(r) for r in MARIO_PIXELS) * SPRITE_SCALE

    DURATION = 28.0  # seconds per loop

    level_map = {
        'NONE':             'empty',
        'FIRST_QUARTILE':   'lvl1',
        'SECOND_QUARTILE':  'lvl2',
        'THIRD_QUARTILE':   'lvl3',
        'FOURTH_QUARTILE':  'lvl4',
    }

    # ── Parse week data ───────────────────────────────────────────
    col_info = []
    for week in weeks_data:
        highest_row = ROWS
        has_commit  = False
        for r_idx, day in enumerate(week['contributionDays']):
            lvl = level_map.get(day.get('contributionLevel', 'NONE'), 'empty')
            if lvl != 'empty':
                has_commit = True
                if r_idx < highest_row:
                    highest_row = r_idx
        col_info.append((highest_row, has_commit))

    # ── Configure Question Blocks + Coins & Goombas ───────────────
    # Requirement: "giảm bớt quái lại 1,3 con thôi" -> strictly 2 Goombas
    # Requirement: "mỗi lần reset lại hãy làm lại tất cả kể cả tiền vàng" -> clean loop reset
    
    # 1. Question Blocks + Coins:
    # Place on active commit columns, plus bonus blocks at scenic spots so Mario collects ~7-8 coins
    qblocks = []  # list of dicts: {'x': ..., 'y': ..., 'col': ...}
    
    # Identify candidate columns for question blocks
    candidate_cols = []
    for c_idx, (h_row, has_c) in enumerate(col_info):
        if has_c:
            candidate_cols.append(c_idx)

    # If few active columns, supplement with scenic milestone columns across the level
    scenic_milestones = [6, 18, 30, 40]
    for sc in scenic_milestones:
        if sc < COLS and sc not in candidate_cols:
            candidate_cols.append(sc)
    candidate_cols.sort()

    # Filter candidates to ensure at least 28px separation
    last_qx = -100
    for c_idx in candidate_cols:
        cx = GRID_X + c_idx * STEP
        if cx - last_qx >= 28:
            h_row = col_info[c_idx][0]
            if h_row < ROWS:
                # Above the highest commit cell
                qy = TOP_PAD + h_row * STEP - 22
            else:
                # Floating at standard jump height above ground
                qy = GROUND_Y - MARIO_H - 26
            qblocks.append({'col': c_idx, 'x': cx + CELL // 2, 'y': qy})
            last_qx = cx

    # 2. Goombas (strictly 2 Goombas, well separated on empty stretches)
    goombas = []
    # Two well-spaced Goombas at Week 12 and Week 36
    goomba_candidates = [12, 36]
    for gc in goomba_candidates:
        if gc < COLS and gc not in [qb['col'] for qb in qblocks]:
            gx = GRID_X + gc * STEP
            goomba_h = len(GOOMBA_PIXELS) * SPRITE_SCALE
            goombas.append({'col': gc, 'x': gx, 'y': GROUND_Y - goomba_h})

    # ── Build Mario Path Points ───────────────────────────────────
    pipe_x   = 8
    pipe_top = GROUND_Y - 32
    start_x  = pipe_x + 12
    start_y  = pipe_top - MARIO_H

    path_points = [(start_x, start_y)]

    # Map obstacles by column for path planning
    qb_by_col = {qb['col']: qb for qb in qblocks}
    gb_by_col = {gb['col']: gb for gb in goombas}

    for c_idx in range(COLS):
        cx = GRID_X + c_idx * STEP
        h_row, has_c = col_info[c_idx]

        if h_row < ROWS:
            ground_or_block_y = TOP_PAD + h_row * STEP - MARIO_H
        else:
            ground_or_block_y = GROUND_Y - MARIO_H

        prev_x, prev_y = path_points[-1]

        # Case A: Question block in this column -> Mario jumps up to hit it!
        if c_idx in qb_by_col:
            qb = qb_by_col[c_idx]
            # Jump up to hit question block
            hit_y = qb['y'] + 15
            path_points.append((cx - 4, prev_y))
            path_points.append((cx, hit_y))
            path_points.append((cx + 6, ground_or_block_y))

        # Case B: Goomba in this column -> Mario jumps high over Goomba!
        elif c_idx in gb_by_col:
            jump_apex = GROUND_Y - MARIO_H - 26
            path_points.append((cx - 8, GROUND_Y - MARIO_H))
            path_points.append((cx, jump_apex))
            path_points.append((cx + 8, GROUND_Y - MARIO_H))

        # Case C: Standard column - hop onto block or run on ground
        else:
            if abs(ground_or_block_y - prev_y) > 4:
                mid_x = (prev_x + cx) / 2
                apex_y = min(prev_y, ground_or_block_y) - 16
                path_points.append((mid_x, apex_y))
            path_points.append((cx, ground_or_block_y))

    # ── End Path: Jump to Flagpole -> Slide -> Enter Castle ────────
    flag_top  = TOP_PAD - 15
    flag_pole = FLAG_X

    last_px, last_py = path_points[-1]
    # Leap to flagpole
    path_points.append(((last_px + flag_pole) / 2, flag_top + 10))
    # Grab pole
    path_points.append((flag_pole - 4, flag_top + 12))
    # Slide down pole
    path_points.append((flag_pole - 4, GROUND_Y - MARIO_H))
    # Jump off pole
    path_points.append((flag_pole + 12, GROUND_Y - MARIO_H))
    # Enter castle doorway
    path_points.append((CASTLE_X + 28, GROUND_Y - MARIO_H))
    # Pause inside castle
    path_points.append((CASTLE_X + 28, GROUND_Y - MARIO_H))

    # ── Timing Calculations ───────────────────────────────────────
    distances = [0.0]
    for i in range(1, len(path_points)):
        dx = path_points[i][0] - path_points[i-1][0]
        dy = path_points[i][1] - path_points[i-1][1]
        distances.append(distances[-1] + (dx**2 + dy**2) ** 0.5)
    total_dist = distances[-1] or 1.0

    # Distribute 92% of duration for travel, 8% for castle celebration pause
    times = [(d / total_dist) * 0.92 for d in distances]
    times[-1] = 1.0  # hold end inside castle until loop reset

    def t_at_x(target_x):
        for i in range(1, len(path_points)):
            x0 = path_points[i-1][0]
            x1 = path_points[i][0]
            if x0 <= target_x <= x1:
                frac = (target_x - x0) / max(x1 - x0, 0.001)
                return times[i-1] + frac * (times[i] - times[i-1])
        return times[-2]

    # Pre-calculate timings for each interactive element
    for qb in qblocks:
        qb['t_hit']     = t_at_x(qb['x'])
        qb['t_collect'] = min(0.91, qb['t_hit'] + 0.022)

    for gb in goombas:
        gb['t_stomp']   = t_at_x(gb['x'])
        gb['t_fade']    = min(0.91, gb['t_stomp'] + 0.02)

    t_flag_arrive = t_at_x(flag_pole - 4)
    # Find slide done time
    t_flag_done   = min(0.91, t_flag_arrive + 0.035)
    t_castle_door = t_at_x(CASTLE_X + 28)

    # ── Build Bezier / Linear Path String for animateMotion ────────
    path_d = f"M {path_points[0][0]:.1f} {path_points[0][1]:.1f}"
    for i in range(1, len(path_points)):
        x0, y0 = path_points[i-1]
        x1, y1 = path_points[i]
        if abs(y1 - y0) > 6:
            cpx = (x0 + x1) * 0.5
            cpy = min(y0, y1) - 14
            path_d += f" Q {cpx:.1f} {cpy:.1f} {x1:.1f} {y1:.1f}"
        else:
            path_d += f" L {x1:.1f} {y1:.1f}"

    kt_str = ";".join(f"{t:.4f}" for t in times)
    spline_str = ";".join(["0.25 0.1 0.25 1.0"] * (len(path_points) - 1))

    # ── GENERATE SVG ──────────────────────────────────────────────
    svg = []
    svg.append(
        f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;">'
    )

    # CSS Stylesheet
    svg.append("""<style>
  .bg       { fill: #5c94fc; }
  .empty    { fill: rgba(255,255,255,0.12); }
  .lvl1     { fill: #0e4429; }
  .lvl2     { fill: #006d32; }
  .lvl3     { fill: #26a641; }
  .lvl4     { fill: #39d353; }
  .ground   { fill: #5C3317; }
  .brick    { fill: #c84c0c; stroke:#000; stroke-width:0.4; }
  .pipe     { fill: #00a800; stroke:#000; stroke-width:0.6; }
  .pipe-top { fill: #00d000; stroke:#000; stroke-width:0.6; }
</style>""")

    # Defs: Sprites
    svg.append('<defs>')
    svg.append(make_sprite_svg('spr_mario',    MARIO_PIXELS,    MARIO_COLORS,    SPRITE_SCALE))
    svg.append(make_sprite_svg('spr_goomba',   GOOMBA_PIXELS,   GOOMBA_COLORS,   SPRITE_SCALE))
    svg.append(make_sprite_svg('spr_question', QUESTION_PIXELS, QUESTION_COLORS, SPRITE_SCALE * 0.95))
    svg.append(make_sprite_svg('spr_coin',     COIN_PIXELS,     COIN_COLORS,     1.3))
    svg.append(make_sprite_svg('spr_star',     STAR_PIXELS,     STAR_COLORS,     1.4))
    svg.append('</defs>')

    # Background sky
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" class="bg"/>')

    # Seamless Parallax Clouds
    cloud_shapes = [
        [(0,0,22,12),(20,-8,18,10),(-18,-6,16,9),(2,10,28,10)],
        [(0,0,18,9),(15,-6,14,8),(-14,-5,13,7),(2,8,22,8)],
        [(0,0,26,13),(22,-9,20,11),(-20,-7,18,10),(3,11,30,11)],
    ]
    cloud_y_pos = [8, 22, 14]
    cloud_speeds = [36, 50, 44]

    for idx, (shape, cy, spd) in enumerate(zip(cloud_shapes, cloud_y_pos, cloud_speeds)):
        for offset in [0, WIDTH]:
            svg.append('<g opacity="0.85">')
            svg.append(
                f'  <animateTransform attributeName="transform" type="translate" '
                f'from="{offset} 0" to="{offset - WIDTH - 120} 0" '
                f'dur="{spd}s" repeatCount="indefinite" begin="{idx * -spd/3:.1f}s"/>'
            )
            for cx, ely, rx, ry in shape:
                svg.append(
                    f'  <ellipse cx="{cx}" cy="{cy + ely}" rx="{rx}" ry="{ry}" '
                    f'fill="#ffffffcc" stroke="#ccc" stroke-width="0.3"/>'
                )
            svg.append('</g>')

    # Ground & Bricks
    svg.append(f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="{HEIGHT - GROUND_Y}" class="ground"/>')
    bw = 28
    for bx in range(0, WIDTH, bw):
        svg.append(f'<rect x="{bx}" y="{GROUND_Y}" width="{bw-1}" height="7" class="brick"/>')
    for bx in range(bw//2, WIDTH, bw):
        svg.append(f'<rect x="{bx}" y="{GROUND_Y+7}" width="{bw-1}" height="7" class="brick"/>')

    # Bushes
    for bx in range(25, WIDTH - 80, 120):
        bh  = 16
        bw2 = 36
        svg.append(f'<ellipse cx="{bx + bw2//2}" cy="{GROUND_Y - bh//2}" rx="{bw2//2}" ry="{bh//2}" fill="#00a800" opacity="0.9"/>')
        svg.append(f'<ellipse cx="{bx + bw2//2 - bw2//4}" cy="{GROUND_Y - bh//2 - 3}" rx="{bw2//3}" ry="{bh//3}" fill="#00c800" opacity="0.9"/>')
        svg.append(f'<ellipse cx="{bx + bw2//2 + bw2//4}" cy="{GROUND_Y - bh//2 - 2}" rx="{bw2//3}" ry="{bh//3}" fill="#00c800" opacity="0.9"/>')

    # Start warp pipe
    svg.append(f'<rect x="{pipe_x}" y="{pipe_top + 10}" width="26" height="{GROUND_Y - pipe_top - 10}" class="pipe"/>')
    svg.append(f'<rect x="{pipe_x - 3}" y="{pipe_top}" width="32" height="12" class="pipe-top"/>')
    svg.append(f'<rect x="{pipe_x + 4}" y="{pipe_top + 10}" width="4" height="{GROUND_Y - pipe_top - 10}" fill="#00d000" opacity="0.3"/>')

    # Contribution Grid Rectangles
    svg.append('<!-- contribution grid -->')
    for c_idx, week in enumerate(weeks_data):
        cx = GRID_X + c_idx * STEP
        for r_idx, day in enumerate(week['contributionDays']):
            lvl = level_map.get(day.get('contributionLevel', 'NONE'), 'empty')
            cy  = TOP_PAD + r_idx * STEP
            svg.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" ry="2" class="{lvl}"/>')

    # ── Obstacle 1: Goombas (strictly 2 Goombas, squashed then reset) ──
    for i, gb in enumerate(goombas):
        gx = gb['x']
        gy = gb['y']
        ts = gb['t_stomp']
        tf = gb['t_fade']
        svg.append(f'<!-- Goomba #{i+1} at x={gx} -->')
        svg.append(f'<g transform="translate({gx},{gy})">')
        svg.append(f'  <use href="#spr_goomba">')
        # Waddling walk animation while alive
        svg.append(
            f'    <animateTransform attributeName="transform" type="translate" '
            f'values="0,0; -2,0; 0,0; 2,0; 0,0" dur="0.8s" repeatCount="indefinite"/>'
        )
        # Squash & vanish when stomped, then reset back to 1 at loop start (t=0)
        svg.append(
            f'    <animate attributeName="opacity" '
            f'values="1; 1; 1; 0; 0; 1" '
            f'keyTimes="0; {ts:.4f}; {ts + 0.004:.4f}; {tf:.4f}; 0.9800; 1" '
            f'dur="{DURATION}s" repeatCount="indefinite"/>'
        )
        svg.append(f'  </use>')
        svg.append(f'</g>')

    # ── Obstacle 2: Question Blocks (Bump on hit, reset at loop end) ──
    for i, qb in enumerate(qblocks):
        qx = qb['x']
        qy = qb['y']
        th = qb['t_hit']
        tb = th + 0.008
        ts = th + 0.016
        svg.append(f'<!-- Question Block #{i+1} at x={qx} -->')
        svg.append(f'<g transform="translate({qx},{qy})">')
        svg.append(f'  <use href="#spr_question">')
        # Bump up 4px and settle back
        svg.append(
            f'    <animateTransform attributeName="transform" type="translate" '
            f'values="0,0; 0,0; 0,-4; 0,0; 0,0" '
            f'keyTimes="0; {th:.4f}; {tb:.4f}; {ts:.4f}; 1" '
            f'dur="{DURATION}s" repeatCount="indefinite"/>'
        )
        svg.append(f'  </use>')
        svg.append(f'</g>')

    # ── Gold Coins: Pop out of blocks, spin, fade, RESET CLEANLY ──
    for i, qb in enumerate(qblocks):
        cx = qb['x'] + 1
        cy = qb['y'] - 4
        th = qb['t_hit']
        tc = qb['t_collect']
        t_spin = (th + tc) / 2
        svg.append(f'<!-- Coin #{i+1} -->')
        svg.append(f'<g>')
        # Translate: hidden inside block -> shoots up 22px -> resets at loop end
        svg.append(
            f'  <animateTransform attributeName="transform" type="translate" '
            f'values="{cx},{cy}; {cx},{cy}; {cx},{cy - 22}; {cx},{cy - 22}; {cx},{cy}" '
            f'keyTimes="0; {th:.4f}; {tc:.4f}; 0.9800; 1" '
            f'dur="{DURATION}s" repeatCount="indefinite"/>'
        )
        svg.append(f'  <use href="#spr_coin">')
        # Opacity: 0 -> 1 on pop -> 0 when collected -> 0 at loop end -> resets to 0 at t=0
        svg.append(
            f'    <animate attributeName="opacity" '
            f'values="0; 0; 1; 1; 0; 0; 0" '
            f'keyTimes="0; {th:.4f}; {th + 0.003:.4f}; {tc - 0.004:.4f}; {tc:.4f}; 0.9800; 1" '
            f'dur="{DURATION}s" repeatCount="indefinite"/>'
        )
        # Horizontal spin (no additive sum to prevent matrix accumulation on loop)
        svg.append(
            f'    <animateTransform attributeName="transform" type="scale" '
            f'values="1,1; 1,1; 0.1,1; 1,1; 1,1; 1,1" '
            f'keyTimes="0; {th:.4f}; {t_spin:.4f}; {tc:.4f}; 0.9800; 1" '
            f'dur="{DURATION}s" repeatCount="indefinite"/>'
        )
        svg.append(f'  </use>')
        svg.append(f'</g>')

    # Twinkling Stars in Sky
    star_positions = [(60, 6), (180, 12), (310, 8), (450, 14), (580, 5), (710, 10), (820, 7)]
    for idx, (sx, sy) in enumerate(star_positions):
        delay = idx * 0.7
        svg.append(f'<g transform="translate({sx},{sy})">')
        svg.append(f'  <use href="#spr_star" opacity="0.0">')
        svg.append(f'    <animate attributeName="opacity" values="0;0.8;0" dur="3s" begin="{delay:.1f}s" repeatCount="indefinite"/>')
        svg.append(f'    <animateTransform attributeName="transform" type="scale" values="0.5;1;0.5" dur="3s" begin="{delay:.1f}s" repeatCount="indefinite"/>')
        svg.append(f'  </use>')
        svg.append(f'</g>')

    # ── Flagpole ──────────────────────────────────────────────────
    flag_pole_h = GROUND_Y - flag_top
    svg.append(f'<rect x="{flag_pole}" y="{flag_top}" width="3" height="{flag_pole_h}" fill="#e0e0e0" stroke="#888" stroke-width="0.5"/>')
    svg.append(f'<circle cx="{flag_pole + 1.5}" cy="{flag_top}" r="5" fill="#f8d820" stroke="#a06000"/>')

    # Flag drops when Mario arrives, holds at bottom, resets at loop start (t=0)
    flag_drop = flag_pole_h - 18
    svg.append(f'<g id="flag">')
    svg.append(
        f'  <animateTransform attributeName="transform" type="translate" '
        f'values="0,0; 0,0; 0,{flag_drop}; 0,{flag_drop}; 0,0" '
        f'keyTimes="0; {t_flag_arrive:.4f}; {t_flag_done:.4f}; 0.9800; 1" '
        f'dur="{DURATION}s" repeatCount="indefinite"/>'
    )
    svg.append(f'  <polygon points="{flag_pole - 18},{flag_top + 3} {flag_pole},{flag_top + 3} {flag_pole},{flag_top + 18}" fill="#00a800" stroke="#004400" stroke-width="0.5"/>')
    svg.append(f'</g>')

    # ── Castle ────────────────────────────────────────────────────
    cx0 = CASTLE_X
    cy0 = GROUND_Y - 45
    # Castle Body
    svg.append(f'<rect x="{cx0}" y="{cy0}" width="60" height="{GROUND_Y - cy0}" fill="#c84c0c" stroke="#000" stroke-width="0.8"/>')
    for bx in [0, 10, 20, 30, 40, 50]:
        svg.append(f'<rect x="{cx0+bx}" y="{cy0-10}" width="8" height="12" fill="#c84c0c" stroke="#000" stroke-width="0.8"/>')
    # Windows
    svg.append(f'<rect x="{cx0+8}" y="{cy0+6}" width="10" height="10" fill="#f8d820" stroke="#000" stroke-width="0.5" rx="1"/>')
    svg.append(f'<rect x="{cx0+42}" y="{cy0+6}" width="10" height="10" fill="#f8d820" stroke="#000" stroke-width="0.5" rx="1"/>')
    # Arched Entrance
    svg.append(f'<path d="M {cx0+22} {GROUND_Y} L {cx0+22} {cy0+24} A 8 8 0 0 1 {cx0+38} {cy0+24} L {cx0+38} {GROUND_Y} Z" fill="#000"/>')
    # Castle Flagpole
    svg.append(f'<rect x="{cx0+28}" y="{cy0-22}" width="2" height="16" fill="#888"/>')

    # Castle Flag raises up when Mario enters castle!
    svg.append(f'<g id="castle_flag">')
    svg.append(
        f'  <animateTransform attributeName="transform" type="translate" '
        f'values="0,12; 0,12; 0,0; 0,0; 0,12" '
        f'keyTimes="0; {t_castle_door:.4f}; {min(0.95, t_castle_door + 0.02):.4f}; 0.9800; 1" '
        f'dur="{DURATION}s" repeatCount="indefinite"/>'
    )
    svg.append(f'  <polygon points="{cx0+30},{cy0-22} {cx0+42},{cy0-16} {cx0+30},{cy0-10}" fill="#e52521"/>')
    svg.append(f'</g>')

    # ── "LEVEL CLEAR!" Text (triumphant display then resets) ───────
    text_x = flag_pole - 60
    text_y = flag_top - 8
    t_clear_start = t_flag_done + 0.008
    svg.append(
        f'<text x="{text_x}" y="{text_y}" font-family="monospace" font-weight="bold" '
        f'font-size="14" fill="#f8d820" stroke="#000" stroke-width="1.2" opacity="0">'
    )
    svg.append(f'  LEVEL CLEAR!')
    svg.append(
        f'  <animate attributeName="opacity" '
        f'values="0; 0; 1; 1; 0; 0" '
        f'keyTimes="0; {t_clear_start:.4f}; {min(0.95, t_clear_start + 0.015):.4f}; 0.9750; 0.9950; 1" '
        f'dur="{DURATION}s" repeatCount="indefinite"/>'
    )
    svg.append(f'</text>')

    # ── Mario: Path Motion + Opacity Fade inside Castle ────────────
    svg.append(f'<path id="mp" d="{path_d}" fill="none" stroke="none"/>')
    svg.append(f'<use href="#spr_mario">')
    # Fades out once inside castle door, re-emerges at pipe at start of loop
    svg.append(
        f'  <animate attributeName="opacity" '
        f'values="1; 1; 0; 0; 1" '
        f'keyTimes="0; {t_castle_door:.4f}; {min(0.96, t_castle_door + 0.015):.4f}; 0.9900; 1" '
        f'dur="{DURATION}s" repeatCount="indefinite"/>'
    )
    svg.append(
        f'  <animateMotion dur="{DURATION}s" repeatCount="indefinite" '
        f'rotate="0" calcMode="spline" keyTimes="{kt_str}" keySplines="{spline_str}">'
    )
    svg.append(f'    <mpath href="#mp"/>')
    svg.append(f'  </animateMotion>')
    svg.append(f'</use>')

    # ── Retro HUD Overlay ─────────────────────────────────────────
    total_coins = len(qblocks)
    svg.append(f'<text x="10" y="14" font-family="monospace" font-size="10" fill="#f8d820" font-weight="bold">MARIO</text>')
    svg.append(f'<text x="10" y="25" font-family="monospace" font-size="10" fill="#ffffff">x{total_coins:02d} COINS</text>')
    svg.append(f'<text x="{WIDTH//2 - 20}" y="14" font-family="monospace" font-size="10" fill="#f8d820" font-weight="bold">WORLD</text>')
    svg.append(f'<text x="{WIDTH//2 - 12}" y="25" font-family="monospace" font-size="10" fill="#ffffff">  1-1</text>')
    svg.append(f'<text x="{WIDTH - 65}" y="14" font-family="monospace" font-size="10" fill="#f8d820" font-weight="bold"> TIME</text>')
    svg.append(f'<text x="{WIDTH - 58}" y="25" font-family="monospace" font-size="10" fill="#ffffff">  400</text>')

    svg.append('</svg>')

    content = "\n".join(svg)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(
        f"OK Generated {filename} ({len(content):,} bytes | "
        f"{COLS} weeks | {total_coins} coins | "
        f"{len(goombas)} goombas | loop={DURATION}s)"
    )


if __name__ == "__main__":
    generate_mario_github_svg()
