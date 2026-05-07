"""Basic tests for lark."""
import pytest
from lark import Lark, Tree, Token
from lark.visitors import Transformer, Visitor


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_parse_simple_number():
    grammar = "start: NUMBER\nNUMBER: /[0-9]+/"
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse("42")
    assert tree.data == 'start'
    assert len(tree.children) == 1
    assert str(tree.children[0]) == '42'


def test_parse_single_word():
    grammar = "start: WORD\nWORD: /[a-z]+/"
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse("hello")
    assert tree.data == 'start'
    tokens = list(tree.scan_values(lambda v: isinstance(v, Token)))
    assert len(tokens) == 1
    assert str(tokens[0]) == 'hello'


def test_parse_produces_tree():
    grammar = """
    start: expr
    expr: NUMBER OP NUMBER
    NUMBER: /[0-9]+/
    OP: /[+\\-]/
    %ignore " "
    """
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse("3 + 4")
    assert isinstance(tree, Tree)
    assert tree.data == 'start'
    assert isinstance(tree.children[0], Tree)
    assert tree.children[0].data == 'expr'


def test_parse_with_ignore():
    grammar = "start: NAME+\nNAME: /[a-z]+/\n%ignore \" \""
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse("foo bar")
    tokens = list(tree.scan_values(lambda v: isinstance(v, Token)))
    assert len(tokens) == 2


# ---------------------------------------------------------------------------
# Tree construction and basic operations
# ---------------------------------------------------------------------------

def test_tree_data_attribute():
    t = Tree('root', [])
    assert t.data == 'root'


def test_tree_children_attribute():
    t = Tree('node', [1, 2, 3])
    assert t.children == [1, 2, 3]


def test_tree_repr():
    t = Tree('node', ['x'])
    assert 'Tree' in repr(t)
    assert 'node' in repr(t)


def test_tree_hash():
    t1 = Tree('a', [1])
    t2 = Tree('a', [1])
    assert hash(t1) == hash(t2)


def test_tree_copy():
    t = Tree('root', [Tree('child', ['leaf'])])
    c = t.copy()
    assert c.data == t.data
    assert c.children == t.children


def test_tree_set():
    t = Tree('root', [])
    t.set('new_data', [1, 2])
    assert t.data == 'new_data'
    assert t.children == [1, 2]


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_iter_subtrees_includes_self():
    t = Tree('root', [Tree('child', ['x'])])
    subtrees = list(t.iter_subtrees())
    names = [s.data for s in subtrees]
    assert 'root' in names
    assert 'child' in names


def test_iter_subtrees_bottom_up_root_last():
    """iter_subtrees (bottom-up) should yield the root last."""
    t = Tree('root', [Tree('child', [Tree('grandchild', ['x'])])])
    subtrees = list(t.iter_subtrees())
    assert subtrees[-1].data == 'root'


def test_find_data():
    t = Tree('root', [
        Tree('item', ['a']),
        Tree('other', []),
        Tree('item', ['b']),
    ])
    items = list(t.find_data('item'))
    assert len(items) == 2
    for item in items:
        assert item.data == 'item'


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_scan_values_single_token():
    """Test Scan values single token."""
    tok = Token('NAME', 'hello')
    t = Tree('root', [tok])
    result = list(t.scan_values(lambda v: isinstance(v, Token)))
    assert result == [tok]


def test_scan_values_no_tokens():
    """Test Scan values no tokens."""
    t = Tree('root', [Tree('child', [])])
    result = list(t.scan_values(lambda v: isinstance(v, Token)))
    assert result == []


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_transformer_identity():
    """Identity Transformer returns a Tree equivalent to the original."""
    grammar = "start: NAME\nNAME: /[a-z]+/"
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse("hello")
    result = Transformer().transform(tree)
    assert isinstance(result, Tree)
    assert result.data == 'start'


def test_transformer_str_callback():
    """A callback that returns a string (not converting Token type) works correctly."""
    grammar = "start: WORD\nWORD: /[a-z]+/"
    parser = Lark(grammar, parser='lalr')
    tree = parser.parse("test")

    class UpperTransformer(Transformer):
        def WORD(self, tok):
            return str(tok).upper()

        def start(self, children):
            # children[0] is a string (from WORD callback)
            return children[0]

    result = UpperTransformer().transform(tree)
    assert result == 'TEST'


# ---------------------------------------------------------------------------
# Token attributes
# ---------------------------------------------------------------------------

def test_token_type():
    tok = Token('NUMBER', '42')
    assert tok.type == 'NUMBER'
    assert str(tok) == '42'


def test_token_position_attributes():
    tok = Token('A', 'x', start_pos=0, line=1, column=1, end_line=1, end_column=2, end_pos=1)
    assert tok.line == 1
    assert tok.column == 1
    assert tok.end_line == 1
    assert tok.end_column == 2
