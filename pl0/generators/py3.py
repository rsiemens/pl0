from pl0.generators.visitor import Visitor

from io import StringIO


class PythonTranspiler(Visitor):
    INDENT = "    "

    def __init__(self):
        self._output = StringIO()
        self.scope = [{"name": "global", "vars": []}]
        self.depth = 0

    def visit_const(self, node):
        self.indent()
        self.output(f"{node['name']} = {node['value']}\n")

    def visit_var(self, node):
        self.indent()
        self.output(f"{node['name']} = None\n")
        self.scope[-1]["vars"].append(node["name"])

    def visit_procedure(self, node):
        self.indent()
        self.output(f"\ndef {node['name']}():\n")

        self.scope.append({"name": node["name"], "vars": []})
        self.depth += 1
        for block in node["blocks"]:
            self.visit(block)
        self.depth -= 1
        self.scope.pop()
        self.output("\n")

    def visit_assignment(self, node):
        if node["name"] not in self.scope[-1]["vars"]:
            self.indent()
            self.output(f"global {node['name']}\n")
            self.scope[-1]["vars"].append(node["name"])

        self.indent()
        self.output(f"{node['name']} = ")

        self.visit(node["value"])
        self.output("\n")

    def visit_call(self, node):
        self.indent()
        self.output(f"{node['name']}()\n")

    def visit_block(self, node):
        for statement in node["statements"]:
            self.visit(statement)

    def visit_if(self, node):
        self.indent()
        self.output("if ")
        self.visit(node["condition"])
        self.output(":\n")

        self.depth += 1
        self.visit(node["body"])
        self.depth -= 1

    def visit_loop(self, node):
        self.indent()
        self.output("while ")
        self.visit(node["condition"])
        self.output(":\n")

        self.depth += 1
        self.visit(node["body"])
        self.depth -= 1

    def visit_output(self, node):
        self.indent()
        self.output("print(")
        self.visit(node["value"])
        self.output(")\n")

    def visit_debug(self, node):
        self.indent()
        self.output("breakpoint()\n")

    def visit_odd(self, node):
        self.visit(node["expression"])
        self.output(f" % 2 == 1")

    def visit_binary(self, node):
        operator = node["operator"]
        self.visit(node["left"])

        if operator == "PLUS":
            self.output(" + ")
        elif operator == "MINUS":
            self.output(" - ")
        elif operator == "TIMES":
            self.output(" * ")
        elif operator == "SLASH":
            self.output(" // ")
        elif operator == "EQL":
            self.output(" == ")
        elif operator == "NEQ":
            self.output(" != ")
        elif operator == "LESS":
            self.output(" < ")
        elif operator == "GEQ":
            self.output(" >= ")
        elif operator == "GTR":
            self.output(" > ")
        elif operator == "LEQ":
            self.output(" >= ")

        self.visit(node["right"])

    def visit_unary(self, node):
        self.output("-")
        self.visit(node["right"])

    def visit_identifier(self, node):
        self.output(node["name"])

    def visit_number(self, node):
        self.output(node["value"])

    def visit_grouping(self, node):
        self.output("(")
        self.visit(node["expression"])
        self.output(")")

    def output(self, code):
        self._output.write(f"{code}")

    def indent(self):
        self._output.write(f"{self.INDENT * self.depth}")

    @classmethod
    def generate_code(cls, ast):
        visitor = cls()
        for node in ast:
            visitor.visit(node)
        return visitor._output.getvalue()
