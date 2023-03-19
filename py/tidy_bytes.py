CP1252 = {
    128: [226, 130, 172],
    129: None,
    130: [226, 128, 154],
    131: [198, 146],
    132: [226, 128, 158],
    133: [226, 128, 166],
    134: [226, 128, 160],
    135: [226, 128, 161],
    136: [203, 134],
    137: [226, 128, 176],
    138: [197, 160],
    139: [226, 128, 185],
    140: [197, 146],
    141: None,
    142: [197, 189],
    143: None,
    144: None,
    145: [226, 128, 152],
    146: [226, 128, 153],
    147: [226, 128, 156],
    148: [226, 128, 157],
    149: [226, 128, 162],
    150: [226, 128, 147],
    151: [226, 128, 148],
    152: [203, 156],
    153: [226, 132, 162],
    154: [197, 161],
    155: [226, 128, 186],
    156: [197, 147],
    157: None,
    158: [197, 190],
    159: [197, 184]
}

def tidy_byte(byte):
    if byte < 160:
        return CP1252[byte]
    elif byte < 192:
        return [194, byte]
    else:
        return [195, byte - 64]

def tidy_bytes(string, force=False):
    bytes_list = list(string.encode('latin-1'))

    if force:
        return bytearray([b for tidy_byte_list in (tidy_byte(b) for b in bytes_list) if tidy_byte_list for b in tidy_byte_list]).decode('utf-8', 'replace')

    conts_expected = 0
    last_lead = 0

    for i, byte in enumerate(bytes_list):
        is_ascii = byte < 128
        is_cont = 127 < byte < 192
        is_lead = 191 < byte < 245
        is_unused = byte > 240
        is_restricted = byte > 244

        if is_unused or is_restricted:
            bytes_list[i] = tidy_byte(byte)
        elif is_cont:
            if conts_expected == 0:
                bytes_list[i] = tidy_byte(byte)
            else:
                conts_expected -= 1
        else:
            if conts_expected > 0:
                for j in range(1, i - last_lead + 1):
                    bytes_list[i - j] = tidy_byte(bytes_list[i - j])
                conts_expected = 0

            if is_lead:
                if i == len(bytes_list) - 1:
                    bytes_list[i] = tidy_byte(bytes_list[-1])
                else:
                    conts_expected = 1 if byte < 224 else 2 if byte < 240 else 3
                    last_lead = i

    tidy_byte_lists = [tidy_byte_list for tidy_byte_list in (tidy_byte(b) for b in bytes_list) if tidy_byte_list]
    return bytearray([b for tidy_byte_list in tidy_byte_lists for b in tidy_byte_list]).decode('utf-8', 'replace')
