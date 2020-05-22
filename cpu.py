"""CPU functionality."""

import sys

HLT = 0b00000001
PRN = 0b01000111
LDI = 0b10000010
MUL = 0b10100010
ADD = 0b10100000
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
IRET = 0b00010011
RET = 0b00010001
CMP = 0b10100111
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0
        self.fl = 0b00000000
        self.sp = 0xF4

    def load(self):
        """Load a program into memory."""

        address = 0

        with open(sys.argv[1]) as program:
            for instruction in program:
                val = instruction.split("#")[0].strip()
                if val == "":
                    continue
                v = int(val, 2)
                self.ram[address] = v
                address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == ADD:
            self.reg[reg_a] += self.reg[reg_b]
        elif op == MUL:
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == CMP:
            # Compare the values in two registers.
            # - If they are equal, set the Equal `E` flag to 1, otherwise set it to 0.
            if self.reg[reg_a] == self.reg[reg_b]:
                self.fl = 0b00000001
            # - If registerA is less than registerB, set the Less-than `L` flag to 1,
            #   otherwise set it to 0.
            elif self.reg[reg_a] < self.reg[reg_b]:
                self.fl = 0b00000100
            # - If registerA is greater than registerB, set the Greater-than `G` flag
            #   to 1, otherwise set it to 0.
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.fl = 0b00000010

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""

        # It needs to read the memory address that's stored in register `PC`, and store
        # that result in `IR`, the _Instruction Register_. This can just be a local
        # variable in `run()`.
        running = True
        while running:
            IR = self.ram_read(self.pc)
            # read the bytes at `PC+1` and `PC+2` from RAM into variables `operand_a` and
            operand_a = self.ram_read(self.pc + 1)
            # `operand_b` in case the instruction needs them.
            operand_b = self.ram_read(self.pc + 2)

            if IR == HLT:
                running = False

            elif IR == JEQ:
                """
                `JEQ register`

                If `equal` flag is set (true), jump to the address stored in the given register.

                Machine code:

                ```
                01010101 00000rrr
                55 0r
                ```

                """
                if self.fl == 0b00000001:
                    self.pc = self.reg[operand_a]
                else:
                    self.pc += 2

            elif IR == JNE:
                """

                `JNE register`

                If `E` flag is clear (false, 0), jump to the address stored in the given
                register.

                Machine code:

                ```
                01010110 00000rrr
                56 0r
                ```
                """
                if self.fl != 0b00000001:
                    self.pc = self.reg[operand_a]
                else:
                    self.pc += 2

            elif IR == JMP:
                """

                ### JMP

                `JMP register`

                Jump to the address stored in the given register.

                Set the `PC` to the address stored in the given register.

                Machine code:

                ```
                01010100 00000rrr
                54 0r
                ```
                """

                self.pc = self.reg[operand_a]

            elif IR == CMP:
                """
                ### CMP

                _This is an instruction handled by the ALU._
                ```
                10100111 00000aaa 00000bbb
                A7 0a 0b
                ```
                """
                self.alu(CMP, operand_a, operand_b)
                self.pc += 3

            elif IR == CALL:
                """`CALL register`

                # Calls a subroutine (function) at the address stored in the register.
                # Machine code:
                # ```
                # 01010000 00000rrr
                # 50 0r
                # ```
                # 1. The address of the **_instruction_** _directly after_ `CALL` is
                #    pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing."""

                # 2. The PC is set to the address stored in the given register. We jump to that location in RAM and execute the first instruction in the subroutine. The PC can move forward or backwards from its current location.
                self.sp -= 1
                self.ram[self.sp] = self.pc + 2
                self.pc = self.reg[operand_a]

            elif IR == RET:
                """
                `RET`

                Return from subroutine.

                Pop the value from the top of the stack and store it in the `PC`.

                Machine Code:

                ```
                00010001
                11
                ```

                """
                popped = self.ram[self.sp]

                self.pc = popped

                self.sp += 1

            elif IR == PUSH:
                # 1. decrement the SP
                self.sp -= 1
                # 2. copy the value from the given register into memory at address SP

                self.ram[self.sp] = self.reg[operand_a]

                self.pc += 2

            elif IR == POP:
                """
                `POP register`

                Pop the value at the top of the stack into the given register.

                1. Copy the value from the address pointed to by `SP` to the given register.
                2. Increment `SP`.

                Machine code:

                ```
                01000110 00000rrr"""
                popped = self.ram[self.sp]

                self.reg[operand_a] = popped

                self.sp += 1

                self.pc += 2

            elif IR == LDI:
                """`LDI register immediate`

                Set the value of a register to an integer.

                Machine code:

                ```
                10000010 00000rrr iiiiiiii
                82 0r ii
    ```"""
                self.reg[operand_a] = operand_b

                self.pc += 3

            elif IR == MUL:
                """ This is an instruction handled by the ALU._

                 `MUL registerA registerB`

                 Multiply the values in two registers together and store the result in registerA.

                 Machine code:

                 ```
                 10100010 00000aaa 00000bbb
                 A2 0a 0b
                 ```
                """

                self.alu(MUL, operand_a, operand_b)
                self.pc += 3

            elif IR == ADD:
                self.alu(ADD, operand_a, operand_b)
                self.pc += 3

            elif IR == PRN:
                """
                PRN register pseudo-instruction

                Print numeric value stored in the given register.

                Print to the console the decimal integer value that is stored in the given
                register.

                Machine code:54

                01000111 00000rrr
                47 0r
                """

                print(self.reg[operand_a])
                self.pc += 2

    def ram_read(self, MAR):
        """ should accept the address to read and return the value stored there. """
        # The MAR contains the address that is being read or written to
        return self.ram[MAR]

    def ram_write(self, MAR, MDR):
        """  should accept a value to write, and the address to write it to. """
        # The MDR contains the data that was read or the data to write.

        self.ram[MAR] = MDR
