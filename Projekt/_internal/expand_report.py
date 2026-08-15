from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv
import numpy as np

ROOT = Path(__file__).parent.parent
PLOTS = ROOT / 'plots'
DATA = ROOT / 'butterfly_data'
OUT = ROOT / 'report.pdf'


def parse_csv(path: Path):
    # returns list of records with keys art, nord, slut (date string)
    records = []
    with path.open(encoding='utf-8', newline='') as fh:
        reader = csv.DictReader(fh, delimiter=';')
        fields = {k.strip().lower(): k for k in (reader.fieldnames or [])}
        for row in reader:
            art = row.get(fields.get('artnamn', ''), '').strip()
            nord = row.get(fields.get('nord', ''), '').strip()
            slut = row.get(fields.get('slutdatum', ''), '').strip()
            try:
                nordv = float(nord)
            except Exception:
                nordv = None
            # parse year
            year = None
            if slut:
                try:
                    year = int(slut[:4])
                except Exception:
                    year = None
            records.append({'art': art, 'nord': nordv, 'year': year})
    return records


def analyze_file(path: Path):
    recs = parse_csv(path)
    # choose most common species
    from collections import Counter, defaultdict
    c = Counter(r['art'] for r in recs if r['art'])
    species = c.most_common(1)[0][0] if c else path.stem
    # aggregate northernmost per year
    north_by_year = defaultdict(lambda: -1e9)
    years = set()
    for r in recs:
        if r['art'] == species and r['nord'] is not None and r['year']:
            y = r['year']
            years.add(y)
            if r['nord'] > north_by_year[y]:
                north_by_year[y] = r['nord']
    if not north_by_year:
        return {'file': path.name, 'species': species, 'first': None, 'last': None, 'slope': None, 'trend': 'no data'}
    xy = sorted(north_by_year.items())
    xs = np.array([y for y, _ in xy], dtype=float)
    ys = np.array([v for _, v in xy], dtype=float)
    # linear fit
    if len(xs) >= 2:
        m, b = np.polyfit(xs, ys, 1)
        slope = float(m)
    else:
        slope = 0.0
    trend = 'northward' if slope > 1e-6 else ('southward' if slope < -1e-6 else 'stable')
    return {'file': path.name, 'species': species, 'first': int(min(xs)) if len(xs) else None, 'last': int(max(xs)) if len(xs) else None, 'slope': slope, 'trend': trend}


def make_page(text_lines, size_px=(2480, 3508), margin_px=150):
    img = Image.new('RGB', size_px, 'white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 40)
        small = ImageFont.truetype('arial.ttf', 20)
    except Exception:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    x = margin_px
    y = margin_px
    draw.text((x, y), text_lines[0], fill='black', font=font)
    y += 80
    for line in text_lines[1:]:
        draw.text((x, y), line, fill='black', font=small)
        y += 36
    return img


def write_report():
    # analyze all CSVs
    metrics = []
    if DATA.exists():
        for f in sorted(DATA.glob('*.csv')):
            metrics.append(analyze_file(f))

    # build text
    lines1 = [
        'Projekt: Fjärilars utbredning — kort rapport (expanded)',
        'Kort mål: skapa figurer och sammanfatta norrförskjutning per art.'
    ]
    lines1 += ['']
    lines1 += ['Kompakt summary:']
    for m in metrics:
        slope_str = f"{m['slope']:.1f}" if m['slope'] is not None else 'NA'
        lines1.append(f"{m['species']} ({m['file']}): {m['first']}-{m['last']}, slope={slope_str} m/yr, {m['trend']}")

    # table page
    lines2 = ['Detaljerad tabell (species | first | last | slope m/yr | trend)', '']
    for m in metrics:
        slope_str = f"{m['slope']:.1f}" if m['slope'] is not None else 'NA'
        lines2.append(f"{m['species']} | {m['first']} | {m['last']} | {slope_str} | {m['trend']}")

    img1 = make_page(lines1)
    img2 = make_page(lines2)

    # embed two thumbnails if available
    thumb_a = None
    thumb_b = None
    if PLOTS.exists():
        n1 = list(PLOTS.glob('*_northernmost_per_year.png'))
        n2 = list(PLOTS.glob('*_weekly_2022.png'))
        if n1:
            thumb_a = n1[0]
        if n2:
            thumb_b = n2[0]
    if thumb_a:
        try:
            t = Image.open(str(thumb_a))
            t.thumbnail((1000, 600))
            img1.paste(t, (150, img1.height - 900))
        except Exception:
            pass
    if thumb_b:
        try:
            t = Image.open(str(thumb_b))
            t.thumbnail((1000, 600))
            img2.paste(t, (150, img2.height - 900))
        except Exception:
            pass

    img1.save(str(OUT), 'PDF', resolution=300, save_all=True, append_images=[img2])
    print('Wrote expanded report to', OUT)


if __name__ == '__main__':
    write_report()
