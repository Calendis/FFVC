"""
    Compiler for Fun Virtual Computer Assembly Language
    Translates to Fun Virtual Computer machine code

    Bert Myroon
    15 Nov., 2020
"""

from sys import argv
from os import path
from time import time

ASSEMBLER_VERSION = 3
HEADER = bytearray([0x39, 0x49, 0x36, ASSEMBLER_VERSION])


def print_usage(code, *info):
    messages = [
        "Usage:\n    fvcal_assembler.py <source file> <output file>",
        "File not found:"
    ]
    print(messages[code], *info)


def print_err(code, line, *info):
    types = [
        "Syntax error\n",
        "Value error\n"
    ]

    """
        Error message, followed by error type
    """
    messages = {
        "Bad line number": 0,
        "Small or duplicate line number": 1,
        "Bad operator": 0,
        "Wrong number of parameters": 0,
        "Bad parameter": 0,
        "Unprefixed parameter": 0,
        "Unknown line": 1,
    }
    errstr = list(messages.keys())[code]
    print("\nCompilation error:\n")
    print(types[messages[errstr]], errstr, *info, "at", line)
    quit()


"""
    This dictionary maps operators to their required number of parameters, the machine opcode they
    are converted to, and the number of mode parameters used by the processor for this instruction
"""

ops_params_bytecode = {
    "ADD": [3, 0x01, 3],
    "MULT": [3, 0x02, 3],
    "COPY": [2, 0x03, 2],
    "MOVE": [2, 0x04, 2],
    "DONE": [0, 0x05, 0],
    "META": [1, 0x06, 1],
    "JMP": [1, 0x07, 1],
    "JMPNUL": [2, 0x08, 2],
    "JMPEQL": [3, 0x09, 3],
    "ERR": [0, 0x0A, 0],
    "PRINT": [1, 0x03, 1],
    "CPYBLK": [2, 0x0B, 3],
    "MOD": [3, 0x0D, 3],
    "DIV": [3, 0x0E, 3],
    "GOTO": [1, 0x07, 1],
    "GTNUL": [2, 0x08, 2],
    "GTEQL": [3, 0x09, 3]
}

ops_length = {
    "ADD":  9,
    "MULT": 9,
    "COPY": 6,
    "MOVE": 6,
    "DONE": 0,
    "META": 3,
    "JMP":  3,
    "JMPNUL": 6,
    "JMPEQL": 9,
    "ERR": 0,
    "PRINT": 8,
    "CPYBLK": 8,
    "MOD": 9,
    "DIV": 9,
    "GOTO": 3,
    "GTNUL": 6,
    "GTEQL": 9
}

keyword_params_bytecode = {
    "OPC": bytearray([0x09, 0x00]),
    "IPT": bytearray([0x0A, 0x00]),
    "PAL": bytearray([0x0C, 0x00]),
    "MOD": bytearray([0x15, 0x00]),
}

"""
    This dictionary maps characters to their value in FVC Text Encoding
"""
FVCTE_table = {
    '§': 0x05,
    '«': 0x0e,
    '0': 0x10,
    '1': 0x11,
    '2': 0x12,
    '3': 0x13,
    '4': 0x14,
    '5': 0x15,
    '6': 0x16,
    '7': 0x17,
    '8': 0x18,
    '9': 0x19,
    'a': 0x1a,
    'b': 0x1b,
    'c': 0x1c,
    'd': 0x1d,
    'e': 0x1e,
    'f': 0x1f,
    'g': 0x20,
    'h': 0x21,
    'i': 0x22,
    'j': 0x23,
    'k': 0x24,
    'l': 0x25,
    'm': 0x26,
    'n': 0x27,
    'o': 0x28,
    'p': 0x29,
    'q': 0x2a,
    'r': 0x2b,
    's': 0x2c,
    't': 0x2d,
    'u': 0x2e,
    'v': 0x2f,
    'w': 0x30,
    'x': 0x31,
    'y': 0x32,
    'z': 0x33,
    'A': 0x34,
    'B': 0x35,
    'C': 0x36,
    'D': 0x37,
    'E': 0x38,
    'F': 0x39,
    'G': 0x3a,
    'H': 0x3b,
    'I': 0x3c,
    'J': 0x3d,
    'K': 0x3e,
    'L': 0x3f,
    'M': 0x40,
    'N': 0x41,
    'O': 0x42,
    'P': 0x43,
    'Q': 0x44,
    'R': 0x45,
    'S': 0x46,
    'T': 0x47,
    'U': 0x48,
    'V': 0x49,
    'W': 0x4a,
    'X': 0x4b,
    'Y': 0x4c,
    'Z': 0x4d,
}

