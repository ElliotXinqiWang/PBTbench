"""Basic tests for lark."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lark import Lark, Tree, Token
from lark.visitors import Transformer, Transformer_InPlace


# ---------------------------------------------------------------------------
# Grammar helpers
# ---------------------------------------------------------------------------

SIMPLE_GRAMMAR = r"""
start: NAME+
NAME: /[a-z]+/
%ignore " "
"""

EXPR_GRAMMAR = r"""
start: NAME "=" NUMBER
NAME: /[a-z]+/
NUMBER: /[0-9]+/
%ignore " "
"""


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_parse_single_token():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    assert tree.data == 'start'
    assert len(tree.children) == 1
    assert str(tree.children[0]) == 'hello'


def test_parse_multiple_tokens():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('foo bar baz')
    assert tree.data == 'start'
    assert len(tree.children) == 3
    values = [str(c) for c in tree.children]
    assert values == ['foo', 'bar', 'baz']


def test_parse_expr():
    parser = Lark(EXPR_GRAMMAR, parser='lalr')
    tree = parser.parse('x = 42')
    assert tree.data == 'start'
    tokens = list(tree.scan_values(lambda v: True))
    assert str(tokens[0]) == 'x'
    assert str(tokens[1]) == '42'


# ---------------------------------------------------------------------------
# Tree construction and basic properties
# ---------------------------------------------------------------------------

def test_tree_data_and_children():
    t = Tree('root', ['a', 'b', 'c'])
    assert t.data == 'root'
    assert t.children == ['a', 'b', 'c']


def test_tree_eq_identical():
    t1 = Tree('rule', [Token('T', 'v')])
    t2 = Tree('rule', [Token('T', 'v')])
    assert t1 == t2


def test_tree_repr():
    t = Tree('rule', ['leaf'])
    r = repr(t)
    assert 'rule' in r


def test_tree_hash():
    t1 = Tree('rule', [Token('T', 'v')])
    t2 = Tree('rule', [Token('T', 'v')])
    assert hash(t1) == hash(t2)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_pretty_depth1_single_leaf():
    """Depth-1 tree with a single leaf: uses inline tab format."""
    t = Tree('root', ['leaf'])
    p = t.pretty()
    assert 'root' in p
    assert 'leaf' in p


def test_pretty_root_no_indent():
    """Root node must have no leading whitespace."""
    t = Tree('root', [Tree('child', ['x'])])
    lines = t.pretty().split('\n')
    # First non-empty line is the root
    first = next(l for l in lines if l.strip())
    assert first == 'root', f"Root line should have no indent: {first!r}"


# ---------------------------------------------------------------------------
# Token attributes
# ---------------------------------------------------------------------------

def test_token_type_and_value():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    tok = tree.children[0]
    assert isinstance(tok, Token)
    assert tok.type == 'NAME'
    assert str(tok) == 'hello'


def test_token_line_starts_at_1():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    tok = tree.children[0]
    assert tok.line == 1, f"Expected line=1, got {tok.line}"


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_transformer_flat_token_only():
    """Test Transformer flat token only."""
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('foo bar')

    class Upper(Transformer):
        def NAME(self, tok):
            return tok.upper()

    result = Upper().transform(tree)
    # result is Tree('start', ['FOO', 'BAR'])
    assert result.data == 'start'
    assert result.children == ['FOO', 'BAR']


def test_transformer_inplace_flat():
    """Transformer_InPlace on a flat grammar — tokens are leaves, not nested subtrees."""
    grammar = r"""
    start: NUMBER+
    NUMBER: /[0-9]+/
    %ignore " "
    """
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse('1 2 3')

    class Stringify(Transformer_InPlace):
        def NUMBER(self, tok):
            return Token('NUMBER', tok + '!')

    result = Stringify().transform(tree)
    values = [str(c) for c in result.children]
    assert values == ['1!', '2!', '3!']


# ---------------------------------------------------------------------------
# Tree.scan_values
# ---------------------------------------------------------------------------

def test_scan_values_all():
    t = Tree('root', [Token('A', 'x'), Tree('inner', [Token('B', 'y')])])
    vals = list(t.scan_values(lambda v: True))
    assert len(vals) == 2
    assert str(vals[0]) == 'x'
    assert str(vals[1]) == 'y'


def test_scan_values_filtered():
    t = Tree('root', [Token('A', 'hello'), Token('B', 'world')])
    vals = list(t.scan_values(lambda v: isinstance(v, Token) and v.type == 'A'))
    assert len(vals) == 1
    assert str(vals[0]) == 'hello'


# ---------------------------------------------------------------------------
# iter_subtrees (bottom-up ordering)
# ---------------------------------------------------------------------------

def test_iter_subtrees_includes_root():
    t = Tree('root', [Tree('child', ['x'])])
    subtrees = list(t.iter_subtrees())
    data_list = [s.data for s in subtrees]
    assert 'root' in data_list
    assert 'child' in data_list


def test_iter_subtrees_child_before_root():
    """Bottom-up: child must appear before root in iter_subtrees()."""
    t = Tree('root', [Tree('child', ['x'])])
    subtrees = list(t.iter_subtrees())
    data_list = [s.data for s in subtrees]
    assert data_list.index('child') < data_list.index('root')


# ---------------------------------------------------------------------------
# find_data
# ---------------------------------------------------------------------------

def test_find_data():
    t = Tree('root', [Tree('a', [Tree('b', ['leaf'])]), Tree('a', ['other'])])
    found = list(t.find_data('a'))
    assert len(found) == 2
