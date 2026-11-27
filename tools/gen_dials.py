"""
gen_dials.py - writes the dial themes drawn by the "pdash" shader (shared/shaders.js) for Cluster Themes on iDrive 7:

    M Performance  apps/cluster_themes/hud/layouts/mperf.json  twin chrome dials in M colours, M stripe, big gear
    M Competition  apps/cluster_themes/hud/layouts/mcomp.json  one big rev dial, huge gear, race data both sides
    i Electric     apps/cluster_themes/hud/layouts/ielec.json  glowing speed + hybrid battery dials in BMW i blue
    Heritage       apps/cluster_themes/hud/layouts/heritage.json  needles and chrome, trip computer, status pill

    python3 tools/gen_dials.py            # from the repo root; edit this file, not the JSON

Colours are the themes "mperf", "mcomp" and "ielec" in shared/hud_themes.js. Every dial is one shader layer (the bands,
glow, ticks, red zone, bezels and the M stripe), the numbers are text widgets on top. Kept clear of the hood line at the
top corners, the driver camera notch, and the seat-belt light; BMW paints its own solid black gear box at x 1406-1597,
y 342-419, so the twin-dial themes centre their right dial on it and BMW's gear letter shows in the middle of the dial.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'layouts')
FONT_H = {'scale': 26, 'b_val': 45, 'b_unit': 29, 'small': 45, 'c_speed': 112, 'c_val': 55, 'r_label': 30, 'y_gear': 222, 's_scale': 27, 'b_scale': 18, 'm_label': 21,
          's_hero': 115, 'n_gear': 83, 'head': 27, 'b_val': 45, 'm_speed': 66, 'm_gl': 23}
GEARBOX = (1406, 342, 1597, 419)
GB_C = ((GEARBOX[0] + GEARBOX[2]) // 2, (GEARBOX[1] + GEARBOX[3]) // 2)      # 1501, 380
SPEED_MARKS = 9                         # shared/hud.js SPEED_SCALE: 9 labels, {{spd:0}} .. {{spd:8}}


def text(id_, x, y, w, txt, font, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x)), 'y': int(round(y)), 'w': int(w), 'h': FONT_H[font],
         'text': txt, 'font': font, 'color': color, 'align': align, 'conn': 1}
    d.update(kw)
    return d


def ctext(id_, cx, cy, w, txt, font, color='fg', **kw):
    """Text centred on (cx, cy)."""
    return text(id_, cx - w / 2, cy - FONT_H[font] / 2, w, txt, font, color, 'center', **kw)


def fill(id_, x, y, w, h, color='bg', z=0, **kw):
    d = {'id': id_, 'type': 'fill', 'class': 'content', 'z': z, 'x': x, 'y': y, 'w': w, 'h': h, 'color': color}
    d.update(kw)
    return d


def meter(id_, x, y, w, h, signal, mn, mx, colors, at, segments=30, gap=3, **kw):
    d = {'id': id_, 'type': 'meter', 'class': 'content', 'z': 2, 'x': x, 'y': y, 'w': w, 'h': h, 'signal': signal,
         'min': mn, 'max': mx, 'segments': segments, 'gap': gap, 'colors': colors, 'at': at, 'conn': 2}
    d.update(kw)
    return d


def dial(cx, cy, r, signal, colors, start=225, sweep=270, band=24, ticks=40, major=5, **kw):
    d = {'cx': cx, 'cy': cy, 'r': r, 'band': band, 'start': start, 'sweep': sweep, 'ticks': ticks, 'major': major,
         'signal': signal, 'colors': colors}
    d.update(kw)
    return d


def pdash(dials, stripe=None, id_='dash', rect=(0, 0, 1920, 660), **kw):
    d = {'id': id_, 'type': 'pdash', 'class': 'content', 'z': 1, 'x': rect[0], 'y': rect[1], 'w': rect[2], 'h': rect[3],
         'dials': dials, 'color': 'bg', 'conn': 0}
    if stripe:
        d['stripe'] = stripe
    d.update(kw)
    return d


def labels(prefix, d, texts, font, color='dim', inset=64, red_from=None):
    """The scale's numbers round a dial, evenly spread over its sweep, inset px inside the outer edge."""
    out, n = [], len(texts)
    R = d['r'] - d['band'] - inset
    for i, t in enumerate(texts):
        a = math.radians(d['start'] + d['sweep'] * i / (n - 1))
        x, y = d['cx'] + R * math.sin(a), d['cy'] - R * math.cos(a)
        c = 'hot' if red_from is not None and i >= red_from else color
        out.append(ctext('%s%d' % (prefix, i), x, y, 110, t, font, c))
    return out


