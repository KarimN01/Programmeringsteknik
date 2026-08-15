import shutil
from pathlib import Path

ROOT = Path(__file__).parent
INTERNAL = ROOT / '_internal'
INTERNAL.mkdir(exist_ok=True)

def move_if_exists(p: Path):
    if p.exists():
        target = INTERNAL / p.name
        if target.exists():
            # avoid overwrite
            target = INTERNAL / (p.stem + '_1' + p.suffix)
        shutil.move(str(p), str(target))
        print('Moved', p, '->', target)

# Files inside Projekt to move
for name in ('extract_pdf_text.py', 'test_sample.csv', 'generate_report.py', 'clean_handin.py'):
    move_if_exists(ROOT / name)

# Move instruction PDFs (project/instructionation documents) into internal
for pdf_name in ('Generella instruktioner.pdf', 'Fjärilsutbredning.pdf'):
    move_if_exists(ROOT / pdf_name)

# directory extracted_texts
move_if_exists(ROOT / 'extracted_texts')

# Move any stray per-species pdfs in workspace root
workspace = ROOT.parent
for f in workspace.glob('Gronsnabbvinge_*.pdf'):
    move_if_exists(f)

print('Cleanup done. Internal files moved to', INTERNAL)
