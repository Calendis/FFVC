from components import bus

'''
    Virtual keyboard driver for FFVC
    Just a pygame loop that writes a byte to reserved mem addrs 23, 24

    Byte format:
    --------------------------------------
    23: X X X X X X X X
    24: 0 1 2 3 4 5 6 7

    23 - specified charater
    24:
        0: Shift key
        1: Caps lock
        2: Ctrl
        3: Alt
        4: Meta
        5: Delta (changes to 0 upon keyup and 1 upon keydown)
        6:
        7: Backspace (takes priority)

'''

# Maps ASCII to the arbitrary encoding I use for FFVC
ascii_to_ffvcte = {
    0: 0x00,
    2: 0x01,
    3: 0x02,
    9: 0x0f,
    13: 0x05,
    27: 0x07,
    32: 0x4e,
    33: 0x63,
    34: 0x5f,
    35: 0x65,
    36: 0x66,
    37: 0x67,
    38: 0x69,
    39: 0x55,
    40: 0x6b,
    41: 0x6c,
    42: 0x6a,
    43: 0x5a,
    44: 0x56,
    45: 0x4f,
    46: 0x57,
    47: 0x58,
    48: 0x10,
    49: 0x11,
    50: 0x12,
    51: 0x13,
    52: 0x14,
    53: 0x15,
    54: 0x16,
    55: 0x17,
    56: 0x18,
    57: 0x19,
    58: 0x5e,
    59: 0x54,
    60: 0x60,
    61: 0x50,
    62: 0x61,
    63: 0x62,
    64: 0x64,
    65: 0x34,
    66: 0x35,
    67: 0x36,
    68: 0x37,
    69: 0x38,
    70: 0x39,
    71: 0x3a,
    72: 0x3b,
    73: 0x3c,
    74: 0x3d,
    75: 0x3e,
    76: 0x3f,
    77: 0x40,
    78: 0x41,
    79: 0x42,
    80: 0x43,
    81: 0x44,
    82: 0x45,
    83: 0x46,
    84: 0x47,
    85: 0x48,
    86: 0x49,
    87: 0x4a,
    88: 0x4b,
    89: 0x4c,
    90: 0x4d,
    91: 0x51,
    92: 0x53,
    93: 0x52,
    94: 0x68,
    95: 0x59,
    96: 0x6d,
    97: 0x1a,
    98: 0x1b,
    99: 0x1c,
    100: 0x1d,
    101: 0x1e,
    102: 0x1f,
    103: 0x20,
    104: 0x21,
    105: 0x22,
    106: 0x23,
    107: 0x24,
    108: 0x25,
    109: 0x26,
    110: 0x27,
    111: 0x28,
    112: 0x29,
    113: 0x2a,
    114: 0x2b,
    115: 0x2c,
    116: 0x2d,
    117: 0x2e,
    118: 0x2f,
    119: 0x30,
    120: 0x31,
    121: 0x32,
    122: 0x33,
    123: 0x5b,
    124: 0x5d,
    125: 0x5c,
    126: 0x6e

}

def parse_keys(x):
    #print(x)
    pygame_key = x.dict

    shift = pygame_key["mod"]
    ascii = pygame_key["key"]

    # We must convert from ASCII (used by pygame)...
    # ... to FFVC's custom encoding
    try:
        keycode = ascii_to_ffvcte[ascii]

    except KeyError:
        print("Keyboard driver: unsupported input!")
        return

    bus.io(1, 23, keycode)  # Addr 23 is the first input byte
