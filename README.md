FFVC (For-Fun Virtual Computer)
-
Virtual computer made for learning purposes.<br>
Current features:<br>
* Processor
  * Special registers such as instruction pointer
  * 8 general-purpose registers
  * 15 instructions
* Memory
  * Fully contiguous bytes
* Bus
* Display
  * Font support
  * Currently uses pygame
  * Palette and mode registers are memory-mapped
* Assembler
  * Supports line numbers/GOTO, which expands to machine instructions
  * PRINT instruction which expands to machine instructions
* Example programs
* Some documentation

How to use
-
Run computer_interface.py. This currently serves as a very basic
"operating system" for the computer.

To-do list
-
* Input/processor interrupts
* Audio
* More peripherals
* Processor clock cycle
* Support access of non-mapped registers

What is NOT simulated
-
* Hardware circuitry
  * CPU voltages
  * Display scanlines
  * etc.