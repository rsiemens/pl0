from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase

from pl0 import VM, Generator, Parser

from .snapshot import assert_matches_snapshot

SCOPE = """\
VAR a;

PROCEDURE outer;
    var b;
    PROCEDURE inner;
        var c;
    BEGIN
        c := 3;
        WRITE a;
        WRITE b;
        WRITE c;
    END;
BEGIN
    b := 2;
    WRITE a;
    WRITE b;
    CALL inner;
END;

PROCEDURE first;
BEGIN
    WRITE a;
    call outer;
END;

BEGIN
    a := 1;
    CALL first;
END.
"""

SQUARE = """\
VAR x, squ;

PROCEDURE square;
BEGIN
   squ:= x * x
END;

BEGIN
   x := 1;
   WHILE x <= 10 DO
   BEGIN
      CALL square;
      WRITE squ;
      x := x + 1
   END
END.
"""

PRIMES = """\
const max = 100;
var arg, ret;

procedure isprime;
var i;
begin
    ret := 1;
    i := 2;
    while i < arg do
    begin
        if arg / i * i = arg then
        begin
            ret := 0;
            i := arg
        end;
        i := i + 1
    end
end;

procedure primes;
begin
    arg := 2;
    while arg < max do
    begin
        call isprime;
        if ret = 1 then write arg;
        arg := arg + 1
    end
end;

call primes
.
"""


PROGRAMS = [("scope", SCOPE), ("square", SQUARE), ("primes", PRIMES)]


class SnapshotTestCases(TestCase):
    def test_parser_snapshots(self):
        for name, program in PROGRAMS:
            assert_matches_snapshot(f"parse_{name}", Parser.parse(program))

    def test_codegen_snapshots(self):
        for name, program in PROGRAMS:
            ast = Parser.parse(program)
            assert_matches_snapshot(f"codegen_{name}", Generator.generate_code(ast))

    def test_vm_snapshots(self):
        for name, program in PROGRAMS:
            ast = Parser.parse(program)
            vm = VM(Generator.generate_code(ast))
            output = StringIO()

            with redirect_stdout(output):
                vm.interpret()

            assert_matches_snapshot(f"vm_{name}_output", output.getvalue())
            assert_matches_snapshot(f"vm_{name}_stack", vm.datastore)
