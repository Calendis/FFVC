"""
    Compiler for Fun Virtual Computer Assembly Language
    Translates to Fun Virtual Computer machine code

    Bert Myroon
    15 Nov., 2020
"""

from sys import argv
from os import path
from time import time

ASSEMBLER_VERSION = 1
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

    messages = {
        "Bad line number": 0,
        "Small or duplicate line number": 1,
        "Bad operator": 0,
        "Wrong number of parameters": 0,
        "Bad parameter": 0,
        "Unprefixed parameter": 0
    }
    errstr = list(messages.keys())[code]
    print(types[messages[errstr]], errstr, *info, "at", line)
    quit()


"""
    This dictionary maps operators to their required number of parameters, the machine opcode they
    are converted to, and the number of mode parameters used by the processor for this instruction
"""
ops_params_bytecode = {
    "ADD": [3, 0x01, 3],
    "MULT": [3, 0x02, 2],
    "COPY": [2, 0x03, 2],
    "MOVE": [2, 0x04, 2],
    "DONE": [0, 0x05, 0],
    "META": [1, 0x06, 1],
    "JMP": [1, 0x07, 1],
    "JMPNUL": [2, 0x08, 2],
    "JMPEQL": [3, 0x09, 3],
    "ERR": [0, 0x0A, 0],
    "PRINT": [1, 0x03, 2]
}

keyword_params_bytecode = {
    "OPC": bytearray([0x09, 0x00]),
    "IPT": bytearray([0x0A, 0x00]),
    "PAL": bytearray([0x0C, 0x00]),
    "MOD": bytearray([0x15, 0x00]),
}


def compile_fvcal(assembly, out_path):
    start_time = time()
    lines = assembly.split('\n')
    last_number = -1
    if lines == ['']:
        print("Source file is empty")
        quit()

    # Parse code to make sure it's valid
    for line in lines:
        if line.strip() != '':
            s_line = line.split()

            number = s_line[0]
            op = s_line[1]
            params = s_line[2:]

            validate_line(number, op, params, last_number)
            last_number = int(number)

    # Code is valid, convert to machine code :)
    print("Code validated, compiling...")
    machine_code = bytearray()

    for line in lines:
        # Ignore blank lines
        if line.strip() == '':
            continue

        s_line = line.split()

        number = s_line[0]
        op = s_line[1]
        params = s_line[2:]

        op_byte = bytearray([ops_params_bytecode[op][1]])

        # Handle special operators that don't have a direct machine code equivalent
        if op == "PRINT":
            pass

        prefix_to_byte = {
            '#': 0x00,
            '$': 0x01,
            '%': 0x02,
            '^': 0x03
        }
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

        instruction_bytes = op_byte + param_bytes
        machine_code += instruction_bytes

    assembled_program = HEADER + machine_code
    out_file = open(out_path, 'wb')
    out_file.write(assembled_program)
    out_file.close()

    end_time = time()
    elapsed = round(end_time - start_time, 3)

    print(*assembled_program)
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
    print("Compiling", in_path, "to", out_path)
    compile_fvcal(assembly, out_path)


if __name__ == '__main__':
    get_input(argv)
