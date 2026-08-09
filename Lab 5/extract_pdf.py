import sys
import subprocess
try:
    import PyPDF2
except Exception:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyPDF2'])
    import PyPDF2
from PyPDF2 import PdfReader
import os
pdf_path = os.path.join(os.path.dirname(__file__), 'Labb 5 instruktioner.pdf')
if not os.path.exists(pdf_path):
    raise SystemExit(f'PDF not found: {pdf_path}')
p = PdfReader(pdf_path)
for i, page in enumerate(p.pages):
    text = page.extract_text()
    print('\n---PAGE %d---\n' % (i+1))
    if text:
        print(text)
    else:
        print('[no extractable text]')
# Also dump any occurrence lines containing 'Krav' or 'KRAV'
print('\n---SEARCH FOR KRAV---\n')
for i, page in enumerate(p.pages):
    text = page.extract_text() or ''
    for ln in text.splitlines():
        if 'Krav' in ln or 'KRAV' in ln or 'krav' in ln:
            print(f'PAGE {i+1}:', ln)
