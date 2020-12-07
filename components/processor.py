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
    
    REGISTERS
    -------------------------------------------------------------------
    OPC register: opcode
    IPT register: instruction pointer
'''


def process_instructions(program):
    # Length, in bytes of each opcode's parameters
    opcode_parameter_lengths = [
        0,  # no-op
        9, 9,  # add, mult
        6, 6,  # cpy, mov
        -1,  # term success
        3,  # display
        3, 6, 9,  # jmp, jmpnul, jmpeql
        -1,  # term error
        7, 7,  # cpyblk, movblk
        9, 9  # mod, div
    ]

    processor_msg(4, "loading program...")
    write_address = bus.reserved_bytes  # The first 32 bytes are reserved and should not be touched

    # Load each instruction/param into RAM
    for instruction in program:
        instruction_size = max(1, ceil(instruction.bit_length() / 8))
        instruction_bytes = instruction.to_bytes(instruction_size, 'little')
        bus.io(1, write_address, instruction_bytes)

        write_address += instruction_size

    processor_msg(4, "loaded program of size", write_address - bus.reserved_bytes)

    '''
        Our registers are memory mapped. This is unusual, so may be changed in the future
    '''
    # Initialize the CPU registers
    #   Special registers
    instruction_pointer = bus.reserved_bytes
    opcode = 0
    #   General-purpose registers, for modes and params
    reg0 = 0
    reg1 = 0
    reg2 = 0
    reg3 = 0
    reg4 = 0
    reg5 = 0
    reg6 = 0
    reg7 = 0

    # Execution of the program occurs in this loop
    # it is the core of this program and handles all the processor opcodes/logic
    # In the future, a clock and fetch-decode-execute cycle should be implemented
    processor_msg(4, "running program...")
    while opcode != 5:

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
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)   # p1 mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)   # p2 mode
            reg2 = bus.io(0, instruction_pointer + 3, 1)   # o mode

            # Direct p1 mode
            if reg0 == 0:
                # Load p1 into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # p1

            # Pointer p1 mode
            elif reg0 == 1:
                # Load ptr to p1 into register, then dereference into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)
                reg3 = bus.io(0, reg3, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct p2 mode
            if reg1 == 0:
                # Load p2 into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # p2

            # Pointer p2 mode
            elif reg1 == 1:
                # Load ptr to p2 into register, then deref into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)
                reg4 = bus.io(0, reg4, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct output
            if reg2 == 0:
                # Load out addr into register
                reg5 = bus.io(0, instruction_pointer + 8, 2)  # out

            # Pointer output
            elif reg2 == 1:
                # Load ptr to out addr into register, then deref
                reg5 = bus.io(0, instruction_pointer + 8, 2)
                reg5 = bus.io(0, reg5, 2)

            else:
                processor_msg(10, reg2)
                quit()

            # Add reg3 and reg4, store in reg6
            reg6 = reg3 + reg4

            # Write contents of reg6 to memory at addr reg5
            bus.io(1, reg5, reg6)

        # Multiply
        elif opcode == 2:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # p1 mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # p2 mode
            reg2 = bus.io(0, instruction_pointer + 3, 1)  # o mode

            # Direct p1 mode
            if reg0 == 0:
                # Load p1 into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # p1

            # Pointer p1 mode
            elif reg0 == 1:
                # Load ptr to p1 into register, then dereference into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)
                reg3 = bus.io(0, reg3, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct p2 mode
            if reg1 == 0:
                # Load p2 into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # p2

            # Pointer p2 mode
            elif reg1 == 1:
                # Load ptr to p2 into register, then deref into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)
                reg4 = bus.io(0, reg4, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct output
            if reg2 == 0:
                # Load out addr into register
                reg5 = bus.io(0, instruction_pointer + 8, 2)  # out

            # Pointer output
            elif reg2 == 1:
                # Load ptr to out addr into register, then deref
                reg5 = bus.io(0, instruction_pointer + 8, 2)
                reg5 = bus.io(0, reg5, 2)

            else:
                processor_msg(10, reg2)
                quit()

            # Multiply reg3 and reg4, store in reg6
            reg6 = reg3 * reg4

            # Write contents of reg6 to memory at addr reg5
            bus.io(1, reg5, reg6)

        # Copy
        elif opcode == 3:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # i_mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # o_mode

            # Direct mode
            if reg0 == 0:
                # Load p1 into register
                reg2 = bus.io(0, instruction_pointer + 3, 2)  # p1

            # Pointer mode
            elif reg0 == 1:
                # Load ptr to p1 into register, and deref
                reg2 = bus.io(0, instruction_pointer + 3, 2)  # a_p1
                reg2 = bus.io(0, reg2, 2)                       # p1

            else:
                processor_msg(9, reg0)
                quit()

            # Direct output mode
            if reg1 == 0:
                # Load out addr into register
                reg3 = bus.io(0, instruction_pointer + 5, 2)  # out
                #bus.io(1, reg3, reg2)

            # Pointer output mode
            elif reg1 == 1:
                # Load ptr to out addr into register, then deref
                reg3 = bus.io(0, instruction_pointer + 5, 2)  # a_out
                reg3 = bus.io(0, reg3, 2)                      # out
                #bus.io(1, reg3, reg2)

            else:
                processor_msg(10, reg1)
                quit()

            # Write the contents of reg2 into addr in reg3
            bus.io(1, reg3, reg2)

        # Move
        elif opcode == 4:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # i_mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # o_mode

            # Move does not have a direct mode, since there is nowhere to move a literal from!
            # Pointer mode
            if reg0 == 0:
                # Load ptr to p1 into register, and deref into reg3, since we need to know the address to delete
                reg2 = bus.io(0, instruction_pointer + 3, 2)  # a_p1
                reg3 = bus.io(0, reg2, 2)                     # p1

                #bus.io(1, reg2, 0)

            # Double pointer mode
            elif reg0 == 1:
                # Load ptr to ptr to p1 into register, deref twice
                reg2 = bus.io(0, instruction_pointer + 3, 2)  # aa_p1
                reg2 = bus.io(0, reg2, 2)                     # a_p1
                reg3 = bus.io(0, reg2, 2)                        # p1

                #bus.io(1, reg2, 0)

            else:
                processor_msg(9, reg0)
                quit()

            # Direct output mode
            if reg1 == 0:
                # Load out addr into register
                reg4 = bus.io(0, instruction_pointer + 5, 2)  # out
                #bus.io(1, reg4, reg3)

            # Pointer output mode
            elif reg1 == 1:
                # Load ptr to out addr into register and deref
                reg4 = bus.io(0, instruction_pointer + 5, 2)  # a_out
                reg4 = bus.io(0, reg4, 2)
                #bus.io(1, reg4, reg3)

            else:
                processor_msg(10, reg1)
                quit()

            # Write the contents of reg3 to the addr in reg4
            bus.io(1, reg4, reg3)

            # Clear the contents of reg2
            # This is the delete portion of the move instruction
            bus.io(1, reg2, 0)

        # Terminate execution successfully
        elif opcode == 5:
            processor_msg(0)

        # Display value
        # This instruction is magic, and is for debugging the processor
        # Eventually, it may be removed
        elif opcode == 6:
            # Load input mode into register
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # i_mode

            # Direct mode
            if reg0 == 0:
                # Load p1 into register
                reg1 = bus.io(0, instruction_pointer + 2, 2)  # p1
                #print(reg1)

            # Pointer mode
            elif reg0 == 1:
                # Load ptr to p1 into register, then deref
                reg1 = bus.io(0, instruction_pointer + 2, 2)  # a_p1
                reg1 = bus.io(0, reg1, 2)                       # p1
                #print(reg1)

            else:
                processor_msg(9, reg0)
                quit()

            # Call Python print and output to console for debugging purposes
            print(reg1)

        # Jump
        elif opcode == 7:
            # Load parameter mode into register
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # jmp_mode

            # Direct jump
            if reg0 == 0 or reg0 == 2:
                # Load jmp addr into register
                reg1 = bus.io(0, instruction_pointer + 2, 2)  # a_jmp

            # Pointer jump
            elif reg0 == 1 or reg0 == 3:
                # Load ptr to jmp addr into register, then deref
                reg1 = bus.io(0, instruction_pointer + 2, 2)  # aa_jmp
                reg1 = bus.io(0, reg1, 2)                     # a_jmp

            else:
                processor_msg(9, reg0)
                quit()

            # Normal jump
            if reg0 == 0 or reg0 == 1:
                instruction_pointer = reg1 - parameter_bytes - 1

            # Relative jump
            elif reg0 == 2 or reg0 == 3:
                instruction_pointer += reg1

        # Jump if null
        elif opcode == 8:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # jmp_mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # p1_mode

            # Direct jump
            if reg0 == 0 or reg0 == 2:
                # Load jmp addr into register
                reg2 = bus.io(0, instruction_pointer + 3, 2)  # a_jmp

            # Pointer jump
            elif reg0 == 1 or reg0 == 3:
                # Load ptr to jmp addr into register, and deref
                reg2 = bus.io(0, instruction_pointer + 3, 2)  # aa_jmp
                reg2 = bus.io(0, reg2, 2)                     # a_jmp

            else:
                processor_msg(9, reg0)
                quit()

            # Literal param
            if reg1 == 0:
                # Load p1 into register
                reg3 = bus.io(0, instruction_pointer + 5, 2)  # p1

            # Pointer param
            elif reg1 == 1:
                # Load ptr to p1 into register, and deref
                reg3 = bus.io(0, instruction_pointer + 5, 2)  # a_p1
                reg3 = bus.io(0, reg3, 2)                       # p1

            else:
                processor_msg(9, reg1)
                quit()

            # Jump if param1 is null (zero)
            if reg3 == 0:
                # Normal jump
                if reg0 == 0 or reg0 == 1:
                    instruction_pointer = reg2 - parameter_bytes - 1

                # Relative jump
                elif reg0 == 2 or reg0 == 3:
                    instruction_pointer += reg2

        # Jump if equal
        elif opcode == 9:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # jmp_mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # p1_mode
            reg2 = bus.io(0, instruction_pointer + 3, 1)  # p2_mode

            # Direct jump
            if reg0 == 0 or reg0 == 2:
                # Load jmp addr into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # a_jmp

            # Pointer jump
            elif reg0 == 1 or reg0 == 3:
                # Load ptr to jmp addr into register and deref
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # aa_jmp
                reg3 = bus.io(0, reg3, 2)                     # a_jmp

            else:
                processor_msg(9, reg0)

            # Literal param
            if reg1 == 0:
                # Load p1 into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # p1

            # Pointer param
            elif reg1 == 1:
                # Load ptr to p1 into register, and deref
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # aa_p1
                reg4 = bus.io(0, reg4, 2)                       # a_p1

            else:
                processor_msg(9, reg1)
                quit()

            # Literal param
            if reg2 == 0:
                # Load p2 into register
                reg5 = bus.io(0, instruction_pointer + 8, 2)  # p2

            # Pointer param
            elif reg2 == 1:
                # Load ptr to p2 into register, then deref
                reg5 = bus.io(0, instruction_pointer + 8, 2)  # a_p2
                reg5 = bus.io(0, reg5, 2)                       # p2

            else:
                processor_msg(9, reg1)
                quit()

            # Jump if given params are equal
            if reg4 == reg5:
                # Normal jump
                if reg0 == 0 or reg0 == 1:
                    instruction_pointer = reg3 - parameter_bytes - 1

                elif reg0 == 2 or reg0 == 3:
                    instruction_pointer += reg3

        # Terminate with error
        elif opcode == 10:
            processor_msg(11)
            opcode = 5

        # Copy block
        elif opcode == 11:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # i_mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # o_mode

            # Load size parameter into register
            reg2 = bus.io(0, instruction_pointer + 3, 1)  # size

            # Direct mode
            if reg0 == 0:
                # Load ptr to p1 into register and deref
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # a_p1
                reg3 = bus.io(0, reg3, reg2)                    # p1

            # Pointer mode
            elif reg0 == 1:
                # Load ptr to ptr to p1 into register and deref twice
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # aa_p1
                reg3 = bus.io(0, reg3, 2)                     # a_p1
                reg3 = bus.io(0, reg3, reg2)                  # p1

            else:
                processor_msg(9, reg0)
                quit()

            # Direct output mode
            if reg1 == 0:
                # Load out addr into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # out

            # Pointer output mode
            elif reg1 == 1:
                # Load ptr to out addr into register and deref
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # a_out
                reg4 = bus.io(0, reg4, 2)                     # out

            else:
                processor_msg(10, reg1)
                quit()

            # Write contents of reg3 into addr in reg4
            # This is slightly cheating since reg3 currently contains a block of memory, not a value
            # TODO: de-magic the CPYBLK instruction
            bus.io(1, reg4, reg3)

        # Move block
        elif opcode == 12:
            print("MOVEBLK UNIMPLEMENTED")
            pass

        # Modulo
        elif opcode == 13:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # p1 mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # p2 mode
            reg2 = bus.io(0, instruction_pointer + 3, 1)  # o mode

            # Direct p1 mode
            if reg0 == 0:
                # Load p1 into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # p1

            # Pointer p1 mode
            elif reg0 == 1:
                # Load ptr to p1 into register, then dereference into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)
                reg3 = bus.io(0, reg3, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct p2 mode
            if reg1 == 0:
                # Load p2 into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # p2

            # Pointer p2 mode
            elif reg1 == 1:
                # Load ptr to p2 into register, then deref into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)
                reg4 = bus.io(0, reg4, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct output
            if reg2 == 0:
                # Load out addr into register
                reg5 = bus.io(0, instruction_pointer + 8, 2)  # out

            # Pointer output
            elif reg2 == 1:
                # Load ptr to out addr into register, then deref
                reg5 = bus.io(0, instruction_pointer + 8, 2)
                reg5 = bus.io(0, reg5, 2)

            else:
                processor_msg(10, reg2)
                quit()

            # Modulo reg3 and reg4, store in reg6
            reg6 = reg3 % reg4

            # Write contents of reg6 to memory at addr reg5
            bus.io(1, reg5, reg6)

        # Division
        elif opcode == 14:
            # Load parameter modes into registers
            reg0 = bus.io(0, instruction_pointer + 1, 1)  # p1 mode
            reg1 = bus.io(0, instruction_pointer + 2, 1)  # p2 mode
            reg2 = bus.io(0, instruction_pointer + 3, 1)  # o mode

            # Direct p1 mode
            if reg0 == 0:
                # Load p1 into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)  # p1

            # Pointer p1 mode
            elif reg0 == 1:
                # Load ptr to p1 into register, then dereference into register
                reg3 = bus.io(0, instruction_pointer + 4, 2)
                reg3 = bus.io(0, reg3, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct p2 mode
            if reg1 == 0:
                # Load p2 into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)  # p2

            # Pointer p2 mode
            elif reg1 == 1:
                # Load ptr to p2 into register, then deref into register
                reg4 = bus.io(0, instruction_pointer + 6, 2)
                reg4 = bus.io(0, reg4, 2)

            else:
                processor_msg(9, reg2)
                quit()

            # Direct output
            if reg2 == 0:
                # Load out addr into register
                reg5 = bus.io(0, instruction_pointer + 8, 2)  # out

            # Pointer output
            elif reg2 == 1:
                # Load ptr to out addr into register, then deref
                reg5 = bus.io(0, instruction_pointer + 8, 2)
                reg5 = bus.io(0, reg5, 2)

            else:
                processor_msg(10, reg2)
                quit()

            # Divide reg3 and reg4, store in reg6
            reg6 = reg3 // reg4

            # Write contents of reg6 to memory at addr reg5
            bus.io(1, reg5, reg6)

        else:
            processor_msg(3, opcode, "at", instruction_pointer, "[EXHAUSTED]")
            quit()

        instruction_pointer += 1 + parameter_bytes
