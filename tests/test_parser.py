from unittest import TestCase

from pl0.parser import Lexer, Parser, ParserException, Symbol


class LexerTestCases(TestCase):
    def test_get_char(self):
        prog = "var a, b;"
        lexer = Lexer(prog)

        for i, char in enumerate(prog):
            self.assertEqual(lexer.get_char(), char)
            self.assertEqual(lexer.cursor, i)
            self.assertEqual(lexer.column, i + 1)

        self.assertEqual(lexer.get_char(), "\0")

    def test_peek_next(self):
        lexer = Lexer("bar")

        # peeking multiple times returns the same char
        self.assertEqual(lexer.peek_next(), "b")
        self.assertEqual(lexer.peek_next(), "b")
        self.assertEqual(lexer.get_char(), "b")

        self.assertEqual(lexer.peek_next(), "a")
        self.assertEqual(lexer.get_char(), "a")

        self.assertEqual(lexer.peek_next(), "r")
        self.assertEqual(lexer.get_char(), "r")

        self.assertEqual(lexer.peek_next(), "\0")

    def test_get_symbol(self):
        prog = """\
        const m = 7, n = 85;
        var x,y,z,q,r;

        procedure multiply;
            var a,b;
        begin
            a := x; b := y; z:= 0;
            while b > 0 do
            begin
                if odd b then
                    z := z + a;
                a := 2*a; b := b/2;
            end
        end;

        begin
            x := m; y:= n; call multiply;
        end.
        """
        lexer = Lexer(prog)
        expected = [
            (Symbol.CONST, None),
            (Symbol.IDENT, "m"),
            (Symbol.EQL, None),
            (Symbol.NUMBER, 7),
            (Symbol.COMMA, None),
            (Symbol.IDENT, "n"),
            (Symbol.EQL, None),
            (Symbol.NUMBER, 85),
            (Symbol.SEMICOLON, None),
            (Symbol.VAR, None),
            (Symbol.IDENT, "x"),
            (Symbol.COMMA, None),
            (Symbol.IDENT, "y"),
            (Symbol.COMMA, None),
            (Symbol.IDENT, "z"),
            (Symbol.COMMA, None),
            (Symbol.IDENT, "q"),
            (Symbol.COMMA, None),
            (Symbol.IDENT, "r"),
            (Symbol.SEMICOLON, None),
            (Symbol.PROC, None),
            (Symbol.IDENT, "multiply"),
            (Symbol.SEMICOLON, None),
            (Symbol.VAR, None),
            (Symbol.IDENT, "a"),
            (Symbol.COMMA, None),
            (Symbol.IDENT, "b"),
            (Symbol.SEMICOLON, None),
            (Symbol.BEGIN, None),
            (Symbol.IDENT, "a"),
            (Symbol.BECOMES, None),
            (Symbol.IDENT, "x"),
            (Symbol.SEMICOLON, None),
            (Symbol.IDENT, "b"),
            (Symbol.BECOMES, None),
            (Symbol.IDENT, "y"),
            (Symbol.SEMICOLON, None),
            (Symbol.IDENT, "z"),
            (Symbol.BECOMES, None),
            (Symbol.NUMBER, 0),
            (Symbol.SEMICOLON, None),
        ]

        for index, expected_items in enumerate(expected):
            expected_symbol, expected_value = expected_items
            token = lexer.get_token()
            self.assertEqual(token, expected_symbol, msg=index)
            self.assertEqual(token.value, expected_value, msg=index)


