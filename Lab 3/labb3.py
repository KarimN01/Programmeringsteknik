def insert_in_sorted(x, sorted_list):
    result = []
    inserted = False

    for item in sorted_list:
        if not inserted and x < item:
            result.append(x)
            inserted = True
        result.append(item)

    if not inserted:
        result.append(x)

    return result


def insertion_sort(my_list):
    out = []

    for item in my_list:
        out = insert_in_sorted(item, out)

    return out


def split_path(filename):
    backslash_index = -1
    slash_index = -1

    index = 0
    while index < len(filename):
        if filename[index] == '\\':
            backslash_index = index
        elif filename[index] == '/':
            slash_index = index
        index += 1

    last_separator = backslash_index
    if slash_index > last_separator:
        last_separator = slash_index

    if last_separator == -1:
        return '', filename

    return filename[:last_separator + 1], filename[last_separator + 1:]


def canonical_word(word):
    word = word.lower()
    word = word.replace('å', 'aa')
    word = word.replace('ä', 'ae')
    word = word.replace('ö', 'oe')
    return word


def number_lines(f):
    input_file = open(f, 'r', encoding='utf-8')
    directory, base_name = split_path(f)
    output_file = open(directory + 'numbered_' + base_name, 'w', encoding='utf-8')

    line_number = 0
    for line in input_file:
        output_file.write(str(line_number) + ' ' + line)
        line_number += 1

    input_file.close()
    output_file.close()


def index_text(filename):
    input_file = open(filename, 'r', encoding='utf-8')
    index = {}

    for line_number, line in enumerate(input_file):
        words_in_line = line.lower().split()
        seen_in_line = []

        for word in words_in_line:
            if word in seen_in_line:
                continue

            seen_in_line.append(word)
            if word not in index:
                index[word] = [line_number]
            elif index[word][-1] != line_number:
                index[word].append(line_number)

    input_file.close()
    return index


def important_words(an_index, stop_words):
    normalized_stop_words = []
    for word in stop_words:
        normalized_stop_words.append(canonical_word(word))

    frequency_pairs = []
    for word in an_index:
        if canonical_word(word) in normalized_stop_words:
            continue
        frequency_pairs.append((-len(an_index[word]), word))

    frequency_pairs = insertion_sort(frequency_pairs)

    result = []
    for pair in frequency_pairs[:5]:
        result.append(pair[1])

    return result


def main():
    stop_words = ['och', 'jag', 'som', 'det', 'för']

    while True:
        filename = input('En textfil: ')
        try:
            index = index_text(filename)
        except FileNotFoundError:
            print('Filen hittades inte. Försök igen.')
            continue

        print('De viktigaste orden är:')
        for word in important_words(index, stop_words):
            print(word)
        break


if __name__ == '__main__':
    main()