comment_char = '/'


def compile_fvcal(assembly, out_path):
    start_time = time()
    lines = assembly.split('\n')
    last_number = -1
    if lines == ['']:
        print("Source file is empty")
        quit()

    # Parse code to make sure it's valid...
    # ... and assemble line-address map
    line_address_map = {}
    address = 32
    for line in lines:
        if line.strip() != '':
            s_line = line.split()
            number = s_line[0]

            # Exempt comments from validation
            if number == comment_char:
                number = last_number
                continue

            op = s_line[1]
            params = s_line[2:]

            validate_line(number, op, params, last_number)
            last_number = int(number)

            line_address_map[number] = address            
            address += ops_length[op] + 1
    
    # Code is valid, convert to machine code :)
    print("Code validated, compiling...")
    machine_code = bytearray()
    text_location = 0

    for line in lines:
        # Ignore blank lines
        if line.strip() == '':
            continue

        s_line = line.split()
        # Ignore commented lines
        if s_line[0] == '/':
            continue

        # number = s_line[0]
        op = s_line[1]
        params = s_line[2:]

        op_byte = bytearray([ops_params_bytecode[op][1]])

        prefix_to_byte = {
            '#': 0x00,
            '$': 0x01,
            '%': 0x02,
            '^': 0x03
        }

        # Handle operators that must be expanded to machine code
        # PRINT expands to JMP and CPYBLK
        if op == "PRINT":
            expanded_bytes = bytearray()
            strlen = len(params[0]) - 1
            prefix = params[0][0]

            # Printing a string literal
            if prefix == '\'':
                # First, we insert a jump ahead
                # This allows us to store some text data in the binary
                expanded_bytes.append(0x07)
                expanded_bytes.append(0x02)
                expanded_bytes.append(strlen)
                expanded_bytes.append(0x00)

                # Store the text data
                for i in range(strlen):
                    current_letter = params[0][i + 1]
                    expanded_bytes.append(FVCTE_table[current_letter])

                # Insert a cpyblk to copy the text data into VRAM
                expanded_bytes.append(0x0B)
                expanded_bytes.append(0x00)
                expanded_bytes.append(0x00)
                expanded_bytes.append(strlen)

                # Calculate the address where the text data is stored in the binary
                current_address = len(machine_code) + len(expanded_bytes) + 28 - strlen
                current_address_b = current_address.to_bytes(2, 'little')
                expanded_bytes += current_address_b

                vram_location = 0x61A8 + text_location
                vram_location_b = vram_location.to_bytes(2, "little")

                # The cpyblk instruction will write to the text portion of VRAM
                expanded_bytes += vram_location_b

            # Pointer to 16-bit int
            elif prefix == '#':
                strlen = 2
                expanded_bytes.append(0x0B)  # CPYBLK opcode
                expanded_bytes.append(0x00)
                expanded_bytes.append(0x00)
                expanded_bytes.append(0x02)  # 16-bit int

                addr_to_print = int(params[0][1:])
                expanded_bytes += addr_to_print.to_bytes(2, "little")

                vram_location = 0x61A8 + text_location
                vram_location_b = vram_location.to_bytes(2, "little")

                # The cpyblk instruction will write to the text portion of VRAM
                expanded_bytes += vram_location_b

            machine_code += expanded_bytes
            text_location += strlen

        # GOTO instruction, expands to JMP
        elif op == "GOTO":
            goto_line = params[0][1:]

            try:
                jmp_address = line_address_map[goto_line]

            except KeyError:
                print_err(6, number, goto_line)

            jmp_address_bytes = jmp_address.to_bytes(2, "little")

            expanded_bytes = bytearray()
            expanded_bytes.append(0x07)  # Create JMP instruction
            expanded_bytes.append(0x00)  # Direct mode

            expanded_bytes += jmp_address_bytes
            machine_code += expanded_bytes

        # GTNUL instruction, expands to JMPNUL
        elif op == "GTNUL":
            expanded_bytes = bytearray()

            mode_byte = prefix_to_byte[params[0][0]]
            addr = int(params[0][1:])
            addr_bytes = addr.to_bytes(2, "little")

            goto_line = params[1][1:]
            try:
                jmp_address = line_address_map[goto_line]

            except KeyError:
                print_err(6, number, goto_line)

            jmp_address_bytes = jmp_address.to_bytes(2, "little")

            expanded_bytes.append(0x08)
            expanded_bytes.append(0x00)
            expanded_bytes.append(mode_byte)
            expanded_bytes += jmp_address_bytes
            expanded_bytes += addr_bytes

            machine_code += expanded_bytes

        # GTEQL instruction, expands to JMPEQL
        elif op == "GTEQL":
            expanded_bytes = bytearray()

            mode_byte1 = prefix_to_byte[params[0][0]]
            mode_byte2 = prefix_to_byte[params[1][0]]
            addr1 = int(params[0][1:])
            addr2 = int(params[1][1:])
            addr1_bytes = addr1.to_bytes(2, "little")
            addr2_bytes = addr2.to_bytes(2, "little")
            goto_line = params[2][1:]

            try:
                jmp_address = line_address_map[goto_line]

            except KeyError:
                print_err(6, number, goto_line)

            jmp_address_bytes = jmp_address.to_bytes(2, "little")

            expanded_bytes.append(0x09)
            expanded_bytes.append(0x00)
            expanded_bytes.append(mode_byte1)
            expanded_bytes.append(mode_byte2)
            expanded_bytes += jmp_address_bytes
            expanded_bytes += addr1_bytes
            expanded_bytes += addr2_bytes

            machine_code += expanded_bytes

        # Handle all other operators
        else:
            # Determine modes from prefixes
            mode_count = ops_params_bytecode[op][2]
            mode_prefixes = []
            for mode_param_i in range(mode_count):
                mode_prefixes.append(params[mode_param_i][0])

            # Assemble list of 8-bit modes
            modes = [prefix_to_byte[p] for p in mode_prefixes]

            # Assemble parameters with their respective modes into bytes
            param_bytes = bytearray()
            modes_inserted = 0

            # First, insert the parameter mode arguments
            for param in params:
                while modes_inserted < mode_count:
                    param_bytes.append(modes[modes_inserted])
                    modes_inserted += 1

                no_prefix_param = param[1:]

                # Handle conversion of keyword params to numbers
                if no_prefix_param in list(keyword_params_bytecode.keys()):
                    no_prefix_param = keyword_params_bytecode[no_prefix_param]

                # Handle conversion of normal params to numbers
                else:
                    no_prefix_param = int(no_prefix_param)
                    no_prefix_param = no_prefix_param.to_bytes(2, "little")

                param_bytes += no_prefix_param

            # Store the assembled machine code
            instruction_bytes = op_byte + param_bytes
            machine_code += instruction_bytes

    # Write the assembled binary to disk
    assembled_program = HEADER + machine_code
    out_file = open(out_path, 'wb')
    out_file.write(assembled_program)
    out_file.close()

    end_time = time()
    elapsed = round(end_time - start_time, 3)

    # print(*assembled_program)
    print("Compilation finished in", elapsed, "seconds")


