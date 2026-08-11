class DnaSeq:
    def __init__(self, accession, seq):
        if accession is None or accession == '':
            raise ValueError('accession must be a non-empty string')
        if seq is None or seq == '':
            raise ValueError('sequence must be a non-empty string')
        self.accession = accession
        self.seq = seq

    def __len__(self):
        return len(self.seq)

    def __str__(self):
        return f"<DnaSeq accession={self.accession}>"


def read_dna(filename):
    import os
    base = os.path.dirname(__file__)
    path = filename if os.path.isabs(filename) else os.path.join(base, filename)
    items = []
    accession = None
    seq_parts = []
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.rstrip('\n')
            if not line:
                continue
            if line.startswith('>'):
                if accession is not None:
                    items.append(DnaSeq(accession, ''.join(seq_parts)))
                accession = line[1:].strip()
                seq_parts = []
            else:
                seq_parts.append(line.strip())
    if accession is not None:
        items.append(DnaSeq(accession, ''.join(seq_parts)))
    return items


def check_exact_overlap(left, right, min_overlap=10):
    """Return the length of the longest exact overlap where a suffix of
    `left.seq` equals a prefix of `right.seq`. Overlaps shorter than
    `min_overlap` are ignored; return 0 if none found.

    Parameters:
    - left: DnaSeq for the left sequence (the suffix comes from this sequence)
    - right: DnaSeq for the right sequence (the prefix comes from this sequence)
    - min_overlap: minimal overlap length to consider (default 10)
    """
    a = left.seq
    b = right.seq
    max_k = min(len(a), len(b))
    best = 0
    for k in range(min_overlap, max_k + 1):
        if a[-k:] == b[:k]:
            best = k
    return best


def overlaps(data, overlap_fn):
    """Return a dict-of-dicts mapping accession pairs to overlap lengths.

    Only include entries where an overlap is found (omit empty rows).
    """
    res = {}
    for left in data:
        row = {}
        for right in data:
            if left is right:
                continue
            val = overlap_fn(left, right)
            if val:
                row[right.accession] = val
        if row:
            res[left.accession] = row
    return res


#
# Testing code. You should not change any line after this one!
#
def test_class_DnaSeq():
    s1 = DnaSeq('s1', 'ACGT')
    s2 = DnaSeq('s2', 'ATGTTTGTTTTTCTTGTTTTATTGCCACTAGTCTCTAGTCAGTGTGTTAATCTTACAACCAGAACTCAAT')
    assert len(s1) == 4, 'Your length method (__len__) is not correct.'
    assert len(s2) == 70, 'Your length method (__len__) is not correct.'

    assert str(s1) == '<DnaSeq accession=s1>', 'The __str__ method is not following the specification.'
    assert str(s2) == '<DnaSeq accession=s2>', 'The __str__ method is not following the specification.'

    # The rest of this function is verifying that we are indeed raising an exception.
    status = 0
    try:
        s3 = DnaSeq('', 'ACGT')
    except ValueError:
        status += 1
    try:
        s3 = DnaSeq('s3', None)
    except ValueError:
        status += 1

    try:
        s3 = DnaSeq(None, '')
    except ValueError:
        status += 1
    if status != 3:
        raise Exception('class DnaSeq does not raise a ValueError '
                        'exception with initialised with empty '
                        'accession and sequence.')
    print('DnaSeq passed')


def test_reading():
    dna1 = read_dna('ex1.fa')
    assert len(dna1) == 6, 'The file "ex1.fa" has exactly 6 sequences, but your code does not return that.'
    assert list(map(lambda x: x.accession, dna1)) == [f's{i}' for i in range(6)], 'The accessions are not read correctly'
    print('read_dna passed')


def test_overlap():
    s0 = DnaSeq('s0', 'AAACCC')
    s1 = DnaSeq('s1', 'CCCGGG')
    s2 = DnaSeq('s2', 'TTTTCC')
    data1 = [s0, s1, s2]
    assert check_exact_overlap(s0, s1, 2) == 3
    assert check_exact_overlap(s0, s1) == 0
    assert check_exact_overlap(s1, s2, 2) == 0
    assert check_exact_overlap(s2, s1, 2) == 2

    res0 = overlaps(data1, lambda s1, s2: check_exact_overlap(s1, s2, 2))
    assert len(res0) == 2, 'You get the wrong number of overlaps'
    assert res0 == {'s0': {'s1': 3}, 's2': {'s1': 2}}

    dna_data = read_dna('ex1.fa')
    res1 = overlaps(dna_data, check_exact_overlap)
    assert len(res1) == 5
    for left, right in [('s0', 's1'), ('s1', 's2'), ('s2', 's3'), ('s3', 's4'), ('s4', 's5')]:
        assert res1[left][right], f'Missing overlap of {left} and {right} (in that order)'
    print('overlap code passed')



def test_all():
    test_class_DnaSeq()
    test_reading()
    test_overlap()
    print('Yay, all good')
