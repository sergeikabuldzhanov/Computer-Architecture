"""CPU functionality."""

import sys
HLT = 0b00000001


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
        self.ram = [0]*256
        self.PC = 0
        self.IR = 0
        self.MAR = 0
        self.MDR = 0
        self.FL = 0
        self.instructions = {0b10000010: self.LDI,
                             0b01000111: self.PRN,
                             0b10100010: self.MUL,
                             0b01000101: self.PUSH,
                             0b01000110: self.POP,
                             0b01010000: self.CALL,
                             0b00010001: self.RET,
                             0b10100000: self.ADD,
                             0b10101000: self.AND,
                             0b10100111: self.CMP,
                             0b01100110: self.DEC,
                             0b01100101: self.INC,
                             0b10100011: self.DIV,
                             0b10000100: self.ST,
                             0b01010100: self.JMP,
                             0b00000001: self.HLT
                             }

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

    def JMP(self, register):
        """
        Jump to the address stored in the given register.
        Set the `PC` to the address stored in the given register.
        """
        self.PC = self.reg[register]

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

    def LDI(self, register, value):
        self.reg[register] = value

    def PRN(self, register):
        print(self.reg[register])

    def ADD(self, reg_a, reg_b):
        self.reg[reg_a] = self.reg[reg_a] + self.reg[reg_b]

    def MUL(self, reg_a, reg_b):
        self.reg[reg_a] = self.reg[reg_a] * self.reg[reg_b]

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

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.PC,
            # self.fl,
            # self.ie,
            self.ram_read(self.PC),
            self.ram_read(self.PC + 1),
            self.ram_read(self.PC + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        # * `AA` Number of operands for this opcode, 0-2
        # * `B` 1 if this is an ALU operation
        # * `C` 1 if this instruction sets the PC
        # * `DDDD` Instruction identifier
        self.PC = 0
        keep_going = True
        while self.PC < len(self.ram):
            # Look at the contents of current cell in ram, pointed at by program counter (PC)
            # assume it is an instruction
            # set IR to the instruction
            self.IR = self.ram[self.PC]
            # print(f"{self.IR:08b}")
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
