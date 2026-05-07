"""Basic tests for lark."""
import pytest
from lark import Lark, Tree, Token
from lark.visitors import Transformer, Visitor, v_args


# ---------------------------------------------------------------------------
# Grammar compilation and basic parsing
# ---------------------------------------------------------------------------

def test_simple_grammar_compiles():
    """A simple grammar can be compiled without errors."""
    parser = Lark('start: "hello"', parser='lalr')
    assert parser is not None


def test_single_terminal_parse():
    """Parse a single terminal token."""
    parser = Lark(r"""
        start: NAME
        NAME: /[a-z]+/
    """, parser='lalr')
    tree = parser.parse('hello')
    assert tree.data == 'start'
    assert len(tree.children) == 1
    assert isinstance(tree.children[0], Token)
    assert str(tree.children[0]) == 'hello'


def test_multiple_terminals_parse():
    """Parse a sequence of terminals."""
    parser = Lark(r'''
        start: NAME NAME NAME
        NAME: /[a-z]+/
        %ignore " "
    ''', parser='lalr')
    tree = parser.parse('a b c')
    assert tree.data == 'start'
    assert len(tree.children) == 3


def test_nested_rule_parse():
    """Parse a grammar with nested rules."""
    parser = Lark(r'''
        start: item
        item: NAME
        NAME: /[a-z]+/
    ''', parser='lalr')
    tree = parser.parse('hello')
    assert tree.data == 'start'
    assert tree.children[0].data == 'item'
    assert str(tree.children[0].children[0]) == 'hello'


def test_optional_rule_parse():
    """Parse a grammar with an optional element."""
    parser = Lark(r'''
        start: NAME number?
        number: NUMBER
        NAME: /[a-z]+/
        NUMBER: /[0-9]+/
        %ignore " "
    ''', parser='lalr')
    # With number
    tree = parser.parse('abc 123')
    # start has NAME + number subtree
    names = [c for c in tree.children if isinstance(c, Token)]
    numbers = [c for c in tree.children if isinstance(c, Tree)]
    assert len(names) == 1
    assert str(names[0]) == 'abc'
    assert len(numbers) == 1
    # Without number
    tree2 = parser.parse('abc')
    names2 = [c for c in tree2.children if isinstance(c, Token)]
    assert len(names2) == 1


def test_ignore_whitespace():
    """Whitespace is properly ignored when declared."""
    parser = Lark(r'''
        start: NAME+
        NAME: /[a-z]+/
        %ignore /[ \t\n]+/
    ''', parser='lalr')
    tree = parser.parse('a b c\nd')
    assert len(tree.children) == 4


# ---------------------------------------------------------------------------
# Tree structure and methods
# ---------------------------------------------------------------------------

def test_tree_data_and_children():
    """Tree has correct data and children attributes."""
    t = Tree('start', ['a', 'b'])
    assert t.data == 'start'
    assert t.children == ['a', 'b']


def test_tree_repr():
    """Tree has a useful string representation."""
    t = Tree('node', [Token('NAME', 'x')])
    r = repr(t)
    assert 'node' in r
    assert 'NAME' in r


def test_tree_equality():
    """Trees with same data and children are equal."""
    t1 = Tree('start', ['a', 'b'])
    t2 = Tree('start', ['a', 'b'])
    assert t1 == t2


def test_tree_inequality_different_data():
    """Trees with different data are not equal."""
    t1 = Tree('start', ['a'])
    t2 = Tree('end', ['a'])
    assert t1 != t2


def test_tree_inequality_different_children():
    """Trees with different children are not equal."""
    t1 = Tree('start', ['a'])
    t2 = Tree('start', ['b'])
    assert t1 != t2


def test_tree_copy():
    """Tree.copy() produces a shallow copy."""
    t = Tree('start', [Token('NAME', 'x')])
    c = t.copy()
    assert c.data == t.data
    assert c.children == t.children
    assert c is not t


def test_tree_scan_values():
    """Tree.scan_values() finds all leaf values matching a predicate."""
    t = Tree('start', [
        Tree('a', [Token('NAME', 'x')]),
        Tree('b', [Token('NAME', 'y')]),
    ])
    names = list(t.scan_values(lambda v: isinstance(v, Token)))
    assert len(names) == 2
    assert {str(n) for n in names} == {'x', 'y'}


def test_tree_find_data():
    """Tree.find_data() finds all subtrees with matching data."""
    t = Tree('start', [
        Tree('item', ['a']),
        Tree('item', ['b']),
        Tree('other', ['c']),
    ])
    items = list(t.find_data('item'))
    assert len(items) == 2


# ---------------------------------------------------------------------------
# Token properties
# ---------------------------------------------------------------------------

def test_token_type_and_value():
    """Token has correct type and value."""
    tok = Token('NAME', 'hello')
    assert tok.type == 'NAME'
    assert str(tok) == 'hello'


def test_token_is_string():
    """Token inherits from str and supports string operations."""
    tok = Token('NAME', 'hello')
    assert tok.upper() == 'HELLO'
    assert len(tok) == 5


# ---------------------------------------------------------------------------
# Basic transformer (standard Transformer, not _InPlace or _InPlaceRecursive)
# ---------------------------------------------------------------------------

def test_standard_transformer_converts_tokens():
    """Standard Transformer correctly converts tokens bottom-up."""
    parser = Lark(r'''
        start: NUMBER "+" NUMBER
        NUMBER: /[0-9]+/
        %ignore " "
    ''', parser='lalr')

    class Calc(Transformer):
        def NUMBER(self, tok):
            return int(tok)
        def start(self, children):
            return children[0] + children[1]

    tree = parser.parse('3 + 4')
    result = Calc().transform(tree)
    assert result == 7


def test_standard_visitor_basic():
    """Standard Visitor calls user methods for each subtree."""
    parser = Lark(r'''
        start: item item
        item: NAME
        NAME: /[a-z]+/
        %ignore " "
    ''', parser='lalr')
    tree = parser.parse('a b')

    visited = []

    class CollectVisitor(Visitor):
        def item(self, t):
            visited.append(str(t.children[0]))

    CollectVisitor().visit(tree)
    assert set(visited) == {'a', 'b'}
