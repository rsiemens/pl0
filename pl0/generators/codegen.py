from collections import ChainMap

from pl0.constants import OP_CODE, OPERATION
from pl0.generators.visitor import Visitor


class Generator(Visitor):
    def __init__(self):
        self.scope = ChainMap()
        self.code = []

    def visit_const(self, node):
        self.scope[node["name"]] = {"type": node["type"], "value": node["value"]}

    def visit_var(self, node):
        # 0 based. First 3 are for some stack frame book keeping (SL, DL, RA)
        addr_offset = self.declaration_count() + 3
        self.scope[node["name"]] = {
            "type": node["type"],
            "level": len(self.scope.maps) - 1,
            "offset": addr_offset,
        }

    def visit_procedure(self, node):
        proc_declaration = {"type": node["type"], "level": len(self.scope.maps) - 1}
        self.scope[node["name"]] = proc_declaration

        # create a new scope for the procedure declarations to live in
        self.push_scope()
        jmp_idx = self.generate(OP_CODE.JMP, 0, 0)

        for i, parameter in enumerate(node["parameters"], start=1):
            self.scope[parameter["name"]] = {
                "type": parameter["type"],
                "level": len(self.scope.maps) - 1,
                "offset": -i,  # parameters are found just below the base pointer.
            }                  # the caller will take care of removing them when the
                               # procedure returns

        for block in node["blocks"]:
            if self.should_fixup(block):
                self.fixup(jmp_idx)
                proc_declaration["address"] = self.code[jmp_idx][2]
            self.visit(block)

        self.generate(OP_CODE.OPR, 0, OPERATION.RETURN)
        self.pop_scope()

    def visit_assignment(self, node):
        level = len(self.scope.maps) - 1
        var = self.scope[node["name"]]
        self.visit(node["value"])
        self.generate(OP_CODE.STO, level - var["level"], var["offset"])

    def visit_call(self, node):
        # This will push the parameters onto the stack in reverse order.
        # then they can be accessed by base_pointer - 1 for first arg, etc.
        for argument in node["arguments"][::-1]:
            self.visit(argument)

        level = len(self.scope.maps) - 1
        procedure = self.scope[node["name"]]
        self.generate(OP_CODE.CAL, level - procedure["level"], procedure["address"])

        # "Pop off" any parameters by decrementing the stack pointer
        for argument in node["arguments"]:
            self.generate(OP_CODE.DET, 0, 0)

    def visit_block(self, node):
        for statement in node["statements"]:
            self.visit(statement)

    def visit_if(self, node):
        self.visit(node["condition"])
        jpc_idx = self.generate(OP_CODE.JPC, 0, 0)
        self.visit(node["body"])
        # fixup
        self.code[jpc_idx][2] = len(self.code)

    def visit_loop(self, node):
        cond_idx = len(self.code)
        self.visit(node["condition"])
        jpc_idx = self.generate(OP_CODE.JPC, 0, 0)
        self.visit(node["body"])
        self.generate(OP_CODE.JMP, 0, cond_idx)
        # fixup
        self.code[jpc_idx][2] = len(self.code)

    def visit_output(self, node):
        self.visit(node["value"])
        self.generate(OP_CODE.OPR, 0, OPERATION.WRITE)

    def visit_debug(self, node):
        self.generate(OP_CODE.OPR, 0, OPERATION.DEBUG)

    def visit_odd(self, node):
        self.visit(node["expression"])
        self.generate(OP_CODE.OPR, 0, OPERATION.ODD)

    def visit_binary(self, node):
        operator = node["operator"]
        self.visit(node["left"])
        self.visit(node["right"])

        if operator == "PLUS":
            self.generate(OP_CODE.OPR, 0, OPERATION.ADD)
        elif operator == "MINUS":
            self.generate(OP_CODE.OPR, 0, OPERATION.SUB)
        elif operator == "TIMES":
            self.generate(OP_CODE.OPR, 0, OPERATION.MULT)
        elif operator == "SLASH":
            self.generate(OP_CODE.OPR, 0, OPERATION.DIV)
        elif operator == "EQL":
            self.generate(OP_CODE.OPR, 0, OPERATION.EQUAL)
        elif operator == "NEQ":
            self.generate(OP_CODE.OPR, 0, OPERATION.NOT_EQUAL)
        elif operator == "LESS":
            self.generate(OP_CODE.OPR, 0, OPERATION.LESS)
        elif operator == "GEQ":
            self.generate(OP_CODE.OPR, 0, OPERATION.GREATER_EQUAL)
        elif operator == "GTR":
            self.generate(OP_CODE.OPR, 0, OPERATION.GREATER)
        elif operator == "LEQ":  # <=
            self.generate(OP_CODE.OPR, 0, OPERATION.LESS_EQUAL)

    def visit_unary(self, node):
        self.visit(node["right"])
        self.generate(OP_CODE.OPR, 0, OPERATION.NEGATE)

    def visit_identifier(self, node):
        level = len(self.scope.maps) - 1
        referenced = self.scope[node["name"]]
        if referenced["type"] == "Const":
            self.generate(OP_CODE.LIT, 0, referenced["value"])
        elif referenced["type"] == "Var":
            self.generate(
                OP_CODE.LOD, level - referenced["level"], referenced["offset"]
            )

    def visit_number(self, node):
        self.generate(OP_CODE.LIT, 0, node["value"])

    def visit_grouping(self, node):
        self.visit(node["expression"])

    def generate(self, instruction, level, value):
        self.code.append([instruction, level, value])
        return len(self.code) - 1

    def should_fixup(self, node):
        return node["type"] not in ["Const", "Var", "Procedure"]

    def fixup(self, jmp_idx):
        """
        Fixup a JMP instruction, and allocate space on the stack
        for static link, dynamic link, return address, and all variable
        declarations.
        """
        # 3 for SL, DL, RA
        var_declarations = self.declaration_count() + 3
        self.code[jmp_idx][2] = len(self.code)
        self.generate(OP_CODE.INT, 0, var_declarations)

    def push_scope(self):
        self.scope = self.scope.new_child()

    def pop_scope(self):
        self.scope = self.scope.parents

    def declaration_count(self):
        """
        Get the number of variable declarations in the current scope.
        """
        count = 0
        for declaration in self.scope.maps[0].values():
            if declaration["type"] == "Var":
                count += 1
        return count

    @classmethod
    def generate_code(cls, ast):
        visitor = cls()
        jmp_idx = visitor.generate(OP_CODE.JMP, 0, 0)
        for node in ast:
            if visitor.should_fixup(node):
                visitor.fixup(jmp_idx)
            visitor.visit(node)
        visitor.generate(OP_CODE.OPR, 0, OPERATION.RETURN)
        return visitor.code