class ParserTestCases(TestCase):
    maxDiff = None

    def test_program(self):
        # simplest legal program
        self.assertEqual(Parser(".").program(), [])

    def test_block(self):
        # Const declaration
        self.assertEqual(
            Parser("const x = 4;").block(), [{"type": "Const", "name": "x", "value": 4}]
        )
        self.assertEqual(
            Parser("const x = 4, y = 5, z = 6;").block(),
            [
                {"type": "Const", "name": "x", "value": 4},
                {"type": "Const", "name": "y", "value": 5},
                {"type": "Const", "name": "z", "value": 6},
            ],
        )

        # Var declaration
        self.assertEqual(Parser("var x;").block(), [{"type": "Var", "name": "x"}])
        self.assertEqual(
            Parser("var x, y, z;").block(),
            [
                {"type": "Var", "name": "x"},
                {"type": "Var", "name": "y"},
                {"type": "Var", "name": "z"},
            ],
        )

        # Procedure declaration
        self.assertEqual(
            Parser("procedure foo; write 10;").block(),
            [
                {
                    "type": "Procedure",
                    "name": "foo",
                    "parameters": [],
                    "blocks": [
                        {"type": "Output", "value": {"type": "Number", "value": 10}}
                    ],
                }
            ],
        )
        self.assertEqual(
            Parser("procedure foo; write 10; procedure bar; write 11;").block(),
            [
                {
                    "type": "Procedure",
                    "name": "foo",
                    "parameters": [],
                    "blocks": [
                        {"type": "Output", "value": {"type": "Number", "value": 10}}
                    ],
                },
                {
                    "type": "Procedure",
                    "name": "bar",
                    "parameters": [],
                    "blocks": [
                        {"type": "Output", "value": {"type": "Number", "value": 11}}
                    ],
                },
            ],
        )

        self.assertEqual(
            Parser("procedure foo; write 10; procedure bar; write 11;").block(),
            [
                {
                    "type": "Procedure",
                    "name": "foo",
                    "parameters": [],
                    "blocks": [
                        {"type": "Output", "value": {"type": "Number", "value": 10}}
                    ],
                },
                {
                    "type": "Procedure",
                    "name": "bar",
                    "parameters": [],
                    "blocks": [
                        {"type": "Output", "value": {"type": "Number", "value": 11}}
                    ],
                },
            ],
        )

        # Procedure declaration with parameters
        self.assertEqual(
            Parser("procedure foo(a, b); write 10;").block(),
            [
                {
                    "type": "Procedure",
                    "name": "foo",
                    "parameters": [
                        {"type": "Var", "name": "a"},
                        {"type": "Var", "name": "b"},
                    ],
                    "blocks": [
                        {"type": "Output", "value": {"type": "Number", "value": 10}}
                    ],
                }
            ],
        )

        # Statement block
        parser = Parser("x := 1")
        parser.declarations["x"] = Symbol.VAR
        self.assertEqual(
            parser.block(),
            [
                {
                    "type": "Assignment",
                    "name": "x",
                    "value": {"type": "Number", "value": 1},
                }
            ],
        )
        self.assertEqual(Parser("").block(), [])

    def test_statement(self):
        # Assignment statement
        parser = Parser("x := 4")
        parser.declarations["x"] = Symbol.VAR
        self.assertEqual(
            parser.statement(),
            {
                "type": "Assignment",
                "name": "x",
                "value": {"type": "Number", "value": 4},
            },
        )

        # Procedure call statement
        parser = Parser("call foo")
        parser.declarations["foo"] = Symbol.PROC
        self.assertEqual(parser.statement(), {"type": "Call", "name": "foo", "arguments": []})

        # Procedure call statement with arguments
        parser = Parser("call foo(a, b + 4)")
        parser.declarations["foo"] = Symbol.PROC
        parser.declarations["a"] = Symbol.VAR
        parser.declarations["b"] = Symbol.VAR
        self.assertEqual(
            parser.statement(),
            {
                "type": "Call",
                "name": "foo",
                "arguments": [
                    {"type": "Identifier", "name": "a"},
                    {
                        "type": "Binary",
                        "left": {"type": "Identifier", "name": "b"},
                        "right": {"type": "Number", "value": 4},
                        "operator": Symbol.PLUS,
                    }
                ]
            }
        )

        # If statement
        parser = Parser("if x < 4 then write x")
        parser.declarations["x"] = Symbol.VAR
        self.assertEqual(
            parser.statement(),
            {
                "type": "If",
                "condition": {
                    "type": "Binary",
                    "left": {"type": "Identifier", "name": "x"},
                    "right": {"type": "Number", "value": 4},
                    "operator": Symbol.LESS,
                },
                "body": {
                    "type": "Output",
                    "value": {"type": "Identifier", "name": "x"},
                },
            },
        )

        # Block statement
        parser = Parser("begin x := 3; y:= x * 4; end")
        parser.declarations["x"] = Symbol.VAR
        parser.declarations["y"] = Symbol.VAR
        self.assertEqual(
            parser.statement(),
            {
                "type": "Block",
                "statements": [
                    {
                        "type": "Assignment",
                        "name": "x",
                        "value": {"type": "Number", "value": 3},
                    },
                    {
                        "type": "Assignment",
                        "name": "y",
                        "value": {
                            "type": "Binary",
                            "left": {"type": "Identifier", "name": "x"},
                            "right": {"type": "Number", "value": 4},
                            "operator": Symbol.TIMES,
                        },
                    },
                ],
            },
        )

        # While statement
        parser = Parser("while i < 10 do i := i + 1")
        parser.declarations["i"] = Symbol.VAR
        self.assertEqual(
            parser.statement(),
            {
                "type": "Loop",
                "condition": {
                    "type": "Binary",
                    "left": {"type": "Identifier", "name": "i"},
                    "right": {"type": "Number", "value": 10},
                    "operator": Symbol.LESS,
                },
                "body": {
                    "type": "Assignment",
                    "name": "i",
                    "value": {
                        "type": "Binary",
                        "left": {"type": "Identifier", "name": "i"},
                        "right": {"type": "Number", "value": 1},
                        "operator": Symbol.PLUS,
                    },
                },
            },
        )

        # Write statement
        self.assertEqual(
            Parser("write 10").statement(),
            {"type": "Output", "value": {"type": "Number", "value": 10}},
        )

        # Debug statement
        self.assertEqual(Parser("Debug").statement(), {"type": "Debug"})

        # Statements have a noop
        self.assertEqual(Parser("").statement(), None)

    def test_condition(self):
        self.assertEqual(
            Parser("odd 4 * 3").condition(),
            {
                "type": "Odd",
                "expression": {
                    "type": "Binary",
                    "left": {"type": "Number", "value": 4},
                    "right": {"type": "Number", "value": 3},
                    "operator": Symbol.TIMES,
                },
            },
        )

        for symbol, repr in [
            (Symbol.EQL, "="),
            (Symbol.NEQ, "!="),
            (Symbol.LESS, "<"),
            (Symbol.LEQ, "<="),
            (Symbol.GTR, ">"),
            (Symbol.GEQ, ">="),
        ]:
            self.assertEqual(
                Parser(f"4 {repr} 3").condition(),
                {
                    "type": "Binary",
                    "left": {"type": "Number", "value": 4},
                    "right": {"type": "Number", "value": 3},
                    "operator": symbol,
                },
            )

        with self.assertRaises(ParserException):
            Parser("4 ~ 3").condition()

    def test_expression(self):
        self.assertEqual(Parser("+4").expression(), {"type": "Number", "value": 4})
        # unary
        self.assertEqual(
            Parser("-4").expression(),
            {
                "type": "Unary",
                "operator": Symbol.MINUS,
                "right": {"type": "Number", "value": 4},
            },
        )

        self.assertEqual(
            Parser("1 + 2").expression(),
            {
                "type": "Binary",
                "left": {"type": "Number", "value": 1},
                "right": {"type": "Number", "value": 2},
                "operator": Symbol.PLUS,
            },
        )

        self.assertEqual(
            Parser("1 - 2").expression(),
            {
                "type": "Binary",
                "left": {"type": "Number", "value": 1},
                "right": {"type": "Number", "value": 2},
                "operator": Symbol.MINUS,
            },
        )

        self.assertEqual(
            Parser("1 * 2 + 4 / 3 - 5").expression(),
            {
                "type": "Binary",
                "left": {
                    "type": "Binary",
                    "left": {
                        "type": "Binary",
                        "left": {"type": "Number", "value": 1},
                        "right": {"type": "Number", "value": 2},
                        "operator": Symbol.TIMES,
                    },
                    "right": {
                        "type": "Binary",
                        "left": {"type": "Number", "value": 4},
                        "right": {"type": "Number", "value": 3},
                        "operator": Symbol.SLASH,
                    },
                    "operator": Symbol.PLUS,
                },
                "right": {"type": "Number", "value": 5},
                "operator": Symbol.MINUS,
            },
        )

    def test_term(self):
        # recurses to factor
        self.assertEqual(Parser("1").term(), {"type": "Number", "value": 1})

        self.assertEqual(
            Parser("1 * 2").term(),
            {
                "type": "Binary",
                "left": {"type": "Number", "value": 1},
                "right": {"type": "Number", "value": 2},
                "operator": Symbol.TIMES,
            },
        )

        self.assertEqual(
            Parser("1 / 2").term(),
            {
                "type": "Binary",
                "left": {"type": "Number", "value": 1},
                "right": {"type": "Number", "value": 2},
                "operator": Symbol.SLASH,
            },
        )

        self.assertEqual(
            Parser("1 / 2 * 4 * 2").term(),
            {
                "type": "Binary",
                "left": {
                    "type": "Binary",
                    "left": {
                        "type": "Binary",
                        "left": {"type": "Number", "value": 1},
                        "right": {"type": "Number", "value": 2},
                        "operator": Symbol.SLASH,
                    },
                    "right": {"type": "Number", "value": 4},
                    "operator": Symbol.TIMES,
                },
                "right": {"type": "Number", "value": 2},
                "operator": Symbol.TIMES,
            },
        )

    def test_factor(self):
        # no x declaration
        with self.assertRaises(ParserException):
            Parser("x").factor()

        # proc declaration
        with self.assertRaises(ParserException):
            parser = Parser("x")
            parser.declarations["x"] = Symbol.PROC
            parser.factor()

        # identifier node
        parser = Parser("x")
        parser.declarations["x"] = Symbol.VAR
        self.assertEqual(parser.factor(), {"type": "Identifier", "name": "x"})

        # number node
        self.assertEqual(Parser("24").factor(), {"type": "Number", "value": 24})

        # no right paren
        with self.assertRaises(ParserException):
            Parser("(23").factor()

        # grouping node
        self.assertEqual(
            Parser("(23)").factor(),
            {"type": "Grouping", "expression": {"type": "Number", "value": 23}},
        )

        with self.assertRaises(ParserException):
            Parser("=").factor()
