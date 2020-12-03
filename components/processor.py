# Virtual machine for fun
# Bert Myroon
# 21 Oct., 2020
from components import bus
from math import ceil


def processor_msg(status_code, *args):
    status_messages = [
        "Terminated successfully",
        "reserved 1",
        "reserved 2",
        "Unknown opcode",
        "Status:",
        "reserved 5",
        "reserved 6",
        "reserved 7",
        "reserved 8",
        "Unknown parameter mode",
        "Unknown output mode",
        "Terminated with error"
    ]

    if status_code not in range(0, len(status_messages)):
        msg = "Unknown status code"
    else:
        msg = status_messages[status_code]

    print("Processor message:", msg, *args)


# Virtual processor documentation
'''
    OPCODE [1 byte] {PARAMETERS} [variable length]
    "mode" parameters are one byte
    "p", and "out" paramaters are two bytes
    ----------------------------------------------------------------
    0: NO-OP {}
    1: ADD {p1_mode, p2_mode, o_mode, p1, p2, a_out}
    2: MULT {p1_mode, p2_mode, o_mode, p1, p2, a_out}
    3: CPY {i_mode, o_mode, p1, a_out}
    4: MOV {i_mode, o_mode, p1, a_out}
    5: TERMINATE SUCCESSFULLY
    6: DISPLAY {o_mode, p1}
    7: JMP {a_dest_mode, a_dest}
    8: JMP if nul {a_dest_mode, p1_mode, a_dest, p1}
    9: JMP if eql {a_dest_mode, p1_mode, p2_mode, a_dest, p1, p2},
    10: TERMINATE WITH ERROR
    11: CPYBLK {i_mode, o_mode, size, p1, a_out}
    12: MOVBLK {i_mode, o_mode, size, p1, a_out}
    13: MOD {p1_mode, p2_mode, o_mode, p1, p2, a_out}
    14: DIV {p1_mode, p2_mode, o_mode, p1, p2, a_out},
    
    PARAMETER MODES
    -----------------------------------------------------------------
    0 - direct, treat parameter as literal (num, or ptr)
    1 - pointer, treat parameter as pointer to literal (ptr to num, or ptr to ptr)
    2(jmp) - direct, relative
    3(jmp) - pointer, relative
    
    ******************************************************************
    A mode 0 input is a literal, and a mode 0 output is a pointer to an address.
    A mode 1 input is a pointer to an address, and a mode 1 output is a pointer to a pointer to an address
    in=42 (mode 0), out=50 (mode 0) will store the value 42 in address 50
    in=42 (mode 1), out=50 (mode 0) will store the value at address 42 in address 50
    in=42 (mode 0), out=50 (mode 1) will store the value at address 42 in the address represented by the value in address 50
    
    
    PROGRAMMING
    ------------------------------------------------------------------
    All programs must loop, or terminate with an opcode 5 or 10.
    Not doing so is UNDEFINED BEHAVIOUR, as the instruction pointer will
    execute from unintended areas, causing either an unknown opcode error or
    strange undefined behaviour.
    
    REGISTERS (decimal)
    -------------------------------------------------------------------
    OPC register: 9
    IPT register: 10-11
'''


