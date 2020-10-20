from pl0.generators.codegen import Generator
from pl0.generators.py3 import PythonTranspiler
from pl0.parser import Parser, ParserException
from pl0.vm import VM


def run(code):
    ast = Parser.parse(code)
    instructions = Generator.generate_code(ast)
    VM(instructions).interpret()

def transpile(code, target):
    if target.lower() == 'python':
        ast = Parser.parse(code)
        return PythonTranspiler.generate_code(ast)
