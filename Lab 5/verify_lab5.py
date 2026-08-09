import sys
import inspect
from io import StringIO
from contextlib import redirect_stdout

import os
# ensure Lab 5 folder is on path (script is inside Lab 5)
sys.path.insert(0, os.path.dirname(__file__) or '.')
import dna

def fail(msg):
	print('FAIL:', msg)

def ok(msg):
	print('OK:', msg)

# 1. DnaSeq behavior
try:
	s = dna.DnaSeq('abc','ACGT')
	assert len(s)==4
	assert str(s)=="<DnaSeq accession='abc'>"
	ok('DnaSeq __len__ and __str__')
except Exception as e:
	fail('DnaSeq basic: '+str(e))

for bad in [('', 'ACGT'), ('s',''), (None,'A')]:
	try:
		dna.DnaSeq(*bad)
		fail(f'DnaSeq should raise for {bad}')
	except ValueError:
		ok(f'DnaSeq raises ValueError for {bad}')

# 2. read_dna
try:
	res = dna.read_dna('ex1.fa')
	assert len(res)==6
	assert [x.accession for x in res]==[f's{i}' for i in range(6)]
	ok('read_dna reads ex1.fa correctly')
except Exception as e:
	fail('read_dna: '+str(e))

# 3. check_exact_overlap signature and docstring
try:
	sig = inspect.signature(dna.check_exact_overlap)
	params = list(sig.parameters.values())
	assert params[-1].default==10
	assert dna.check_exact_overlap.__doc__ and 'min_overlap' in dna.check_exact_overlap.__doc__
	ok('check_exact_overlap signature and docstring')
except Exception as e:
	fail('check_exact_overlap: '+str(e))

# behavior tests copied from lab
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
	fail('check_exact_overlap behavior: '+str(e))

# 4. overlaps behavior and no extraneous prints
try:
	data1 = [s0,s1,s2]
	buf = StringIO()
	with redirect_stdout(buf):
		res0 = dna.overlaps(data1, lambda a,b: dna.check_exact_overlap(a,b,2))
	out = buf.getvalue()
	assert out==''
	assert len(res0)==2
	assert res0=={'s0':{'s1':3}, 's2':{'s1':2}}
	ok('overlaps behavior and no printing')
except Exception as e:
	fail('overlaps: '+str(e))

print('\nVerification finished')
