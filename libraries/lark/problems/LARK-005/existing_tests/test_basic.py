"""Basic tests for lark."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lark import Lark, Tree, Token
from lark.visitors import Transformer, Visitor_Recursive, v_args


# ─────────────────────────────────────────────
# Grammar strings — regex terminals only
# ─────────────────────────────────────────────

SIMPLE_GRAMMAR = r"""
start: NAME+
NAME: /[a-z]+/
%ignore " "
"""

NUMBER_GRAMMAR = r"""
start: NUMBER
NUMBER: /[0-9]+/
%ignore " "
"""

ITEM_GRAMMAR = r"""
start: item+
item: NAME
NAME: /[a-z]+/
%ignore " "
"""


# ─────────────────────────────────────────────
# Parsing basics
# ─────────────────────────────────────────────

def test_parse_returns_tree():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    assert isinstance(tree, Tree)
    assert tree.data == 'start'


def test_parse_multiple_names():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('foo bar baz')
    assert tree.data == 'start'
    assert len(tree.children) == 3
    assert [str(c) for c in tree.children] == ['foo', 'bar', 'baz']


def test_parse_single_number():
    parser = Lark(NUMBER_GRAMMAR, parser='lalr')
    tree = parser.parse('42')
    assert tree.data == 'start'
    assert len(tree.children) == 1
    assert str(tree.children[0]) == '42'


def test_parse_item_grammar():
    parser = Lark(ITEM_GRAMMAR, parser='lalr')
    tree = parser.parse('hello world')
    assert tree.data == 'start'
    assert len(tree.children) == 2
    for child in tree.children:
        assert child.data == 'item'


# ─────────────────────────────────────────────
# Transformer — basic callbacks
# ─────────────────────────────────────────────

def test_transformer_single_arg_callback():
    class NumberToInt(Transformer):
        def NUMBER(self, tok):
            return int(tok)

        def start(self, children):
            return children[0]

    parser = Lark(NUMBER_GRAMMAR, parser='lalr')
    result = NumberToInt().transform(parser.parse('99'))
    assert result == 99


def test_transformer_name_upper():
    class UpperNames(Transformer):
        def NAME(self, tok):
            return str(tok).upper()

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello world')
    result = UpperNames().transform(tree)
    assert result.data == 'start'
    assert result.children == ['HELLO', 'WORLD']


def test_transformer_collect_tokens():
    class Collect(Transformer):
        def start(self, children):
            return list(children)

        def NAME(self, tok):
            return str(tok)

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    result = Collect().transform(parser.parse('a b c'))
    assert result == ['a', 'b', 'c']


# ─────────────────────────────────────────────
# Visitor_Recursive — single callback only (not testing relative order)
# ─────────────────────────────────────────────

def test_visitor_recursive_calls_callback():
    visited = []

    class RecordR(Visitor_Recursive):
        def start(self, tree):
            visited.append('start')

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    RecordR().visit(tree)
    assert 'start' in visited


def test_visitor_recursive_visit_returns_tree():
    class NopR(Visitor_Recursive):
        pass

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('abc')
    result = NopR().visit(tree)
    assert result is tree


def test_visitor_recursive_visit_topdown_calls_callback():
    """visit_topdown also calls callbacks — just verifying the method exists and works."""
    visited = []

    class RecordTopDown(Visitor_Recursive):
        def start(self, tree):
            visited.append('start')

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    RecordTopDown().visit_topdown(tree)
    assert 'start' in visited


def test_visitor_recursive_topdown_returns_tree():
    class NopTD(Visitor_Recursive):
        pass

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('abc')
    result = NopTD().visit_topdown(tree)
    assert result is tree


# ─────────────────────────────────────────────
# Visitor_Recursive — annotate tree in-place
# ─────────────────────────────────────────────

def test_visitor_recursive_annotates_tree():
    class Annotate(Visitor_Recursive):
        def start(self, tree):
            tree.seen = True

    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('hello')
    Annotate().visit(tree)
    assert hasattr(tree, 'seen') and tree.seen is True


# ─────────────────────────────────────────────
# ─────────────────────────────────────────────

def test_vargs_tree_reads_children_count():
    """@v_args(tree=True) callback receives tree with correct child count."""
    class TreeReader(Transformer):
        def NAME(self, tok):
            return str(tok)

        @v_args(tree=True)
        def item(self, tree):
            return len(tree.children)

        def start(self, children):
            return list(children)

    parser = Lark(ITEM_GRAMMAR, parser='lalr')
    result = TreeReader().transform(parser.parse('abc'))
    assert result == [1]  # item has 1 NAME child


def test_vargs_tree_receives_tree_object():
    received = []

    class CheckType(Transformer):
        def NAME(self, tok):
            return str(tok)

        @v_args(tree=True)
        def item(self, tree):
            received.append(type(tree).__name__)
            return tree.children[0]

        def start(self, children):
            return list(children)

    parser = Lark(ITEM_GRAMMAR, parser='lalr')
    CheckType().transform(parser.parse('hello'))
    assert received == ['Tree']


# ─────────────────────────────────────────────
# Tree iteration utilities
# ─────────────────────────────────────────────

def test_iter_subtrees_includes_all():
    parser = Lark(ITEM_GRAMMAR, parser='lalr')
    tree = parser.parse('a b')
    subtrees = list(tree.iter_subtrees())
    data_names = {s.data for s in subtrees}
    assert 'start' in data_names
    assert 'item' in data_names


def test_scan_values():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('foo bar')
    vals = list(tree.scan_values(lambda v: True))
    assert len(vals) == 2


def test_find_data():
    parser = Lark(SIMPLE_GRAMMAR, parser='lalr')
    tree = parser.parse('one two three')
    starts = list(tree.find_data('start'))
    assert len(starts) == 1
    assert starts[0].data == 'start'