def validate_line(number, op, params, last_number):
    allowed_ops = list(ops_params_bytecode.keys())
    valid_prefixes = ['$', '#', '\'', '%', '^']

    # Make sure line number is valid
    try:
        int(number)
        assert (int(number) > last_number)

    except ValueError:
        print_err(0, number)

    except AssertionError:
        print_err(1, number)

    # Make sure operator is valid
    try:
        assert (op in allowed_ops)

    except AssertionError:
        print_err(2, number, op)

    # Make sure correct number of parameters is used
    try:
        assert (ops_params_bytecode[op][0] == len(params))
    except AssertionError:
        print_err(3, number)

    # Make sure each parameter is valid
    for param in params:
        prefix = param[0]
        prefixed = prefix in valid_prefixes

        # Good, the param has a prefix
        if prefixed:
            # Is the param a string?
            if prefix == '\'':
                pass

            # Is the param a number/address?
            else:
                try:
                    int(param[1:])

                except ValueError:
                    # The param is not a string, number, or address
                    # Is it an address keyword?
                    try:
                        assert (param[1:] in list(keyword_params_bytecode.keys()))

                    except AssertionError:
                        # The param is invalid because it is not a string, number, address, or address keyword
                        print_err(4, number, param)

        # The param is invalid because it does not have a prefix
        else:
            print_err(5, number, param)


def get_input(args):
    if len(args) != 3:
        print_usage(0)
        return 1

    in_path = args[1]
    out_path = args[2]

    if not path.isfile(in_path):
        print_usage(1, in_path)
        return 1

    # Everything seems good!
    assembly = open(in_path, 'r').read()
    print("\nCompiling", in_path, "to", out_path)
    print("------------------------------------")
    compile_fvcal(assembly, out_path)


if __name__ == '__main__':
    get_input(argv)
