from abc import ABC

class Visitor(ABC):
    def visit_const(self, node):
        raise NotImplemented
        raise NotImplementedError("visit_const must be implemented")

    def visit_var(self, node):
        raise NotImplementedError("visit_var must be implemented")

    def visit_procedure(self, node):
        raise NotImplementedError("visit_procedure must be implemented")

    def visit_assignment(self, node):
        raise NotImplementedError("visit_assignment must be implemented")

    def visit_call(self, node):
        raise NotImplementedError("visit_call must be implemented")

    def visit_block(self, node):
        raise NotImplementedError("visit_block must be implemented")

    def visit_if(self, node):
        raise NotImplementedError("visit_if must be implemented")

    def visit_loop(self, node):
        raise NotImplementedError("visit_loop must be implemented")

    def visit_output(self, node):
        raise NotImplementedError("visit_output must be implemented")

    def visit_debug(self, node):
        raise NotImplementedError("visit_debug must be implemented")

    def visit_odd(self, node):
        raise NotImplementedError("visit_odd must be implemented")

    def visit_binary(self, node):
        raise NotImplementedError("visit_binary must be implemented")

    def visit_unary(self, node):
        raise NotImplementedError("visit_unary must be implemented")

    def visit_identifier(self, node):
        raise NotImplementedError("visit_identifier must be implemented")

    def visit_number(self, node):
        raise NotImplementedError("visit_number must be implemented")

    def visit_grouping(self, node):
        raise NotImplementedError("visit_grouping must be implemented")

    def visit(self, node):
        node_type = node['type'].lower()
        getattr(self, f"visit_{node_type}")(node)

    @classmethod
    def generate_code(cls, ast):
        raise NotImplementedError("generate_code must be implemented")
