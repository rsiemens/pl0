import argparse

from pl0 import VM, Generator, Parser, ParserException


class Command:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.add_arguments(self.parser)
        self.handle(self.parser.parse_args())

    def add_arguments(self, parser):
        parser.add_argument("src", type=str, help="Source file")
        parser.add_argument(
            "--parse",
            action="store_true",
            default=False,
            help="Perform up to parsing on the src file and return the resulting AST.",
        )
        parser.add_argument(
            "--codegen",
            action="store_true",
            default=False,
            help="Perform up to code generation on the src file and return the resulting code.",
        )

    def handle(self, args):
        with open(args.src, "r", encoding="utf8") as f:
            ast = Parser.parse(f.read())
            if ast is None:
                return

            if args.parse:
                print(ast)
                return

            code = Generator.generate_code(ast)
            if args.codegen:
                print(code)
                return

            VM(code).interpret()


Command()
