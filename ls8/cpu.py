"""CPU functionality."""

import sys

import msvcrt


def kbfunc():
    x = msvcrt.kbhit()
    if x:
        ret = ord(msvcrt.getch())
    else:
        ret = 0
    return ret


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        """
        * `PC`: Program Counter, address of the currently executing instruction
        * `IR`: Instruction Register, contains a copy of the currently executing instruction
        * `MAR`: Memory Address Register, holds the memory address we're reading or writing
        * `MDR`: Memory Data Register, holds the value to write or the value just read
        * `FL`: Flags, see below
        """
        self.reg = [0]*8
        self.reg[7] = 0xF4
        self.reg[5] = 0xFF
        self.ram = [0]*256
        self.PC = 0
        self.IR = 0
        self.MAR = 0
        self.MDR = 0
        self.FL = 0
        self.allow_interrupts = True
        self.instructions = {0b10000010: self.LDI,
                             0b01000111: self.PRN,
                             0b01000101: self.PUSH,
                             0b01000110: self.POP,
                             0b10000100: self.ST,
                             0b01001000: self.PRA,
                             0b10000011: self.LD,
                             0b00000001: self.HLT,
                             0b00000000: self.NOP,
                             # PC mutators
                             0b01010000: self.CALL,
                             0b00010001: self.RET,
                             0b01010010: self.INT,
                             0b00010011: self.IRET,
                             0b01010101: self.JEQ,
                             0b01010110: self.JNE,
                             0b01010111: self.JGT,
                             0b01011000: self.JLT,
                             0b01011001: self.JLE,
                             0b01011010: self.JGE,
                             0b01010100: self.JMP,
                             # ALU ops
                             0b10100000: self.ADD,
                             0b10100001: self.SUB,
                             0b10100010: self.MUL,
                             0b10100011: self.DIV,
                             0b10100100: self.MOD,
                             0b01100101: self.INC,
                             0b01100110: self.DEC,
                             0b10100111: self.CMP,
                             0b10101000: self.AND,
                             0b01101001: self.NOT,
                             0b10101010: self.OR,
                             0b10101011: self.XOR,
                             0b10101100: self.SHL,
                             0b10101101: self.SHR,
                             }

    def JMP(self, register):
        """
        Jump to the address stored in the given register.
        Set the `PC` to the address stored in the given register.
        """
        self.PC = self.reg[register]

    def JGE(self, register):
        if self.FL & 0b011:
            self.PC = self.reg[register]
        else:
            self.PC+=2

    def JLE(self, register):
        if self.FL & 0b101:
            self.PC = self.reg[register]
        else:
            self.PC+=2

    def JLT(self, register):
        if self.FL & 0b100:
            self.PC = self.reg[register]
        else:
            self.PC+=2

    def JGT(self, register):
        if self.FL & 0b10:
            self.PC = self.reg[register]
        else:
            self.PC+=2

    def JNE(self, register):
        if not self.FL & 0b1:
            self.PC = self.reg[register]
        else:
            self.PC+=2

    def JEQ(self, register):
        # print(self.PC,self.reg[register], self.FL)
        if self.FL & 0b1:
            self.PC = self.reg[register]
        else:
            self.PC+=2

    def CMP(self, reg_a, reg_b):
        """`FL` bits: `00000LGE`"""
        if self.reg[reg_a] == self.reg[reg_b]:
            self.FL = 0b001
        elif self.reg[reg_a] < self.reg[reg_b]:
            self.FL = 0b100
        elif self.reg[reg_a] > self.reg[reg_b]:
            self.FL = 0b010

    def AND(self, reg_a, reg_b):
        self.reg[reg_a] = self.reg[reg_a] & self.reg[reg_b]

    def ADD(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] + self.reg[reg_b]) & 0xff

    def MUL(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] * self.reg[reg_b]) & 0xff

    def SHR(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] >> self.reg[reg_b]) & 0xff

    def SHL(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] << self.reg[reg_b]) & 0xff

    def XOR(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] ^ self.reg[reg_b]) & 0xff

    def OR(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] | self.reg[reg_b]) & 0xff

    def NOT(self, reg_a):
        self.reg[reg_a] = ~self.reg[reg_a]

    def MOD(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] % self.reg[reg_b]) & 0xff

    def SUB(self, reg_a, reg_b):
        self.reg[reg_a] = (self.reg[reg_a] - self.reg[reg_b]) & 0xff

    def INC(self, register):
        self.reg[register] = (self.reg[register]+1) & 0xff

    def DIV(self, reg_a, reg_b):
        if self.reg[reg_b] == 0:
            print("Invalid value error: Can't divide by 0")
            self.HLT()
        else:
            self.reg[reg_a] = (self.reg[reg_a]/self.reg[reg_b]) & 0xff

    def DEC(self, register):
        self.reg[register] = (self.reg[register]-1) & 0xff

    def NOP(self):
        pass

    def LD(self, reg_a, reg_b):
        """Loads registerA with the value at the memory address stored in registerB."""
        self.reg[reg_a] = self.ram[self.reg[reg_b]]

    def IRET(self):
        # 1. Registers R6-R0 are popped off the stack in that order.
        for i in range(7):
            self.reg[6-i] = self.ram[self.reg[7]]
            self.reg[7] += 1
        # 2. The `FL` register is popped off the stack.
        self.FL = self.ram[self.reg[7]]
        self.reg[7] += 1
        # 3. The return address is popped off the stack and stored in `PC`.
        self.PC = self.ram[self.reg[7]]
        self.reg[7] += 1
        # 4. Interrupts are re-enabled
        self.allow_interrupts = True

    def PRA(self, register):
        print(chr(self.reg[register]), end="")

    def INT(self, register):
        self.reg[6] |= 2**self.reg[register]

    def ST(self, reg_a, reg_b):
        """Store value in registerB in the ram address stored in registerA."""
        self.ram[self.reg[reg_a]] = self.reg[reg_b]

    def HLT(self):
        sys.exit()

    def RET(self):
        self.PC = self.ram[self.reg[7]]
        self.reg[7] += 1

    def CALL(self, register):
        """
        Calls a subroutine (function) at the address stored in the register.
        1. The address of the ***instruction*** _directly after_ `CALL` is
        pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
        2. The PC is set to the address stored in the given register.
        We jump to that location in RAM and execute the first instruction in the subroutine.
        The PC can move forward or backwards from its current location.
        """
        # move stack pointer
        self.reg[7] -= 1
        # push address of the next instruction on the stack, which is equal to PC+2, since it has a single argument
        self.ram[self.reg[7]] = self.PC+2
        # set PC to the value at given register
        self.PC = self.reg[register]

    def handle_interrupt(self, interrupt):
        self.allow_interrupts = False
        # 2. Clear the bit in the IS register.
        self.reg[6] &= 0xff - 2**(interrupt)
        # 3. The `PC` register is pushed on the stack.
        self.reg[7] -= 1
        self.ram[self.reg[7]] = self.PC
        # 4. The `FL` register is pushed on the stack.
        self.reg[7] -= 1
        self.ram[self.reg[7]] = self.FL
        for i in range(7):
            # 5. Registers R0-R6 are pushed on the stack in that order.
            self.reg[7] -= 1
            self.ram[self.reg[7]] = self.reg[i]
        # 6. The address (_vector_ in interrupt terminology) of the appropriate
        #    handler is looked up from the interrupt vector table.
        interrupt_address = self.ram[0xF8+interrupt]
        # 7. Set the PC is set to the handler address.
        self.PC = interrupt_address

    def LDI(self, register, value):
        self.reg[register] = value

    def PRN(self, register):
        print(self.reg[register])

    def PUSH(self, register):
        self.reg[7] -= 1
        self.ram[self.reg[7]] = self.reg[register]

    def POP(self, reg):
        self.reg[reg] = self.ram[self.reg[7]]
        self.reg[7] += 1

    def ram_read(self, address):
        """Accepts the adress to read and returns it's value"""
        return self.ram[address]

    def ram_write(self, value, address):
        self.ram[address] = value

    def load(self, filename):
        """Load a program into memory."""
        import re
        pattern = "#(.+|)"
        with open(filename) as file:
            # replace all comment lines with empty ""
            text = re.sub(pattern, "", file.read())
            # strip of all whitespace and split on \n
            commands = text.strip().split()
        self.MAR = 0
        # convert strings to binary digits
        program = [int(command, 2) for command in commands]

        for instruction in program:
            self.ram[self.MAR] = instruction
            self.MAR += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        # elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02d | %02d %02d %02d |" % (
            self.PC,
            # self.fl,
            # self.ie,
            self.ram_read(self.PC),
            self.ram_read(self.PC + 1),
            self.ram_read(self.PC + 2)
        ), end='')

        for i in range(8):
            print(" %02d" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        # * `AA` Number of operands for this opcode, 0-2
        # * `B` 1 if this is an ALU operation
        # * `C` 1 if this instruction sets the PC
        # * `DDDD` Instruction identifier
        import time
        clock = time.time()
        self.PC = 0
        while self.PC < len(self.ram):
            """
            Prior to instruction fetch, the following steps occur:
            1. The IM register is bitwise AND-ed with the IS register and the
            results stored as `maskedInterrupts`.
            2. Each bit of `maskedInterrupts` is checked, starting from 0 and going
            up to the 7th bit, one for each interrupt.
            3. If a bit is found to be set, follow the next sequence of steps. Stop
            further checking of `maskedInterrupts`.
            """
            # print(self.PC)
            # self.trace()
            masked_interrupts = list(
                reversed([int(char) for char in f"{self.reg[5]&self.reg[6]:08b}"]))
            # print(f"{self.FL:08b},{self.reg[1]:08b}")
            for i in range(len(masked_interrupts)):
                # If a bit is set, handle the interrupt:
                if masked_interrupts[i]:
                    self.handle_interrupt(i)
                    break
            # check if 1 second has passed
            # if time.time() - clock >= 1:
            #     # set the 0eth bit to 1
            #     self.reg[6] |= 0b1
            #     clock = time.time()
            # check if keyboard has been hit
            key_hit = kbfunc()
            if key_hit:
                self.ram[0xf4] = key_hit
                self.reg[6] |= 0b10

            # Look at the contents of current cell in ram, pointed at by program counter (PC)
            # assume it is an instruction
            # set IR to the instruction
            self.IR = self.ram[self.PC]
            # print(f"{masked_interrupts}")
            # extract the number of arguments
            num_of_operands = (self.IR & 0b11000000) >> 6
            # extract if it's ALU op
            is_alu_operation = (self.IR & 0b00100000) << 2 >> 7
            # extract if it's setting PC
            sets_pc = (self.IR & 0b00010000) << 3 >> 7
            # execute the instruction with the proper num of operands
            if num_of_operands == 2:
                # 2 operands
                operand_1 = self.ram[self.PC+1]
                operand_2 = self.ram[self.PC+2]
                self.instructions[self.IR](operand_1, operand_2)
            elif num_of_operands == 1:
                # 1 operand
                operand_1 = self.ram[self.PC+1]
                self.instructions[self.IR](operand_1)
            else:
                # 0 operands
                self.instructions[self.IR]()
            if not sets_pc:
                self.PC += num_of_operands+1
            # if it's not setting the pc directly, increment the pc
