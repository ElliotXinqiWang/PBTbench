"""Basic tests for lark."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lark import Lark, Tree, Token
from lark.visitors import Transformer, Transformer_InPlace, Visitor, v_args


# ---------------------------------------------------------------------------
# Grammars used across multiple tests
# ---------------------------------------------------------------------------

_SIMPLE_GRAMMAR = r"""
start: WORD+
WORD: /[a-z]+/
%ignore " "
"""

_ARITH_GRAMMAR = r"""
start: expr ("+" expr)*
expr: NUMBER
NUMBER: /[0-9]+/
%ignore " "
"""

_STMT_GRAMMAR = r"""
start: assign+
assign: NAME "=" NUMBER NEWLINE
NAME: /[a-z]+/
NUMBER: /[0-9]+/
NEWLINE: /\n/
%ignore " "
"""


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_parse_single_word():
    parser = Lark(_SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    assert tree.data == 'start'
    assert len(tree.children) == 1
    assert str(tree.children[0]) == 'hello'


def test_parse_multiple_words():
    parser = Lark(_SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('foo bar baz')
    assert tree.data == 'start'
    assert len(tree.children) == 3
    words = [str(c) for c in tree.children]
    assert words == ['foo', 'bar', 'baz']


def test_parse_arithmetic():
    parser = Lark(_ARITH_GRAMMAR, parser='lalr')
    tree = parser.parse('3 + 7 + 2')
    assert tree.data == 'start'
    # 3 expr nodes + 2 expr nodes = 3 children (3 expr trees)
    exprs = [c for c in tree.children if isinstance(c, Tree)]
    assert len(exprs) == 3


# ---------------------------------------------------------------------------
# Transformer (standard, not InPlaceRecursive)
# ---------------------------------------------------------------------------

def test_transformer_uppercase():
    parser = Lark(_SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello world')

    class Upper(Transformer):
        def WORD(self, tok):
            return tok.upper()

    result = Upper().transform(tree)
    assert result.data == 'start'
    assert result.children == ['HELLO', 'WORLD']


def test_transformer_collect_numbers():
    parser = Lark(_ARITH_GRAMMAR, parser='lalr')
    tree = parser.parse('5 + 3')

    class CollectNums(Transformer):
        def NUMBER(self, tok):
            return int(tok)
        def expr(self, children):
            return children[0]
        def start(self, children):
            return children

    result = CollectNums().transform(tree)
    assert result == [5, 3]


def test_transformer_inplace_tokens():
    """Transformer_InPlace with token-only transformation (no InPlaceRecursive)."""
    parser = Lark(_SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('abc def')

    class MarkTIP(Transformer_InPlace):
        def WORD(self, tok):
            return Token('WORD', tok + '!')

    result = MarkTIP().transform(tree)
    assert result.children == ['abc!', 'def!']


# ---------------------------------------------------------------------------
# Visitor.visit (bottom-up, not visit_topdown)
# ---------------------------------------------------------------------------

def test_visitor_visit_bottom_up():
    """Test Visitor visit bottom up."""
    parser = Lark(_ARITH_GRAMMAR, parser='lalr')
    tree = parser.parse('1 + 2')
    visited = []

    class Recorder(Visitor):
        def expr(self, t):
            visited.append('expr')
        def start(self, t):
            visited.append('start')

    Recorder().visit(tree)
    # Bottom-up: expr nodes before start
    assert 'expr' in visited
    assert 'start' in visited
    assert visited.index('expr') < visited.index('start')


def test_visitor_returns_tree():
    """Visitor.visit() must return the (modified in-place) tree."""
    t = Tree('root', [Tree('child', ['leaf'])])

    class Noop(Visitor):
        pass

    result = Noop().visit(t)
    assert result is t


# ---------------------------------------------------------------------------
# Tree construction and basic properties
# ---------------------------------------------------------------------------

def test_tree_data_children():
    t = Tree('rule', [Token('T', 'v'), 'literal'])
    assert t.data == 'rule'
    assert len(t.children) == 2


def test_tree_equality_same():
    t1 = Tree('rule', [Token('T', 'v')])
    t2 = Tree('rule', [Token('T', 'v')])
    assert t1 == t2


def test_tree_equality_different_data():
    t1 = Tree('a', [1])
    t2 = Tree('b', [1])
    assert t1 != t2


def test_tree_repr():
    t = Tree('node', ['child'])
    assert 'node' in repr(t)


def test_tree_iter_subtrees_bottom_up():
    """iter_subtrees() is documented as bottom-up (postorder)."""
    root = Tree('root', [Tree('child', ['leaf'])])
    subtrees = list(root.iter_subtrees())
    names = [s.data for s in subtrees]
    assert 'root' in names
    assert 'child' in names
    assert names.index('child') < names.index('root')


def test_tree_iter_subtrees_topdown():
    """iter_subtrees_topdown() is documented as top-down (breadth-first)."""
    root = Tree('root', [Tree('child', ['leaf'])])
    subtrees = list(root.iter_subtrees_topdown())
    names = [s.data for s in subtrees]
    assert names.index('root') < names.index('child')


def test_tree_scan_values_all():
    t = Tree('root', [Token('A', 'x'), Tree('sub', [Token('B', 'y')])])
    vals = list(t.scan_values(lambda v: True))
    assert len(vals) == 2
    strs = {str(v) for v in vals}
    assert 'x' in strs
    assert 'y' in strs


def test_tree_scan_values_filtered():
    t = Tree('root', [Token('A', 'hello'), Token('B', 'world')])
    vals = list(t.scan_values(lambda v: isinstance(v, Token) and v.type == 'A'))
    assert len(vals) == 1
    assert str(vals[0]) == 'hello'


def test_tree_pretty_root_level():
    """Root node must have no leading whitespace in pretty()."""
    t = Tree('root', ['leaf'])
    p = t.pretty()
    lines = [l for l in p.split('\n') if l.strip()]
    assert lines[0].startswith('root')
    assert not lines[0].startswith(' ')


# ---------------------------------------------------------------------------
# Token construction and attributes
# ---------------------------------------------------------------------------

def test_token_type_value():
    tok = Token('NAME', 'foo')
    assert tok.type == 'NAME'
    assert str(tok) == 'foo'
    assert tok.value == 'foo'


def test_token_eq_same_type_value():
    t1 = Token('NAME', 'foo')
    t2 = Token('NAME', 'foo')
    assert t1 == t2


def test_token_eq_diff_value():
    """Tokens with different values are not equal."""
    t1 = Token('NAME', 'foo')
    t2 = Token('NAME', 'bar')
    assert t1 != t2


def test_token_str_operations():
    """Token inherits from str; string operations work on the value."""
    tok = Token('NAME', 'hello')
    assert tok.upper() == 'HELLO'
    assert tok + '!' == 'hello!'
    assert len(tok) == 5


def test_parse_token_line_column():
    """Parsed tokens have line and column attributes (1-indexed)."""
    parser = Lark(_SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('abc')
    tok = tree.children[0]
    assert tok.line == 1
    assert tok.column == 1


# ---------------------------------------------------------------------------
# v_args decorator — method-level (inline=True on a single method)
# ---------------------------------------------------------------------------

def test_v_args_inline_single_method():
    """@v_args(inline=True) on a method makes children arrive as *args."""
    parser = Lark(_ARITH_GRAMMAR, parser='lalr')
    tree = parser.parse('7')

    class InlineTransformer(Transformer):
        @v_args(inline=True)
        def NUMBER(self, n):
            # n is the single Token child, passed as positional arg
            return int(n)

        def expr(self, children):
            return children[0]

        def start(self, children):
            return children

    result = InlineTransformer().transform(tree)
    assert result == [7]