def strip():
    """The bottom row (as Cruise): clock, fuel range, outside temperature; BMW's own gear letter left uncovered."""
    return [
        fill('strip_cover_l', 0, 660, 1380, 60, stripRow='l'),
        fill('strip_cover_r', 1460, 660, 460, 60, stripRow='r'),
        text('strip_time', 184, 660, 146, '{{time}}', 'c_val', align='right', z=3, stripRow='l'),
        text('strip_ampm', 336, 689, 32, '{{ampm}}', 'r_label', 'dim', 'left', z=3, stripRow='l'),
        text('strip_range', 862, 660, 128, '{{range}}', 'c_val', align='right', z=3, stripRow='l'),
        text('strip_range_u', 996, 689, 32, '{{u:dist}}', 'r_label', 'dim', 'left', z=3, stripRow='l'),
        text('strip_out', 1668, 660, 88, '{{ambientN}}', 'c_val', align='right', z=3, stripRow='r'),
        text('strip_out_u', 1762, 689, 25, '{{u:temp}}', 'r_label', 'dim', 'left', z=3, stripRow='r'),
    ]


def readout(prefix, x, y, head, val, unit, head_color='dim', w=190, font='c_val'):
    """A small label over a number with its unit, left-aligned at x."""
    return [text(prefix + '_h', x, y, w, head, 'm_label', head_color, 'left', spacing=2),
            text(prefix, x, y + 28, 120, val, font, 'fg', 'right'),
            text(prefix + '_u', x + 126, y + 28 + FONT_H[font] - 34, 70, unit, 'r_label', 'dim', 'left')]


def mperf():
    r = 252
    rcx, rcy = GB_C
    lcx = 1920 - rcx
    spd = dial(lcx, rcy, r, 'speed', ['mlb', 'mdb', 'mred'], ticks=32, major=4, glow=0.75)
    tach = dial(rcx, rcy, r, 'rpm', ['mlb', 'mdb', 'mred'], ticks=35, major=5, max=7000, glow=0.75)
    w = [pdash([spd, tach], stripe=[858, 150, 204, 14])]
    w += labels('spd_l', spd, ['{{spd:%d}}' % i for i in range(SPEED_MARKS)], 's_scale')
    w += labels('rpm_l', tach, [str(i) for i in range(8)], 's_scale')
    # inside the speed dial: the speed and its unit; inside the tach BMW's gear letter, the revs under it
    w += [ctext('speed', lcx, rcy - 8, 330, '{{speed}}', 'c_speed'),
          ctext('speed_u', lcx, rcy + 74, 200, '{{u:speedLc}}', 'r_label', 'dim'),
          ctext('rpm_x', rcx, rcy - 92, 200, 'RPM X1000', 'm_label', 'dim', spacing=2),
          ctext('rpm', rcx, GEARBOX[3] + 46, 200, '{{rpm}}', 'm_gl', 'dim')]
    # the middle: shift lights under the camera notch, the M stripe, a huge gear, the drive mode, three readouts
    w += [{'id': 'lights', 'type': 'lights', 'class': 'content', 'z': 2, 'x': 760, 'y': 118, 'w': 400, 'h': 20,
           'count': 12, 'from': 3500, 'round': True, 'conn': 2},
          ctext('gear', 960, 300, 260, '{{gearnum}}', 'y_gear', hotWhen='now'),
          ctext('mode', 960, 432, 300, '{{mode}}', 'm_label', 'accent', spacing=3)]
    w += readout('oil', 742, 482, 'OIL', '{{oil}}', '{{u:temp}}', w=150)
    w += readout('cool', 905, 482, 'WATER', '{{coolant}}', '{{u:temp}}', w=150)
    w += readout('pwr', 1068, 482, 'POWER', '{{power}}', 'kW', w=150)
    for e in w:
        if e['id'] in ('oil', 'cool', 'pwr'):
            e['w'], e['x'] = 100, e['x'] - 10
        if e['id'] in ('oil_u', 'cool_u', 'pwr_u'):
            e['x'] -= 36
    return {
        'schemaVersion': 2, 'name': 'M Performance', 'theme': 'mperf',
        '_about': 'M Performance cluster for iDrive 7, generated by tools/gen_dials.py (edit that and regenerate): twin '
                  'chrome-ringed dials drawn in one shader (pdash), the bands filling M light blue -> M blue -> M red '
                  'with a glow and a bright tip, the tach\'s red zone from the Redline setting; BMW\'s own gear letter '
                  'inside the tach. Between them shift lights, the slanted M stripe, a huge gear (red at the shift '
                  'point), the drive mode, oil, water and engine kW. No map window. Widget reference: shared/hud.js.',
        'widgets': w + strip(),
    }


