import os

from components import bus
from random import randint

# Get useful magic numbers
resolution = bus.vid.true_resolution
colour_bound = bus.vid.colour_bound
text_bound = bus.vid.text_bound
palette_bound = bus.vid.palette_bound
mode_bound = bus.vid.mode_bound

ram_bound = bus.mapping["vram"][0]


def bios_msg(status_code, *args):
    status_messages = [
        "Booting...",
        "File not found",
        "Bad header"
    ]

    if status_code not in range(0, len(status_messages)):
        msg = "Unknown status code"
    else:
        msg = status_messages[status_code]

    print("BIOS message:", msg, *args)


def power_on():
    # Show boot message
    bios_msg(0)

    # Load default palette
    default_palette = open("files/default_palette.txt", 'r').read().split('\n')
    default_palette = [int(bs, 2) for bs in default_palette]
    default_palette_bytes = bytearray(len(default_palette))
    for i in range(len(default_palette)):
        default_palette_bytes[i] = default_palette[i]

    bus.io(1, ram_bound + text_bound, default_palette_bytes)

    # Display boot image on screen
    draw_coords = open("files/boot_img.txt", 'r').read().split('\n')
    test_img_bitstring = ""
    for i in range(resolution[0] * resolution[1]):
        if str(i) in draw_coords:
            test_img_bitstring += '001'
        else:
            test_img_bitstring += '000'

    test_img_bitstring = [test_img_bitstring[i:i + 8] for i in range(0, len(test_img_bitstring), 8)]
    test_img_ints = [int(v, 2) for v in test_img_bitstring]
    test_img = bytearray(len(test_img_ints))
    for i in range(len(test_img_ints)):
        test_img[i] = test_img_ints[i]
    bus.io(1, ram_bound, test_img)

    # Play test sound
    pass

    await_input()


# Very basic operating system for the virtual computer written in Python, of course
# Eventually, I'd like to write the operating system on the machine itself
def await_input():
    while True:
        x = input("? ")

        if x == "randimg":
            rand_img = bytearray(colour_bound)
            for i in range(len(rand_img)):
                rand_img[i] = randint(0, 255)
            bus.io(1, ram_bound, rand_img)

        elif x == "randpal":
            rand_p = bytearray(8)
            for i in range(len(rand_p)):
                rand_p[i] = randint(0, 255)

            bus.io(1, ram_bound + text_bound, rand_p)
            #refresh_display()

        elif x == "testimg":
            test_image = bytearray(colour_bound)
            for i in range(len(test_image)):
                test_image[i] = int(i * 255 / 24000)
            bus.io(1, ram_bound, test_image)

        elif x == "loadprog":
            path = input(" path: ")
            if not os.path.isfile(path):
                bios_msg(1)
                quit()

            prog = open(path, 'rb').read()
            header = prog[:4]
            if header[:3].decode("ASCII", "ignore") != "9I6":
                bios_msg(2, *header)
                quit()

            prog = prog[4:]  # Discard the 4-byte header
            bus.processor.process_instructions(prog)

        elif x == "showgvram":
            memcpy = bus.io(2, ram_bound, colour_bound-ram_bound)
            print(*memcpy)

        elif x == "showtvram":
            memcpy = bus.io(2, colour_bound+ram_bound, text_bound-colour_bound)
            print(*memcpy)

        elif x == "showram":
            memcpy = bus.io(2, 0, ram_bound)
            print(*memcpy)

        elif x == "showpal":
            memcpy = bus.io(2, palette_bound-8+ram_bound, 8)
            print(*memcpy)

        elif x == "textmode":
            # Set mode byte
            newmode = 1
            bus.io(1, ram_bound + palette_bound, newmode.to_bytes(1, "little"))

        elif x == "graphicsmode":
            newmode = 0
            bus.io(1, ram_bound + palette_bound, newmode.to_bytes(1, "little"))

        elif x == "loadfont":
            # Load font into RAM
            font = open("files/font2.bgt", 'rb').read()
            bus.io(1, 532, font)

        elif x == "clearram":
            # Clear program memory, but not the first 32 bytes of ram, or VRAM
            bus.io(1, 32, bytes(999-32))

        elif x == "quit":
            quit()

        else:
            print("unknown command")

        refresh_display()


def refresh_display():
    gvram = bus.io(2, ram_bound, mode_bound)
    bus.io(1, ram_bound, gvram)


power_on()
