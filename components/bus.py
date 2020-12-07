from components import memory, display, processor
from math import ceil

# ALL RANGES ARE INCLUSIVE
mapping = {
    "ram": (0, 33009),
    "vram": (1000, 33009),
    "snd": (33010, 33143),
}
min_addr = 0
max_addr = 33143

ram_size = mapping["ram"][1] - mapping["ram"][0] + 1
vram_size = mapping["vram"][1] - mapping["vram"][0] + 1
snd_size = mapping["snd"][1] - mapping["snd"][0] + 1

mem = memory.MemBlock(ram_size, True)
vid = display.Screen(320, 200, 320, 200)
snd = None

reserved_bytes = memory.reserved_bytes


def bus_msg(status_code, *args):
    status_messages = [
        "Unknown signal",
        "Unmapped address",
        "Invalid mapping for address",
        "Improper data"
    ]
    if status_code not in range(0, len(status_messages)):
        msg = "Unknown status code"
    else:
        msg = status_messages[status_code]

    print("Bus message:", msg, *args)


def io(signal, location, size_or_val):
    # Make sure location exists in memory map
    if location not in range(min_addr, max_addr):
        bus_msg(1, location)
        quit()

    mem_addrs = mapping["ram"]
    vid_addrs = mapping["vram"]
    snd_addrs = mapping["snd"]

    # Read signal
    if signal == 0:
        return int.from_bytes(mem.read(location, size_or_val), "little")

    # Write signal
    elif signal == 1:

        write_device = None
        offset = 0

        # Are we writing to RAM?
        if location in range(mem_addrs[0], mem_addrs[1] + 1):
            offset = mem_addrs[0]

            # RAM and VRAM overlap
            if location in range(vid_addrs[0], vid_addrs[1] + 1):
                write_device = vid
                offset = vid_addrs[0]

        # Are we writing to the audio controller?
        elif location in range(snd_addrs[0], snd_addrs[1] + 1):
            write_device = snd
            offset = snd_addrs[0]

        else:
            bus_msg(2, location)
            quit()

        # Convert to bytes
        if type(size_or_val) != bytearray and type(size_or_val) != bytes:
            val_size = max(1, ceil(size_or_val.bit_length() / 8))
            size_or_val = size_or_val.to_bytes(val_size, "little")

        if write_device is not None:
            write_device.write(location - offset, size_or_val)
        mem.write(location, size_or_val)

    # Read as bytes signal
    elif signal == 2:
        return mem.read(location, size_or_val)

    else:
        bus_msg(0)
        quit()