def mcomp():
    cx, cy, r = 960, 470, 340
    tach = dial(cx, cy, r, 'rpm', ['white', 'amber', 'mred'], start=240, sweep=240, band=34, ticks=70, major=10,
                max=7000, glow=0.9)
    w = [pdash([tach], stripe=[912, 238, 96, 10])]
    w += labels('rpm_l', tach, [str(i) for i in range(8)], 's_scale', inset=48)
    w += [ctext('gear', cx, 352, 260, '{{gearnum}}', 'y_gear', hotWhen='now'),
          ctext('speed', cx, 520, 240, '{{speed}}', 'm_speed'),
          ctext('speed_u', cx, 574, 160, '{{u:speedLc}}', 'r_label', 'dim'),
          ctext('mode', cx, 616, 300, '{{mode}}', 'm_label', 'accent', spacing=3)]
    # left side: engine data with bars
    L = 230
    for i, (k, head, tok, unit, sig, mn, mx, at) in enumerate([
            ('oil', 'OIL', '{{oil}}', '{{u:temp}}', 'oil', 40, 150, [0.45, 0.85]),
            ('cool', 'WATER', '{{coolant}}', '{{u:temp}}', 'coolant', 40, 130, [0.45, 0.85]),
            ('pwr', 'POWER', '{{power}}', 'kW', 'powerPct', 0, 100, [0.6, 0.9])]):
        y = 300 + i * 112
        w += [text(k + '_h', L, y, 150, head, 'm_label', 'dim', 'left', spacing=2),
              text(k, L + 160, y - 14, 100, tok, 'c_val', align='right'),
              text(k + '_u', L + 266, y + 4, 60, unit, 'r_label', 'dim', 'left'),
              meter(k + '_bar', L, y + 52, 330, 6, sig, mn, mx, ['white', 'amber', 'mred'], at, 33, 2)]
    # right side (clear of BMW's gear box at y 342-419): battery and fuel above it, the g-forces under it
    R = 1340
    w += [text('hv_h', R, 190, 150, 'BATTERY', 'm_label', 'dim', 'left', spacing=2),
          text('hv', R + 170, 176, 90, '{{hvSoc}}', 'c_val', align='right'),
          text('hv_u', R + 266, 194, 40, '%', 'r_label', 'dim', 'left'),
          meter('hv_bar', R, 242, 330, 6, 'hvSoc', 0, 100, ['mred', 'white', 'white'], [0.12, 1], 33, 2),
          text('fuel_h', R, 268, 150, 'FUEL', 'm_label', 'dim', 'left', spacing=2),
          meter('fuel_bar', R, 302, 330, 6, 'fuel', 0, 1, ['mred', 'white', 'white'], [0.12, 1], 33, 2),
          text('fuel', R + 170, 256, 90, '{{fuelPct}}', 'r_label', align='right'),
          text('fuel_u', R + 266, 256, 40, '%', 'r_label', 'dim', 'left'),
          text('g_h', R, 452, 150, 'G LAT', 'm_label', 'dim', 'left', spacing=2),
          text('g', R + 150, 438, 140, '{{gSide}}', 'r_label', align='right'),
          text('gb_h', R, 512, 150, 'G LONG', 'm_label', 'dim', 'left', spacing=2),
          text('gb', R + 150, 498, 140, '{{gFwd}}', 'r_label', align='right'),
          text('best_h', R, 572, 150, 'G BEST', 'm_label', 'dim', 'left', spacing=2),
          text('best', R + 150, 558, 140, '{{gBest}}', 'r_label', 'accent', 'right')]
    return {
        'schemaVersion': 2, 'name': 'M Competition', 'theme': 'mcomp', 'engine': {'powerKw': 135, 'torqueNm': 300},
        '_about': 'M Competition cluster for iDrive 7, generated by tools/gen_dials.py (edit that and regenerate): one big '
                  'rev dial in the middle (pdash shader) heating white -> amber -> M red with a glow, the red zone from the '
                  'Redline setting, a huge gear inside (red at the shift point), speed and drive mode under it; oil, water '
                  'and engine power with bars on the left; battery, fuel and the g-forces on the right, clear of BMW\'s '
                  'gear box. No map window. Widget reference: shared/hud.js header.',
        'widgets': w + strip(),
    }


