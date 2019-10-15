"""
The PL/0 Parser
===============

A recursive decent parser for the following grammar expressed in EBNF.

program = block ".";
block = ["const" ident "=" number {"," ident "=" number} ";"]
        ["var" ident {"," ident} ";"]
        {"procedure" ident ";" block ";"} statement;
statement = [ident ":=" expression
             | "call" ident
             | "if" condition "then" statement
             | "begin" statement {";" statement} "end"
             | "while" condition "do" statement
             | "write" expression
             | "debug"];
condition = "odd" expression |
            expression ("=" | "!=" | "<" | "<=" | ">" | ">=") expression;
expression = ["+" | "-" ] term {("+" | "-") term};
term = factor {("*" | "/") factor};
factor = ident | number | "(" expression ")";
ident = ascii_letter {ascii_letter | ascii_digit};
number = ascii_digit {ascii_digit};
"""
import string
import sys

ERROR_CODES = {
    1: "Use = instead of :=",
    2: "= must be followed by a number",
    3: "Identifier must be followed by =",
    4: "const, var, procedure must be followed by an identifier",
    5: "Semicolon or comma missing",
    6: "Incorrect symbol after procedure declaration",
    7: "Statement expected",
    8: "Incorrect symbol after statement part in block",
    9: "Period expected",
    10: "Semicolon between statements is missing",
    11: "Undeclared identifier",
    12: "Assignment to constant or procedure is not allowed",
    13: "Assignment operator := expected",
    14: "call must be followed by an identifier",
    15: "Call of a constant or variable is meaningless",
    16: "then expected",
    17: "Semicolon or end expected",
    18: "do expected",
    19: "Incorrect symbol following statement",
    20: "Relational operator expected",
    21: "Expression must not contain a procedure identifier",
    22: "Right parenthesis missing",
    23: "The preceding factor cannot be followed by this symbol",
    24: "An expression cannot begin with this symbol",
    30: "This number is too large",
}


class ParserException(Exception):
    def __init__(self, error_code, line, token):
        self.code = error_code
        self.message = (
            f"{ERROR_CODES[error_code]} - got {token} "
            f"{token.line}:{token.column}\n{line}"
        )
        super().__init__(self.message)


class Symbol:
    NULL = "NULL"
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    TIMES = "TIMES"
    SLASH = "SLASH"
    ODD = "ODD"
    EQL = "EQL"
    NEQ = "NEQ"
    LESS = "LESS"
    LEQ = "LEQ"
    GTR = "GTR"
    GEQ = "GEQ"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    PERIOD = "PERIOD"
    BECOMES = "BECOMES"
    BEGIN = "BEGIN"
    END = "END"
    IF = "IF"
    THEN = "THEN"
    WHILE = "WHILE"
    DO = "DO"
    CALL = "CALL"
    CONST = "CONST"
    VAR = "VAR"
    PROC = "PROC"
    WRITE = "WRITE"
    DEBUG = "DEBUG"


class Token:
    def __init__(self, symbol, value=None, line=0, column=0):
        self.symbol = symbol
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"{self.line}:{self.column} {self.symbol} {self.value}"

    def __str__(self):
        return f"{self.symbol}"

    def __eq__(self, other):
        return self.symbol == other


