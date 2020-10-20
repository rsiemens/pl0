import argparse

from pl0 import VM, Generator, Parser, transpile


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
        parser.add_argument(
            "--transpile",
            action="store",
            dest="transpile_target",
            type=str,
            default=None,
            help="Transpile to target",
        )

    def handle(self, args):
        with open(args.src, "r", encoding="utf8") as f:
            if args.transpile_target != None:
                print(transpile(f.read(), target=args.transpile_target.lower()))
                return

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