def ielec():
    r = 252
    rcx, rcy = GB_C
    lcx = 1920 - rcx
    spd = dial(lcx, rcy, r, 'speed', ['deep', 'iblue', 'cyan'], ticks=32, major=4, glow=1.0, band=20)
    bat = dial(rcx, rcy, r, 'hvSoc', ['teal', 'iblue', 'cyan'], ticks=20, major=5, min=0, max=100, glow=1.0,
               band=20)
    w = [pdash([spd, bat], bezelColor='line')]
    w += labels('spd_l', spd, ['{{spd:%d}}' % i for i in range(SPEED_MARKS)], 'b_scale', inset=50)
    w += labels('bat_l', bat, ['0', '25', '50', '75', '100'], 'b_scale', inset=50)
    w += [ctext('speed', lcx, rcy - 8, 330, '{{speed}}', 'c_speed'),
          ctext('speed_u', lcx, rcy + 74, 200, '{{u:speedLc}}', 'r_label', 'dim'),
          ctext('bat_h', rcx, rcy - 96, 240, 'BATTERY', 'm_label', 'iblue', spacing=3),
          text('bat', rcx - 110, GEARBOX[3] + 14, 120, '{{hvSoc}}', 'c_val', align='right'),
          text('bat_u', rcx + 16, GEARBOX[3] + 32, 40, '%', 'r_label', 'dim', 'left')]
    # the middle: eDrive state, mode, fuel and power
    w += [ctext('eng', 960, 196, 300, '{{engineState}}', 'm_label', 'cyan', spacing=3),
          ctext('mode', 960, 236, 300, '{{mode}}', 'm_label', 'dim', spacing=3),
          fill('rule1', 790, 270, 340, 1, 'line', z=2, conn=2),
          text('pwr_h', 790, 296, 160, 'POWER', 'm_label', 'dim', 'left', spacing=2),
          text('pwr', 990, 282, 90, '{{power}}', 'c_val', align='right'),
          text('pwr_u', 1086, 300, 44, 'kW', 'r_label', 'dim', 'left'),
          meter('pwr_bar', 790, 350, 340, 6, 'powerPct', 0, 100, ['iblue', 'cyan', 'cyan'], [0.7, 1], 34, 2),
          text('fuel_h', 790, 392, 160, 'FUEL', 'm_label', 'dim', 'left', spacing=2),
          text('fuel', 990, 378, 90, '{{fuelPct}}', 'c_val', align='right'),
          text('fuel_u', 1086, 396, 44, '%', 'r_label', 'dim', 'left'),
          meter('fuel_bar', 790, 446, 340, 6, 'fuel', 0, 1, ['hot', 'fg', 'fg'], [0.12, 1], 34, 2),
          text('avg_h', 790, 488, 160, 'AVERAGE', 'm_label', 'dim', 'left', spacing=2),
          text('avg', 990, 474, 90, '{{avgSpeed}}', 'c_val', align='right'),
          text('avg_u', 1086, 492, 60, '{{u:speedLc}}', 'r_label', 'dim', 'left')]
    return {
        'schemaVersion': 2, 'name': 'i Electric', 'theme': 'ielec', 'engine': {'powerKw': 135, 'torqueNm': 300},
        '_about': 'i Electric cluster for iDrive 7 plug-in hybrids (made on a 330e), generated by tools/gen_dials.py (edit '
                  'that and regenerate): two glowing dials in one shader (pdash), deep blue -> BMW i blue -> cyan: the '
                  'speed on the left, the high-voltage battery on the right with BMW\'s gear letter '
                  'inside it. In the middle ENGINE ON / OFF, the drive mode, engine kW (of the B48\'s 135), fuel and the '
                  'average speed. No map window. Widget reference: shared/hud.js header.',
        'widgets': w + strip(),
    }


