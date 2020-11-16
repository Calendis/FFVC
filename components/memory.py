from math import ceil

'''
    Memory block object for VM
    The first 32 bytes are RESERVED
    
    Address   | Slice | Purpose
    ----------------------------------------------
    0 to 3     | 0:4    | block size
    4 to 8     | 4:9    | earliest writeable address
    9 to 11    | 9:12   | cpu registers
        9     OPC
        10-11 IPT
    12 to 21   | 12:22  | display registers
        12-20 palette
        21    mode
    22 to 31   | 22:32  | free registers
'''

reserved_bytes = 32


def memory_msg(status_code, *args):
    status_messages = [
        "Out-of-bounds read at address",
        "Out-of-bounds write at address",
        "Memory is in read-only mode",
        "Write to read-only address"
    ]

    if status_code not in range(0, len(status_messages)):
        msg = "Unknown status code"
    else:
        msg = status_messages[status_code]

    print("Memory message:", msg, *args)


class MemBlock:
    def __init__(self, size, write_allowed):
        # Check to make sure memory size is valid
        if size - 1 > 4294967295:
            print("Memory block size", size, "too large. Max is", 4294967296)
            quit()
        elif size < 16:
            print("Memory block size", size, "too small. Min is", 16)
            quit()

        self.data = bytearray(size)

        # First four bytes store block size
        self.data[0:4] = size.to_bytes(4, "little")

        # Fifth byte stores whether writing is allowed
        self.data[4:5] = write_allowed.to_bytes(1, "little")

        # The first nine bytes shouldn't be attempted to be written to
        # The remaining 23 reserved bytes are registers and can be written to
        self.set_write_bound(9)

    def __getitem__(self, getargs):

        # Read defaults to one byte
        if type(getargs) == tuple:
            loc, size = getargs
        elif type(getargs) == int:
            loc = getargs
            size = 1

        return self.read(loc, size)

    def __setitem__(self, key, value):
        self.write(key, value)

    def read(self, loc, size):
        # Make sure read address exists
        if loc + size > self.get_size():
            memory_msg(0, loc)
            quit()

        # Read and return value as bytes
        return self.data[loc:loc + size]

    def write(self, loc, val):
        # Make sure value is in bytes format
        if type(val) == int:
            intsize = max(1, ceil(val.bit_length() / 8))
            val = val.to_bytes(intsize, 'little')

        # Determine size of data to write
        size = len(val)

        # Make sure writing is permitted
        if self.is_read_only():
            memory_msg(2)
            quit()

        # Make sure enough memory exists to write the data
        elif loc + size > self.get_size():
            memory_msg(1, loc)
            quit()

        # Make sure the specified location permits writing
        elif loc < self.get_write_bound():
            memory_msg(3, loc)
            quit()

        # If all goes well, write the data!
        self.data[loc:loc + size] = val

    def get_size(self):
        return int.from_bytes(self.data[0:4], "little")

    def is_read_only(self):
        return not (bool.from_bytes(self.data[4:5], "little"))

    def get_write_bound(self):
        return int.from_bytes(self.data[5:10], "little")

    def set_write_bound(self, loc):
        self.data[5:10] = loc.to_bytes(4, "little")
