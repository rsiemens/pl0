from pl0.codegen import Generator
from pl0.parser import Parser, ParserException
from pl0.vm import VM


def run(code):
    ast = Parser.parse(code)
    instructions = Generator.generate_code(ast)
    VM(instructions).interpret()