class Lexer:
    KEYWORDS = {
        "BEGIN": Symbol.BEGIN,
        "CALL": Symbol.CALL,
        "CONST": Symbol.CONST,
        "DO": Symbol.DO,
        "END": Symbol.END,
        "IF": Symbol.IF,
        "ODD": Symbol.ODD,
        "PROCEDURE": Symbol.PROC,
        "THEN": Symbol.THEN,
        "VAR": Symbol.VAR,
        "WHILE": Symbol.WHILE,
        "WRITE": Symbol.WRITE,
        "DEBUG": Symbol.DEBUG,
    }

    def __init__(self, input):
        self.input = input
        self.cursor = -1
        self.line = 1
        self.column = 0

    def get_char(self):
        self.cursor += 1
        self.column += 1
        try:
            return self.input[self.cursor]
        except IndexError:
            return "\0"

    def peek_next(self):
        try:
            return self.input[self.cursor + 1]
        except IndexError:
            return "\0"

    def get_token(self):
        char = self.get_char()
        while char in " \t\n":
            if char == "\n":
                self.line += 1
                self.column = 0
            char = self.get_char()

        # Identifiers and keywords start with an ascii letter
        if char in string.ascii_letters:
            word = char
            while self.peek_next() in string.ascii_letters + string.digits:
                word += self.get_char()

            keyword = self.KEYWORDS.get(word.upper())
            if keyword is not None:
                return Token(keyword, line=self.line, column=self.column)
            else:
                return Token(Symbol.IDENT, word, line=self.line, column=self.column)
        elif char in string.digits:
            num = char
            while self.peek_next() in string.digits:
                num += self.get_char()
            return Token(Symbol.NUMBER, int(num), line=self.line, column=self.column)
        elif char == ":":
            char = self.get_char()
            if char == "=":
                return Token(Symbol.BECOMES, line=self.line, column=self.column)
            return Token(Symbol.NULL, line=self.line, column=self.column)
        elif char == "+":
            return Token(Symbol.PLUS, line=self.line, column=self.column)
        elif char == "-":
            return Token(Symbol.MINUS, line=self.line, column=self.column)
        elif char == "*":
            return Token(Symbol.TIMES, line=self.line, column=self.column)
        elif char == "/":
            return Token(Symbol.SLASH, line=self.line, column=self.column)
        elif char == "(":
            return Token(Symbol.LPAREN, line=self.line, column=self.column)
        elif char == ")":
            return Token(Symbol.RPAREN, line=self.line, column=self.column)
        elif char == "=":
            return Token(Symbol.EQL, line=self.line, column=self.column)
        elif char == ",":
            return Token(Symbol.COMMA, line=self.line, column=self.column)
        elif char == ".":
            return Token(Symbol.PERIOD, line=self.line, column=self.column)
        elif char == ";":
            return Token(Symbol.SEMICOLON, line=self.line, column=self.column)
        elif char == "<":
            if self.peek_next() == "=":
                self.get_char()
                return Token(Symbol.LEQ, line=self.line, column=self.column)
            return Token(Symbol.LESS, line=self.line, column=self.column)
        elif char == ">":
            if self.peek_next() == "=":
                self.get_char()
                return Token(Symbol.GEQ, line=self.line, column=self.column)
            return Token(Symbol.GTR, line=self.line, column=self.column)
        elif char == "!":
            char = self.get_char()
            if char == "=":
                return Token(Symbol.NEQ, line=self.line, column=self.column)
            return Token(Symbol.NULL, line=self.line, column=self.column)
        else:
            return Token(Symbol.NULL, line=self.line, column=self.column)


