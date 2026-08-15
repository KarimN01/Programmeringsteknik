import sys
from pathlib import Path

# Provide importlib.metadata shim for Python < 3.8 when importlib-metadata is installed
try:
    import importlib.metadata as _importlib_metadata
except Exception:
    try:
        import importlib_metadata as _importlib_metadata
        sys.modules['importlib.metadata'] = _importlib_metadata
    except Exception:
        _importlib_metadata = None

PdfReader = None
try:
    from pypdf import PdfReader  # type: ignore
except Exception:
    PdfReader = None

if PdfReader is None:
    try:
        from pdfminer.high_level import extract_text
    except Exception:
        print('Missing pypdf and pdfminer; please install with: pip install pypdf pdfminer.six', file=sys.stderr)
        raise

ROOT = Path(__file__).parent
OUTDIR = ROOT / 'extracted_texts'
OUTDIR.mkdir(exist_ok=True)

for pdf in ROOT.glob('*.pdf'):
    try:
        if PdfReader is not None:
            reader = PdfReader(str(pdf))
            texts = []
            for p in reader.pages:
                try:
                    texts.append(p.extract_text() or '')
                except Exception:
                    texts.append('')
            content = '\n\n'.join(texts)
        else:
            # use pdfminer
            content = extract_text(str(pdf)) or ''

        out = OUTDIR / (pdf.stem + '.txt')
        out.write_text(content, encoding='utf-8')
        print(f'Wrote {out}')
    except Exception as e:
        print(f'Failed to read {pdf}: {e}', file=sys.stderr)
        continue

print('Done')