def heritage():
    """An F80 M3's cluster (2015): two big chrome-ringed dials side by side, small fuel and oil gauges outboard, the gear
    and the speed between the dials at the bottom; plus a trip computer, the hybrid battery and a status pill."""
    r, cy = 255, 330
    scx, tcx = 960 - r, 960 + r                   # the two dials touch in the middle
    big = dict(start=230, sweep=260, band=0, bandW=6, needle=True, face=True, glow=0.0, tickScale=0.9)
    small = dict(start=240, sweep=240, band=0, bandW=5, needle=True, face=True, glow=0.0, tickScale=0.55)
    spd = dial(scx, cy, r, 'speed', ['fg', 'fg', 'fg'], ticks=28, major=2, linear=True, max=280, **big)
    tach = dial(tcx, cy, r, 'rpm', ['fg', 'fg', 'fg'], ticks=35, major=5, max=7000, redW=16, **big)
    fuel = dial(255, 420, 100, 'fuel', ['fg', 'fg', 'fg'], ticks=8, major=4, min=0, max=1, **small)
    oil = dial(1665, 420, 100, 'oil', ['fg', 'fg', 'fg'], ticks=10, major=5, min=70, max=170, red=150, **small)
    face = dict(start=240, sweep=240, band=0, bandW=4, needle=True, face=False, glow=0.0, bezel=False, tickScale=0.45)
    # in the dials' lower faces: the hybrid battery's power (charge left of 0, power right) and an econometer
    pwr = dial(scx, 452, 64, 'hvKw', ['fg', 'fg', 'fg'], ticks=12, major=4, min=-40, max=80, **face)
    eco = dial(tcx, 452, 64, 'l100', ['fg', 'fg', 'fg'], ticks=10, major=5, min=0, max=20, red=15, **face)
    pill = [870, 64, 180, 34]                      # the status pill: in the gap over the two dials
    w = [fill('bg', 0, 0, 1920, 660),
         pdash([fuel, spd, pwr], id_='dash_l', rect=(0, 40, 960, 620), needleColor='needle', faceColor='panel', tickColor='fg'),
         pdash([tach, oil, eco], id_='dash_r', rect=(960, 40, 960, 620), needleColor='needle', faceColor='panel', tickColor='fg',
               stripe=[tcx - 36, 196, 72, 12]),
         pdash([], id_='dash_m', rect=(pill[0] - 4, pill[1] - 4, pill[2] + 8, pill[3] + 8), pill=pill, z=2, conn=2)]
    # the scales: numerals inside the ticks
    w += labels('spd_l', spd, [str(v) for v in range(0, 281, 20)], 'scale', 'fg', inset=60)
    w += labels('rpm_l', tach, [str(i) for i in range(8)], 'b_val', 'fg', inset=66)
    w += [ctext('spd_u', scx, cy - 95, 120, 'km/h', 'b_unit', 'fg'),
          ctext('rpm_u', tcx, cy - 95, 200, '1/min x 1000', 'r_label', 'fg'),
          ctext('eng', tcx, cy - 60, 200, '{{engineState}}', 'm_label', 'dim', spacing=1)]
    # the lower faces' small gauges: their ends and readings
    for k, d, ends, val in (('pwr', pwr, ('CHG', 'PWR'), '{{hvKw}} kW'), ('eco', eco, ('0', '20'), '{{l100}} l/100')):
        for j, t in enumerate(ends):          # the two ends, just outside the dial's open bottom
            w.append(ctext('%s_l%d' % (k, j), d['cx'] + (-1 if j == 0 else 1) * 70, d['cy'] + 44, 60, t, 'm_label', 'dim'))
        w.append(ctext(k + '_v', d['cx'], d['cy'] + 66, 160, val, 'r_label', 'fg'))
    # the small gauges: fuel 0 1/2 1 (and the pump's side), oil 70 120 170 C
    for k, d, ends in (('fuel', fuel, ('0', '1/2', '1')), ('oil', oil, ('70', '120', '170'))):
        R = d['r'] - 40
        for j, t in enumerate(ends):
            a = math.radians(d['start'] + d['sweep'] * j / 2)
            w.append(ctext('%s_l%d' % (k, j), d['cx'] + R * math.sin(a), d['cy'] - R * math.cos(a), 70, t, 'r_label', 'fg'))
    w += [{'id': 'fuel_icon', 'type': 'icon', 'icon': 'fuel', 'z': 5, 'x': 237, 'y': 444, 'w': 22, 'h': 26, 'color': 'dim',
           'conn': 3},
          text('fuel_side', 262, 446, 20, '>', 'head', 'dim', 'left', conn=3),
          ctext('fuel_v', 255, 492, 120, '{{fuelPct}} %', 'r_label', 'dim'),
          ctext('oil_u', 1665, 492, 140, 'OIL {{oil}}°', 'r_label', 'dim')]
    # between the dials, at the bottom: the speed and the gear
    w += [text('speed', 880, 476, 106, '{{speed}}', 'c_val', 'fg', 'right', conn=2),
          text('speed_u', 990, 497, 60, 'km/h', 'r_label', 'dim', 'left', conn=2),
          ctext('gear', 960, 588, 160, '{{gearnum}}', 'n_gear', 'fg', hotWhen='now', conn=2),
          ctext('mode', 960, 642, 220, '{{mode}}', 'm_label', 'accent', spacing=2, conn=2)]
    # the status pill in the speedo's lower face
    w += [text('status_ok', pill[0], pill[1] + 7, pill[2], 'ALL OK', 'm_label', 'ok', spacing=3, showWhen='ok', conn=2),
          text('status_warn', pill[0], pill[1] + 7, pill[2], '{{status}}', 'm_label', 'fg', spacing=1, showWhen='!ok', conn=2)]
    # under the small gauges: the trip computer (left), the date, battery and water (right)
    def cell(k, x, y, head, tok, unit, color='fg'):
        return [text(k + '_h', x, y, 160, head, 'm_label', 'dim', 'left', spacing=1, conn=3),
                text(k, x, y + 22, 180, tok + ' ' + unit if unit else tok, 'r_label', color, 'left', conn=3)]
    for side, x0, cells in (('trip', 50, [('TRIP', '{{trip}}', 'km', 'fg'), ('TIME', '{{tripTime}}', 'h', 'fg'),
                                          ('AVERAGE', '{{avgSpeed}}', 'km/h', 'fg'), ('FUEL', '{{tripFuel}}', 'l/100', 'fg')]),
                            ('info', 1490, [('HV', '{{hvSoc}}', '%', 'ev'), ('E-RANGE', '{{eRange}}', 'km', 'ev'),
                                            ('WATER', '{{coolant}}°', '', 'fg'), ('DATE', '{{date}}', '', 'fg')])):
        for i, (head, tok, unit, col) in enumerate(cells):
            w += cell('%s%d' % (side, i), x0 + 10 + (i % 2) * 200, 552 + (i // 2) * 52, head, tok, unit, col)
        w += [fill(side + '_vr', x0 + 196, 556, 1, 92, 'frame', z=2),
              fill(side + '_hr', x0, 601, 390, 1, 'frame', z=2)]
    return {
        'schemaVersion': 2, 'name': 'Heritage', 'theme': 'heritage', 'units': 'metric', 'packWaste': 3,
        'engine': {'powerKw': 135, 'torqueNm': 300},
        '_about': 'Heritage cluster: an F80 M3 (2015), generated by tools/gen_dials.py (edit that and regenerate), always '
                  'in km/h and C ("units": "metric"). Two big dials side by side with chrome rings open at the bottom, '
                  'grey faces, white ticks and numerals, thin red needles on dark hubs: the speed (linear 0-280) and the '
                  'revs (0-7, a red block from the Redline setting, the M stripe and ENGINE ON / OFF in its face). Small '
                  'fuel (0 1/2 1) and oil (70 120 170) gauges outboard. Between the dials at the bottom the speed, the '
                  'gear (red at the shift point) and the drive mode. A status pill in the speedo (green ALL SYSTEMS OK, '
                  'amber or red with the reason), a trip computer under the fuel gauge, the hybrid battery, electric '
                  'range, water and the date under the oil gauge. Widget reference: shared/hud.js.',
        'widgets': w + strip(),
    }

def main():
    for name, fn in (('mperf', mperf), ('mcomp', mcomp), ('ielec', ielec), ('heritage', heritage)):
        with open(os.path.join(OUT, name + '.json'), 'w') as f:
            json.dump(fn(), f, indent=2)
            f.write('\n')
        print('wrote', name)


if __name__ == '__main__':
    main()
