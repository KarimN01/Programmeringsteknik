import os, sys, inspect
from io import StringIO
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__) or '.')
import dna

passed = []
failed = []

def ok(msg):
    print('OK: ' + msg)
    passed.append(msg)

def fail(msg):
    print('FAIL: ' + msg)
    failed.append(msg)

# 1. Class and methods exist
try:
    assert hasattr(dna, 'DnaSeq')
    c = dna.DnaSeq
    assert callable(c)
    assert hasattr(c, '__init__')
    assert hasattr(c, '__str__')
    assert hasattr(c, '__len__')
    ok('DnaSeq class and methods exist')
except Exception as e:
    fail('DnaSeq class/methods: ' + str(e))

# 2. __len__ returns len(seq)
try:
    s = dna.DnaSeq('id','ACGTAC')
    assert len(s) == 6
    ok('__len__ returns sequence length')
except Exception as e:
    fail('__len__: ' + str(e))

# 3. __str__ format
try:
    s = dna.DnaSeq('abc123','A')
    assert str(s) == "<DnaSeq accession='abc123'>"
    ok("__str__ format with single quotes")
except Exception as e:
    fail('__str__: ' + str(e))

# 4. constructor raises ValueError on empty accession/seq
for args in [('', 'ACGT'), (None,'A'), ('s', ''), ('s', None)]:
    try:
        dna.DnaSeq(*args)
        fail(f'Constructor did not raise for {args}')
    except ValueError:
        ok(f'Constructor raises ValueError for {args}')

# 5. read_dna reads provided files and returns DnaSeq list
try:
    res = dna.read_dna('ex1.fa')
    assert isinstance(res, list)
    assert all(isinstance(x, dna.DnaSeq) for x in res)
    ok('read_dna returns list of DnaSeq')
except Exception as e:
    fail('read_dna basic: ' + str(e))

# 6. read_dna ignores blank lines and concatenates multi-line sequences
try:
    tmp = os.path.join(os.path.dirname(__file__), 'tmp_test.fa')
    with open(tmp,'w',encoding='utf-8') as fh:
        fh.write('>a\n')
        fh.write('ACG\n')
        fh.write('\n')
        fh.write('T\n')
        fh.write('>b\n')
        fh.write('GATT\n')
    seqs = dna.read_dna('tmp_test.fa')
    os.remove(tmp)
    assert len(seqs)==2
    assert seqs[0].accession == 'a' and seqs[0].seq == 'ACGT'
    assert seqs[1].seq == 'GATT'
    ok('read_dna ignores blank lines and concatenates multiline sequences')
except Exception as e:
    fail('read_dna blank/multiline: ' + str(e))

# 7. check_exact_overlap signature default and docstring
try:
    sig = inspect.signature(dna.check_exact_overlap)
    params = list(sig.parameters.values())
    assert params[-1].default == 10
    assert dna.check_exact_overlap.__doc__ and 'min_overlap' in dna.check_exact_overlap.__doc__
    ok('check_exact_overlap signature and docstring')
except Exception as e:
    fail('check_exact_overlap signature/doc: ' + str(e))

# 8. check_exact_overlap behavior
try:
    s0 = dna.DnaSeq('s0','AAACCC')
    s1 = dna.DnaSeq('s1','CCCGGG')
    s2 = dna.DnaSeq('s2','TTTTCC')
    assert dna.check_exact_overlap(s0,s1,2)==3
    assert dna.check_exact_overlap(s0,s1)==0
    assert dna.check_exact_overlap(s1,s2,2)==0
    assert dna.check_exact_overlap(s2,s1,2)==2
    ok('check_exact_overlap behavior')
except Exception as e:
    fail('check_exact_overlap behavior: ' + str(e))

# 9. overlaps behavior and dict-of-dicts, no empty entries
try:
    data1 = [s0,s1,s2]
    res0 = dna.overlaps(data1, lambda a,b: dna.check_exact_overlap(a,b,2))
    assert isinstance(res0, dict)
    assert res0 == {'s0': {'s1': 3}, 's2': {'s1': 2}}
    ok('overlaps returns correct dict-of-dicts and omits empty entries')
except Exception as e:
    fail('overlaps behavior: ' + str(e))

# 10. functions do not print
try:
    buf = StringIO()
    with redirect_stdout(buf):
        dna.read_dna('ex1.fa')
        dna.check_exact_overlap(s0,s1)
        dna.overlaps(data1, lambda a,b: dna.check_exact_overlap(a,b,2))
    out = buf.getvalue()
    assert out == ''
    ok('No extraneous printing from core functions')
except Exception as e:
    fail('Printing check: ' + str(e))

print('\nSummary:')
print('Passed:', len(passed))
print('Failed:', len(failed))
if failed:
    print('\nFailed items:')
    for f in failed:
        print('-', f)
else:
    print('All Krav satisfied')
