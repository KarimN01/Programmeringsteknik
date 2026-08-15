from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / 'report.pdf'


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
    lines1 = [
        'Projekt: Fjärilars utbredning — kort rapport',
        '1) Uppgift som implementerats:',
        '   E-nivå: Analys av Artportalens fjärilsdata — diagram för nordligaste',
        '   observation per år, antal observationer per år, samt veckovis för 2022.',
        '',
        '2) Hur programmet startas och används:',
        '   - Kör scriptet: python butterfly_analysis.py --csv <file-or-dir> [--species NAME]',
        '   - För flera filer: use --csv <dir> --all --outdir <plots_dir>',
        '',
        '   Example: python Projekt/butterfly_analysis.py --csv Projekt/butterfly_data --all --outdir Projekt/plots',
        '',
        '3) Bibliotek / installation:',
        '   - matplotlib, numpy (see Projekt/requirements.txt)',
        '   - Install: python -m pip install --user -r Projekt/requirements.txt',
        '',
        '4) Programstruktur (viktiga filer):',
        '   - butterfly_analysis.py : huvudsakligt skript (CSV -> PDF-figurer)',
        '   - extract_pdf_text.py : helper used earlier to extract PDFs (not required)',
        '   - generate_report.py : genererar denna PDF',
        '   - requirements.txt, README.md, Projekt/plots/ (figurer)'
    ]

    lines2 = [
        'Kort reflektion och kontrollpunkter',
        '- Läsning med csv.DictReader (delimiter=";") utan pandas.',
        '- Enkel aggregering: max(nord) per år, räkna observationer per år, veckovis 2022',
        '  och beräkna 5/95 percentiler för 90%-intervallet.',
        '- Figurer sparas i PDF-format i angiven utmappning.',
        '',
        'Appendix: exempel på figurer (PDF-filer) finns i Projekt/plots/',
    ]

    # attempt to embed two thumbnails from Projekt/plots if available
    plots_dir = ROOT / 'plots'
    thumb1 = None
    thumb2 = None
    if plots_dir.exists():
        # prefer a northernmost and a weekly thumbnail for Grönsnabbvinge if present
        candidates = list(plots_dir.glob('*_northernmost_per_year.png'))
        if candidates:
            thumb1 = candidates[0]
        candidates = list(plots_dir.glob('*_weekly_2022.png'))
        if candidates:
            thumb2 = candidates[0]

    img1 = make_page(lines1)
    img2 = make_page(lines2)

    # paste thumbnails if found
    def paste_thumb(page_img, thumb_path, xpos=200, ypos=200, maxw=800, maxh=600):
        try:
            t = Image.open(str(thumb_path))
            t.thumbnail((maxw, maxh))
            page_img.paste(t, (xpos, page_img.height - ypos - t.height))
        except Exception:
            pass

    if thumb1:
        paste_thumb(img1, thumb1, xpos=150, ypos=400, maxw=1000, maxh=600)
    if thumb2:
        paste_thumb(img1, thumb2, xpos=150, ypos=1200, maxw=1000, maxh=600)

    img1.save(str(OUT), 'PDF', resolution=300, save_all=True, append_images=[img2])


if __name__ == '__main__':
    write_report()
    print('Wrote', OUT)
