"""
The PL/0 Virtual Machine
=========================

The VM consists of two data stores and three registers.

Stores
------

code - A read only segment which contains the instructions to be
    executed by the machine.

data - A read write segment which is organized as a stack.


Registers
---------

topstack - Pointer to the top element of data in the data store.

program - Pointer to the next instruction to be fetched for
    interpretation from the code store.

base - The address to the base of the most recently allocated data
    segment (stack frame).


Data Segments (A.K.A. Stack Frames)
-----------------------------------

Every procedure, when invoked, contains at minimum the following info
in its stack frame:

Static Link - The index to the lexical scope stack frame in the data
    store. Used to resolve variable lookup.

Dynamic Link - The index to the base of the stack frame of this
    procedures caller.

Return Address - The index to the code store of what instruction to
    use next (calling index + 1).


Instruction
-----------

An instruction is a sequence of three items:

OP Code - The operation to be executed

Level - The lexical scope offset relative to calling code (only used
    by LOD, STO, CAL).

Value - Has a different meaning based on the instruction. May be an
    address (index) into the data store (LOD, STO), an address into
    the code store (CAL, JMP, JPC), a numeric literal (LIT). It can
    also be an operation like addition, subtraction, etc., to perform
    (in the case of OPR) or it may be number of times to increment
    the stack pointer (INT) for allocating space on the stack.


Here is a quick snapshot of what the state of the VM could look like
for the following pseudo code:

```
declare x

fun foo:
    declare y
    y = 20
    x = y + x  <-- execution point

x = 10
foo()
```

Registers:

 program: 8  <-- points to the next instruction to fetch (STO, 1, 3)
 base: 4     <-- points to the base of the current stack frame (foo)
 topstack: 9 <-- points to the top of the data store stack

Code Store:                               Data Store:

 0: JMP, 0, 10                            foo frame
 1: JMP, 0, 2                             +-------+
 2: INT, 0, 4                             | 9: 10 | <-- `x` loaded onto stack for add operation
 3: LIT, 0, 20                            | 8: 20 | <-- `y` loaded onto stack for add operation
 4: STO, 0, 3                             | 7: 20 | <-- Storage for `y` variable
 5: LOD, 0, 3                             | 6: 14 | <-- Return Address (index into the code store)
 6: LOD, 1, 3                             | 5: 0  | <-- Dynamic Link
 7: OPR, 0, 2  <-- execution point        | 4: 0  | <-- Static Link
 8: STO, 1, 3                             +-------+
 9: OPR, 0, 0
10: INT, 0, 4                             global frame
11: LIT, 0, 10                            +-------+
12: STO, 0, 3                             | 3: 10 | <-- Storage for `x` variable
13: CAL, 0, 2                             | 2: 0  | <-- Return Address
14: OPR, 0, 0                             | 1: 0  | <-- Dynamic Link
                                          | 0: 0  | <-- Static Link
                                          +-------+
"""
import operator

from pl0.constants import OP_CODE, OPERATION


class VM:
    OPERATION_MAP = {
        OPERATION.ADD: operator.add,
        OPERATION.SUB: operator.sub,
        OPERATION.MULT: operator.mul,
        OPERATION.DIV: operator.floordiv,
        OPERATION.EQUAL: operator.eq,
        OPERATION.NOT_EQUAL: operator.ne,
        OPERATION.LESS: operator.lt,
        OPERATION.LESS_EQUAL: operator.le,
        OPERATION.GREATER: operator.gt,
        OPERATION.GREATER_EQUAL: operator.ge,
    }

    def __init__(self, code, stack_size=500, debug=False):
        self.code = code
        self.stack_size = stack_size
        self.program = 0
        self.base = 0
        self.topstack = -1
        self.datastore = [0] * self.stack_size
        self.debug = debug

    def interpret(self):
        # initialize the registers and the global stack frame
        self.topstack = -1
        self.base = 0
        self.program = 0
        self.datastore[0] = 0
        self.datastore[1] = 0
        self.datastore[2] = 0

        while True:
            op_code, level, value = self.code[self.program]
            self.program += 1

            if self.debug:
                self.print_debug()

            if op_code == OP_CODE.LIT:
                self.push(value)
            elif op_code == OP_CODE.OPR:
                self.perform_operation(value)
            elif op_code == OP_CODE.LOD:
                base = self.find_base(level)
                loaded_value = self.datastore[base + value]
                self.push(loaded_value)
            elif op_code == OP_CODE.STO:
                base = self.find_base(level)
                self.datastore[base + value] = self.pop()
            elif op_code == OP_CODE.CAL:
                # generate a new stack frame
                # store the static link for variable lookups (lexical scope)
                self.datastore[self.topstack + 1] = self.find_base(level)
                # store the dynamic link for popping the stack frame when returning
                self.datastore[self.topstack + 2] = self.base
                # store the return address for setting the program register when returning
                self.datastore[self.topstack + 3] = self.program
                self.base = self.topstack + 1
                self.program = value
            elif op_code == OP_CODE.INT:
                self.topstack += value
            elif op_code == OP_CODE.JMP:
                self.program = value
            elif op_code == OP_CODE.JPC:
                # really this is better named branch not equal
                if self.datastore[self.topstack] == 0:
                    self.program = value
                self.topstack -= 1

            if self.program == 0:
                break

    def perform_operation(self, operation):
        if operation == OPERATION.RETURN:
            # set the stack pointer to the top of the previous stack frame (pop the stack)
            self.topstack = self.base - 1
            # set the next instruction to the return address
            self.program = self.datastore[self.topstack + 3]
            # set the base to the bottom of the previous stack frame
            self.base = self.datastore[self.topstack + 2]
        elif operation in self.OPERATION_MAP:
            rhs = self.pop()
            lhs = self.pop()
            self.push(self.OPERATION_MAP[operation](lhs, rhs))
        elif operation == OPERATION.NEGATE:
            self.datastore[self.topstack] = -self.datastore[self.topstack]
        elif operation == OPERATION.ODD:
            self.push(self.pop() % 2)  # 0 is False 1 is True
        elif operation == OPERATION.WRITE:
            print(self.datastore[self.topstack])
        elif operation == OPERATION.DEBUG:
            self.debug = True

    def find_base(self, level):
        """
        Find the base of a stack frame `level` levels down.
        """
        base = self.base
        while level > 0:
            base = self.datastore[base]
            level -= 1
        return base

    def pop(self):
        """
        Pop value off the top of the stack and decrement the
        `topstack`.
        """
        value = self.datastore[self.topstack]
        self.topstack -= 1
        return value

    def push(self, value):
        """
        Increment the `topstack` and push a value onto the
        top of the stack.
        """
        self.topstack += 1
        self.datastore[self.topstack] = value

    def print_debug(self):
        """
        Debugging output about the state of execution for when the
        debugging flag is set.
        """
        code = ""
        for i, c in enumerate(self.code):
            if i == self.program - 1:
                code += f"{i}: {c[0]}, {c[1]}, {c[2]} <--\n"
            else:
                code += f"{i}: {c[0]}, {c[1]}, {c[2]}\n"

        output = f"""\
Registers:
    program: {self.program - 1}
    base: {self.base}
    topstack: {self.topstack}

{code}
{self.datastore[:self.topstack + 1]}
        """
        print(output)
        if input("> ").lower() == "q":
            self.debug = False