def process_instructions(program):

    opcode_parameter_lengths = [
        0,  # no-op
        9, 9,  # add, mult
        6, 6,  # cpy, mov
        -1,  # term success
        3,  # display
        3, 6, 9,  # jmp, jmpnul, jmpeql
        -1,  # term error
        7, 7, # cpyblk, movblk
        9, 9 # mod, div
    ]

    # Load program
    processor_msg(4, "loading program...")
    write_address = bus.reserved_bytes  # The first 32 bytes are reserved and should not be touched
    for instruction in program:
        instruction_size = max(1, ceil(instruction.bit_length() / 8))
        instruction_bytes = instruction.to_bytes(instruction_size, 'little')
        bus.io(1, write_address, instruction_bytes)

        write_address += instruction_size

    processor_msg(4, "loaded program of size", write_address-bus.reserved_bytes)

    # Set IPT register
    bus.io(1, 10, bus.reserved_bytes)

    # Set OPC register
    bus.io(1, 9, 0)
    opcode = bus.io(0, 9, 1)

    # Execution of the program occurs in this loop
    # it is the core of this program and handles all the processor opcodes/logic
    processor_msg(4, "running program...")
    while opcode != 5:

        # What's the instruction pointer currently?
        instruction_pointer = bus.io(0, 10, 2)

        # Get the opcode from program memory (one byte)
        opcode = bus.io(0, instruction_pointer, 1)

        # Make sure opcode is valid
        if opcode >= len(opcode_parameter_lengths):
            processor_msg(3, opcode, "at", instruction_pointer)
            quit()

        # How many bytes do our parameters take up?
        parameter_bytes = opcode_parameter_lengths[opcode]

        # No-op
        if opcode == 0:
            pass

        # Add
        elif opcode == 1:
            p1_mode = bus.io(0, instruction_pointer+1, 1)
            p2_mode = bus.io(0, instruction_pointer+2, 1)
            o_mode = bus.io(0, instruction_pointer+3, 1)

            # Direct p1 mode
            if p1_mode == 0:
                p1 = bus.io(0, instruction_pointer+4, 2)

            # Pointer p1 mode
            elif p1_mode == 1:
                a_p1 = bus.io(0, instruction_pointer+4, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct p2 mode
            if p2_mode == 0:
                p2 = bus.io(0, instruction_pointer + 6, 2)

            # Pointer p2 mode
            elif p2_mode == 1:
                a_p2 = bus.io(0, instruction_pointer + 6, 2)
                p2 = bus.io(0, a_p2, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct output
            if o_mode == 0:
                out = bus.io(0, instruction_pointer+8, 2)
                bus.io(1, out, p1 + p2)

            # Pointer output
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer+8, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1 + p2)

            else:
                processor_msg(10, o_mode)
                quit()

        # Multiply
        elif opcode == 2:
            p1_mode = bus.io(0, instruction_pointer + 1, 1)
            p2_mode = bus.io(0, instruction_pointer + 2, 1)
            o_mode = bus.io(0, instruction_pointer + 3, 1)

            # Direct p1 mode
            if p1_mode == 0:
                p1 = bus.io(0, instruction_pointer + 4, 2)

            # Pointer p1 mode
            elif p1_mode == 1:
                a_p1 = bus.io(0, instruction_pointer + 4, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct p2 mode
            if p2_mode == 0:
                p2 = bus.io(0, instruction_pointer + 6, 2)

            # Pointer p2 mode
            elif p2_mode == 1:
                a_p2 = bus.io(0, instruction_pointer + 6, 2)
                p2 = bus.io(0, a_p2, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct output
            if o_mode == 0:
                out = bus.io(0, instruction_pointer + 8, 2)
                bus.io(1, out, p1 * p2)

            # Pointer output
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer + 8, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1 * p2)

            else:
                processor_msg(10, o_mode)
                quit()

        # Copy
        elif opcode == 3:
            i_mode = bus.io(0, instruction_pointer+1, 1)
            o_mode = bus.io(0, instruction_pointer+2, 1)

            # Direct mode
            if i_mode == 0:
                p1 = bus.io(0, instruction_pointer+3, 2)

            # Pointer mode
            elif i_mode == 1:
                a_p1 = bus.io(0, instruction_pointer+3, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, i_mode)
                quit()

            # Direct output mode
            if o_mode == 0:
                out = bus.io(0, instruction_pointer+5, 2)
                bus.io(1, out, p1)

            # Pointer output mode
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer+5, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1)

            else:
                processor_msg(10, o_mode)
                quit()


        # Move
        elif opcode == 4:
            i_mode = bus.io(0, instruction_pointer+1, 1)
            o_mode = bus.io(0, instruction_pointer+2, 1)

            # Move does not have a direct mode, since there is nowhere to move a literal from!
            # Pointer mode
            if i_mode == 0:
                a_p1 = bus.io(0, instruction_pointer+3, 2)
                p1 = bus.io(0, a_p1, 2)

                # The delete portion of the move instruction
                bus.io(1, a_p1, 0)

            # Double pointer mode
            elif i_mode == 1:
                aa_p1 = bus.io(0, instruction_pointer+3, 2)
                a_p1 = bus.io(0, aa_p1, 2)
                p1 = bus.io(0, a_p1, 2)

                # The delete portion of the move instruction
                bus.io(1, a_p1, 0)

            else:
                processor_msg(9, i_mode)
                quit()

            # Direct output mode
            if o_mode == 0:
                out = bus.io(0, instruction_pointer+5, 2)
                bus.io(1, out, p1)

            # Pointer output mode
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer+5, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1)

            else:
                processor_msg(10, o_mode)
                quit()

        # Terminate execution successfully
        elif opcode == 5:
            processor_msg(0)

        # Display value
        elif opcode == 6:
            i_mode = bus.io(0, instruction_pointer+1, 1)

            # Direct mode
            if i_mode == 0:
                p1 = bus.io(0, instruction_pointer+2, 2)
                print(p1)

            # Pointer mode
            elif i_mode == 1:
                a_p1 = bus.io(0, instruction_pointer+2, 2)
                p1 = bus.io(0, a_p1, 2)
                print(p1)

            else:
                processor_msg(9, i_mode)
                quit()

        # Jump
        elif opcode == 7:
            jmp_mode = bus.io(0, instruction_pointer+1, 1)

            # Direct jump
            if jmp_mode == 0 or jmp_mode == 2:
                a_jmp = bus.io(0, instruction_pointer+2, 2)

            # Pointer jump
            elif jmp_mode == 1 or jmp_mode == 3:
                aa_jmp = bus.io(0, instruction_pointer+2, 2)
                a_jmp = bus.io(0, aa_jmp, 2)

            else:
                processor_msg(9, jmp_mode)
                quit()

            # Normal jump
            if jmp_mode == 0 or jmp_mode == 1:
                bus.io(1, 10, a_jmp - parameter_bytes - 1)

            # Relative jump
            elif jmp_mode == 2 or jmp_mode == 3:
                bus.io(1, 10,
                       bus.io(0, 10, 2) + a_jmp)

        # Jump if null
        elif opcode == 8:
            jmp_mode = bus.io(0, instruction_pointer+1, 1)
            p1_mode = bus.io(0, instruction_pointer+2, 1)

            # Direct jump
            if jmp_mode == 0 or jmp_mode == 2:
                a_jmp = bus.io(0, instruction_pointer+3, 2)

            # Pointer jump
            elif jmp_mode == 1 or jmp_mode == 3:
                aa_jmp = bus.io(0, instruction_pointer+3, 2)
                a_jmp = bus.io(0, aa_jmp, 2)

            else:
                processor_msg(9, jmp_mode)
                quit()

            # Literal param
            if p1_mode == 0:
                p1 = bus.io(0, instruction_pointer+5, 2)

            # Pointer param
            elif p1_mode == 1:
                a_p1 = bus.io(0, instruction_pointer+5, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, p1_mode)
                quit()

            # Jump if param1 is null (zero)
            if p1 == 0:
                # Normal jump
                if jmp_mode == 0 or jmp_mode == 1:
                    #instruction_pointer = a_jmp - parameter_bytes - 1
                    bus.io(1, 10, a_jmp - parameter_bytes - 1)

                # Relative jump
                elif jmp_mode == 2 or jmp_mode == 3:
                    #instruction_pointer += a_jmp
                    bus.io(1, 10,
                           bus.io(0, 10, 2) + a_jmp)

        # Jump if equal
        elif opcode == 9:
            jmp_mode = bus.io(0, instruction_pointer + 1, 1)
            p1_mode = bus.io(0, instruction_pointer + 2, 1)
            p2_mode = bus.io(0, instruction_pointer + 3, 1)

            # Direct jump
            if jmp_mode == 0 or jmp_mode == 2:
                a_jmp = bus.io(0, instruction_pointer+4, 2)

            # Pointer jump
            elif jmp_mode == 1 or jmp_mode == 3:
                aa_jmp = bus.io(0, instruction_pointer+4, 2)
                a_jmp = bus.io(0, aa_jmp, 2)

            else:
                processor_msg(9, jmp_mode)

            # Literal param
            if p1_mode == 0:
                p1 = bus.io(0, instruction_pointer+6, 2)

            # Pointer param
            elif p1_mode == 1:
                a_p1 = bus.io(0, instruction_pointer+6, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, p1_mode)
                quit()

            # Literal param
            if p2_mode == 0:
                p2 = bus.io(0, instruction_pointer + 8, 2)

            # Pointer param
            elif p2_mode == 1:
                a_p2 = bus.io(0, instruction_pointer+8, 2)
                p2 = bus.io(0, a_p2, 2)

            else:
                processor_msg(9, p1_mode)
                quit()

            # Jump if given params are equal
            if p1 == p2:
                # Normal jump
                if jmp_mode == 0 or jmp_mode == 1:
                    #instruction_pointer = a_jmp - parameter_bytes - 1
                    bus.io(1, 10, a_jmp - parameter_bytes - 1)

                elif jmp_mode == 2 or jmp_mode == 3:
                    #instruction_pointer += a_jmp
                    bus.io(1, 10,
                           bus.io(0, 10, 2) + a_jmp)

        # Terminate with error
        elif opcode == 10:
            processor_msg(11)
            opcode = 5

        # Copy block
        elif opcode == 11:
            i_mode = bus.io(0, instruction_pointer + 1, 1)
            o_mode = bus.io(0, instruction_pointer + 2, 1)
            size = bus.io(0, instruction_pointer + 3, 1)

            # Direct mode
            if i_mode == 0:
                a_p1 = bus.io(0, instruction_pointer + 4, 2)
                p1 = bus.io(0, a_p1, size)

            # Pointer mode
            elif i_mode == 1:
                aa_p1 = bus.io(0, instruction_pointer + 4, 2)
                a_p1 = bus.io(0, aa_p1, 2)
                p1 = bus.io(0, a_p1, size)

            else:
                processor_msg(9, i_mode)
                quit()

            # Direct output mode
            if o_mode == 0:
                out = bus.io(0, instruction_pointer + 6, 2)
                bus.io(1, out, p1)

            # Pointer output mode
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer + 6, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1)

            else:
                processor_msg(10, o_mode)
                quit()

        # Move block
        elif opcode == 12:
            print("MOVEBLK UNIMPLEMENTED")
            pass

        # Modulo
        elif opcode == 13:
            p1_mode = bus.io(0, instruction_pointer + 1, 1)
            p2_mode = bus.io(0, instruction_pointer + 2, 1)
            o_mode = bus.io(0, instruction_pointer + 3, 1)

            # Direct p1 mode
            if p1_mode == 0:
                p1 = bus.io(0, instruction_pointer + 4, 2)

            # Pointer p1 mode
            elif p1_mode == 1:
                a_p1 = bus.io(0, instruction_pointer + 4, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct p2 mode
            if p2_mode == 0:
                p2 = bus.io(0, instruction_pointer + 6, 2)

            # Pointer p2 mode
            elif p2_mode == 1:
                a_p2 = bus.io(0, instruction_pointer + 6, 2)
                p2 = bus.io(0, a_p2, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct output
            if o_mode == 0:
                out = bus.io(0, instruction_pointer + 8, 2)
                bus.io(1, out, p1 % p2)

            # Pointer output
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer + 8, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1 % p2)

            else:
                processor_msg(10, o_mode)
                quit()

        # Division
        elif opcode == 14:
            p1_mode = bus.io(0, instruction_pointer + 1, 1)
            p2_mode = bus.io(0, instruction_pointer + 2, 1)
            o_mode = bus.io(0, instruction_pointer + 3, 1)

            # Direct p1 mode
            if p1_mode == 0:
                p1 = bus.io(0, instruction_pointer + 4, 2)

            # Pointer p1 mode
            elif p1_mode == 1:
                a_p1 = bus.io(0, instruction_pointer + 4, 2)
                p1 = bus.io(0, a_p1, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct p2 mode
            if p2_mode == 0:
                p2 = bus.io(0, instruction_pointer + 6, 2)

            # Pointer p2 mode
            elif p2_mode == 1:
                a_p2 = bus.io(0, instruction_pointer + 6, 2)
                p2 = bus.io(0, a_p2, 2)

            else:
                processor_msg(9, o_mode)
                quit()

            # Direct output
            if o_mode == 0:
                out = bus.io(0, instruction_pointer + 8, 2)
                bus.io(1, out, p1 // p2)

            # Pointer output
            elif o_mode == 1:
                a_out = bus.io(0, instruction_pointer + 8, 2)
                out = bus.io(0, a_out, 2)
                bus.io(1, out, p1 // p2)

            else:
                processor_msg(10, o_mode)
                quit()

        else:
            processor_msg(3, opcode, "at", instruction_pointer, "[EXHAUSTED]")
            quit()

        #instruction_pointer += 1 + parameter_bytes
        bus.io(1, 10,
               bus.io(0, 10, 2) + 1 + parameter_bytes)