class Parser:
    def __init__(self, input):
        self.lexer = Lexer(input.strip())
        self.token = self.lexer.get_token()
        self.declarations = {}
        self.code = []

    @classmethod
    def parse(cls, input):
        try:
            return cls(input).program()
        except ParserException as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()

    def program(self):
        program = self.block()
        self.match(Symbol.PERIOD, 9)
        return program

    def block(self):
        blocks = []
        if self.token == Symbol.CONST:
            self.get_token()
            blocks.append(self.const_declaration())
            while self.token == Symbol.COMMA:
                self.get_token()
                blocks.append(self.const_declaration())
            self.match(Symbol.SEMICOLON, 5)

        if self.token == Symbol.VAR:
            self.get_token()
            blocks.append(self.var_declaration())
            while self.token == Symbol.COMMA:
                self.get_token()
                blocks.append(self.var_declaration())
            self.match(Symbol.SEMICOLON, 5)

        while self.token == Symbol.PROC:
            self.get_token()
            ident = self.match(Symbol.IDENT, 4)
            self.declarations[ident] = Symbol.PROC
            self.match(Symbol.SEMICOLON, 5)
            blocks.append(self.node("Procedure", name=ident, blocks=self.block()))
            self.match(Symbol.SEMICOLON, 5)

        statement = self.statement()
        if statement is not None:
            blocks.append(statement)
        return blocks

    def const_declaration(self):
        ident = self.match(Symbol.IDENT, 4)
        self.match(Symbol.EQL, 3)
        value = self.match(Symbol.NUMBER, 2)
        self.declarations[ident] = Symbol.CONST
        return self.node("Const", name=ident, value=value)

    def var_declaration(self):
        ident = self.match(Symbol.IDENT, 4)
        self.declarations[ident] = Symbol.VAR
        return self.node("Var", name=ident)

    def statement(self):
        if self.token == Symbol.IDENT:
            ident = self.token.value
            declaration_type = self.declarations.get(ident)
            if declaration_type is None:
                self.error(11)
            if declaration_type != Symbol.VAR:
                self.error(12)
            self.get_token()
            self.match(Symbol.BECOMES, 13)
            return self.node("Assignment", name=ident, value=self.expression())

        if self.token == Symbol.CALL:
            self.get_token()
            ident = self.match(Symbol.IDENT, 14)
            declaration_type = self.declarations.get(ident)
            if declaration_type is None:
                self.error(11)
            if declaration_type != Symbol.PROC:
                self.error(15)
            return self.node("Call", name=ident)

        if self.token == Symbol.IF:
            self.get_token()
            condition = self.condition()
            self.match(Symbol.THEN, 16)
            return self.node("If", condition=condition, body=self.statement())

        if self.token == Symbol.BEGIN:
            self.get_token()
            statements = [self.statement()]
            while self.token == Symbol.SEMICOLON:
                self.get_token()
                statement = self.statement()
                if statement:
                    statements.append(statement)
            self.match(Symbol.END, 17)
            return self.node("Block", statements=statements)

        if self.token == Symbol.WHILE:
            self.get_token()
            condition = self.condition()
            self.match(Symbol.DO, 18)
            return self.node("Loop", condition=condition, body=self.statement())

        if self.token == Symbol.WRITE:
            self.get_token()
            return self.node("Output", value=self.expression())

        if self.token == Symbol.DEBUG:
            self.get_token()
            return self.node("Debug")

        return None

    def condition(self):
        if self.token == Symbol.ODD:
            self.get_token()
            return self.node("Odd", expression=self.expression())

        left = self.expression()
        if self.token not in [
            Symbol.EQL,
            Symbol.NEQ,
            Symbol.LESS,
            Symbol.LEQ,
            Symbol.GTR,
            Symbol.GEQ,
        ]:
            self.error(20)
        operator = self.token
        self.get_token()
        return self.node(
            "Binary", left=left, right=self.expression(), operator=operator
        )

    def expression(self):
        if self.token in [Symbol.PLUS, Symbol.MINUS]:
            operator = self.token
            self.get_token()
            if operator == Symbol.MINUS:
                expr = self.node("Unary", operator=operator, right=self.term())
            else:
                expr = self.term()
        else:
            expr = self.term()

        while self.token in [Symbol.PLUS, Symbol.MINUS]:
            operator = self.token
            self.get_token()
            expr = self.node("Binary", left=expr, right=self.term(), operator=operator)

        return expr

    def term(self):
        expr = self.factor()
        while self.token in [Symbol.TIMES, Symbol.SLASH]:
            operator = self.token
            self.get_token()
            expr = self.node(
                "Binary", left=expr, right=self.factor(), operator=operator
            )
        return expr

    def factor(self):
        if self.token == Symbol.IDENT:
            value = self.token.value
            declaration_type = self.declarations.get(value)
            if declaration_type is None:
                self.error(11)
            if declaration_type == Symbol.PROC:
                self.error(21)
            self.get_token()
            return self.node("Identifier", name=value)

        if self.token == Symbol.NUMBER:
            value = self.token.value
            self.get_token()
            return self.node("Number", value=value)

        if self.token == Symbol.LPAREN:
            self.get_token()
            expression = self.expression()
            self.match(Symbol.RPAREN, 22)
            return self.node("Grouping", expression=expression)

        self.error(23)

    def error(self, error_num):
        lines = self.lexer.input.split("\n")
        start_context = ""
        after_context = ""

        if self.token.line - 1 > 1:
            start_context = f"{lines[self.token.line - 2]}\n"

        line = self.lexer.input.split("\n")[self.token.line - 1]
        line += "\n" + (" " * (self.token.column - 1)) + "^"

        if len(lines) - 1 > self.token.line:
            after_context = f"\n{lines[self.token.line]}"

        line = f"{start_context}{line}{after_context}"
        raise ParserException(error_num, line, self.token)

    def get_token(self):
        self.token = self.lexer.get_token()
        return self.token

    def match(self, symbol, error_code):
        value = self.token.value
        if self.token == symbol:
            self.get_token()
        else:
            self.error(error_code)
        return value

    def node(self, type, **kwargs):
        return dict(type=type, **kwargs)
