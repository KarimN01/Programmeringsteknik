# Uppgift 1a
def int_to_hexa_char(tal):
    hexa_chars = "0123456789ABCDEF"
    return hexa_chars[tal]


# Uppgift 1b
def hexa_char_to_int(symbol):
    hexa_chars = "0123456789ABCDEF"
    return hexa_chars.find(symbol.upper())


# Uppgift 2
def hexa_to_deci(hexa):
    value = 0
    exponent = 0
    i = len(hexa) - 1

    # Vi läser från höger till vänster: först 16^0, sedan 16^1, osv.
    while i >= 0:
        digit = hexa_char_to_int(hexa[i])
        value = value + digit * (16 ** exponent)
        exponent += 1
        i -= 1

    return value


# Uppgift 3
def deci_to_hexa(deci):
    if deci == 0:
        return "0"

    remainders = []
    number = deci

    # Resterna kommer i omvänd ordning (minst signifikant först).
    while number > 0:
        remainder = number % 16
        remainders.append(int_to_hexa_char(remainder))
        number = number // 16

    result = ""
    i = len(remainders) - 1
    while i >= 0:
        result += remainders[i]
        i -= 1

    return result


# Uppgift 4
def remove_prefix(hexa):
    if hexa == "":
        return "0"

    cleaned = hexa
    # Prefix 0x/0X tas bort om det finns.
    if len(cleaned) >= 2 and cleaned[0] == "0" and (cleaned[1] == "x" or cleaned[1] == "X"):
        cleaned = cleaned[2:]

    # Ledande nollor påverkar inte värdet.
    while len(cleaned) > 0 and cleaned[0] == "0":
        cleaned = cleaned[1:]

    if cleaned == "":
        return "0"

    return cleaned


# Uppgift 5
def add_mixed_list(mixed_list, output_form):
    total = 0

    for item in mixed_list:
        if type(item) == int:
            total += item
        else:
            cleaned = remove_prefix(item)
            total += hexa_to_deci(cleaned)

    if output_form == "d":
        return total

    return deci_to_hexa(total)


# Uppgift 6a
def validate_hexa(string):
    if string == "":
        return False

    cleaned = string
    if len(cleaned) >= 2 and cleaned[0] == "0" and (cleaned[1] == "x" or cleaned[1] == "X"):
        cleaned = cleaned[2:]

    if cleaned == "":
        return False

    valid_chars = "0123456789ABCDEF"
    i = 0
    while i < len(cleaned):
        # Vi godkänner både stora och små bokstäver genom att normalisera till versaler.
        char = cleaned[i].upper()
        if valid_chars.find(char) == -1:
            return False
        i += 1

    return True


# Uppgift 6b
def valid_hexa_list(string_list):
    valid_list = []

    for text in string_list:
        if validate_hexa(text):
            valid_list.append(text)

    return valid_list


# if __name__ == "__main__":
    # # Uppgift 1a: int_to_hexa_char
    # print("Uppgift 1a")
    # print(int_to_hexa_char(13))  # D
    # print(int_to_hexa_char(4))   # 4
    # print()

    # # Uppgift 1b: hexa_char_to_int
    # print("Uppgift 1b")
    # print(hexa_char_to_int("5"))  # 5
    # print(hexa_char_to_int("D"))  # 13
    # print()

    # # Uppgift 2: hexa_to_deci
    # print("Uppgift 2")
    # print(hexa_to_deci("3C5"))  # 965
    # print(hexa_to_deci("000"))  # 0
    # print(hexa_to_deci("FF"))   # 255
    # print()

    # # Uppgift 3: deci_to_hexa
    # print("Uppgift 3")
    # print(deci_to_hexa(32))   # 20
    # print(deci_to_hexa(965))  # 3C5
    # print(deci_to_hexa(9))    # 9
    # print()

    # # Uppgift 4: remove_prefix
    # print("Uppgift 4")
    # myHexNum = "0x05B"
    # print(remove_prefix(myHexNum))   # 5B
    # print(remove_prefix("0x00000"))  # 0
    # print(remove_prefix(""))         # 0
    # print()

    # # Uppgift 5: add_mixed_list
    # print("Uppgift 5")
    # small_list = [1, "1"]
    # print(add_mixed_list(small_list, "d"))  # 2
    # print(add_mixed_list(small_list, "h"))  # 2
    # print(small_list)                         # [1, "1"]
    # print(add_mixed_list([1, "0001", "0xA"], "d"))  # 12
    # print(add_mixed_list([0, 0, 0], "h"))             # 0
    # print()

    # # Uppgift 6a: validate_hexa
    # print("Uppgift 6a")
    # print(validate_hexa("Inte ett tal"))  # False
    # print(validate_hexa("0xF1"))          # True
    # print()

    # # Uppgift 6b: valid_hexa_list
    # print("Uppgift 6b")
    # myList = ["0xF1", "glass", "A"]
    # print(valid_hexa_list(myList))  # ["0xF1", "A"]
    # print(myList)                   # ["0xF1", "glass", "A"]
