"""Basic tests for pycparser."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pycparser import c_parser, c_generator


def _parse(code):
    parser = c_parser.CParser()
    return parser.parse(code, filename="<none>")


def _generate(code):
    ast = _parse(code)
    gen = c_generator.CGenerator()
    return gen.visit(ast)


def test_simple_return_value():
    """Return a simple integer constant — no comma expression involved."""
    code = "int f() { return 42; }"
    out = _generate(code)
    assert "return 42" in out


def test_return_variable():
    """Return a simple variable — no comma expression."""
    code = "int f(int x) { return x; }"
    out = _generate(code)
    assert "return x" in out


def test_return_binary_op():
    """Return the result of a binary operation."""
    code = "int f(int a, int b) { return a + b; }"
    out = _generate(code)
    assert "return" in out
    assert "a + b" in out


def test_return_function_call():
    """Return the result of a function call."""
    code = "int f() { return g(); }"
    out = _generate(code)
    assert "return g()" in out


def test_simple_assignment():
    """Simple assignment of a constant — no comma expression."""
    code = "void f() { int x; x = 10; }"
    out = _generate(code)
    assert "x = 10" in out


def test_assignment_from_variable():
    """Assignment from another variable."""
    code = "void f(int a) { int x; x = a; }"
    out = _generate(code)
    assert "x = a" in out


def test_assignment_binary_expr():
    """Assignment of an arithmetic expression."""
    code = "void f(int a, int b) { int x; x = a + b; }"
    out = _generate(code)
    assert "x = a + b" in out


def test_if_else_generation():
    """Generate an if-else statement."""
    code = "void f(int x) { if (x > 0) { x = 1; } else { x = -1; } }"
    out = _generate(code)
    assert "if" in out
    assert "else" in out


def test_while_loop():
    """Generate a while loop."""
    code = "void f(int n) { while (n > 0) { n = n - 1; } }"
    out = _generate(code)
    assert "while" in out


def test_for_loop():
    """Generate a for loop."""
    code = "void f() { int i; for (i = 0; i < 10; i = i + 1) { } }"
    out = _generate(code)
    assert "for" in out


def test_function_with_params():
    """Generate a function with multiple parameters."""
    code = "int add(int a, int b) { return a + b; }"
    out = _generate(code)
    assert "int add" in out
    assert "int a" in out
    assert "int b" in out


def test_struct_declaration():
    """Generate a struct declaration."""
    code = "struct Point { int x; int y; };"
    out = _generate(code)
    assert "struct" in out
    assert "Point" in out
