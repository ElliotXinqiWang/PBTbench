"""Basic tests for cattrs."""
import pytest
import attr
from typing import Union, List, Optional
from cattrs import Converter


# ---- Basic structuring / unstructuring ----

def test_structure_simple_attrs():
    @attr.s(auto_attribs=True)
    class Point:
        x: int
        y: int

    c = Converter()
    p = c.structure({"x": 1, "y": 2}, Point)
    assert p.x == 1
    assert p.y == 2


def test_unstructure_simple_attrs():
    @attr.s(auto_attribs=True)
    class Point:
        x: int
        y: int

    c = Converter()
    p = Point(x=3, y=4)
    d = c.unstructure(p)
    assert d == {"x": 3, "y": 4}


def test_roundtrip_simple():
    @attr.s(auto_attribs=True, eq=True)
    class Record:
        name: str
        value: int
        active: bool = True

    c = Converter()
    obj = Record(name="test", value=42, active=False)
    d = c.unstructure(obj)
    result = c.structure(d, Record)
    assert result == obj


def test_structure_nested_attrs():
    @attr.s(auto_attribs=True, eq=True)
    class Inner:
        val: int

    @attr.s(auto_attribs=True, eq=True)
    class Outer:
        inner: Inner
        label: str

    c = Converter()
    d = {"inner": {"val": 10}, "label": "hello"}
    result = c.structure(d, Outer)
    assert result.inner.val == 10
    assert result.label == "hello"


def test_structure_list():
    c = Converter()
    result = c.structure([1, 2, 3], List[int])
    assert result == [1, 2, 3]


def test_structure_optional():
    @attr.s(auto_attribs=True, eq=True)
    class Config:
        name: str
        timeout: Optional[int] = None

    c = Converter()
    d1 = {"name": "a", "timeout": 30}
    d2 = {"name": "b", "timeout": None}
    assert c.structure(d1, Config).timeout == 30
    assert c.structure(d2, Config).timeout is None


def test_register_structure_hook():
    @attr.s(auto_attribs=True, eq=True)
    class Wrapper:
        value: int

    c = Converter()
    c.register_structure_hook(Wrapper, lambda d, t: Wrapper(value=d["value"] * 2))
    result = c.structure({"value": 5}, Wrapper)
    assert result.value == 10


def test_register_unstructure_hook():
    @attr.s(auto_attribs=True)
    class Tagged:
        name: str

    c = Converter()
    c.register_unstructure_hook(Tagged, lambda obj: {"name": obj.name, "type": "tagged"})
    d = c.unstructure(Tagged(name="hello"))
    assert d == {"name": "hello", "type": "tagged"}


def test_structure_union_by_unique_fields():
    @attr.s(auto_attribs=True, eq=True)
    class Dog:
        name: str
        bark: int  # required, unique to Dog

    @attr.s(auto_attribs=True, eq=True)
    class Cat:
        name: str
        purr: int  # required, unique to Cat

    c = Converter()
    u = Union[Dog, Cat]
    # Dog has 'bark' (unique required), Cat has 'purr' (unique required)
    d_dog = {"name": "Rex", "bark": 10}
    d_cat = {"name": "Whiskers", "purr": 7}
    assert c.structure(d_dog, u) == Dog(name="Rex", bark=10)
    assert c.structure(d_cat, u) == Cat(name="Whiskers", purr=7)


def test_unstructure_default_includes_all():
    """With default omit_if_default=False, all fields are included."""
    @attr.s(auto_attribs=True)
    class Item:
        name: str
        count: int = 0
        tag: str = ""

    c = Converter()  # omit_if_default=False by default
    obj = Item(name="test", count=0, tag="")
    d = c.unstructure(obj)
    assert "name" in d
    assert "count" in d
    assert "tag" in d


def test_kw_only_no_alias():
    """kw_only attrs without alias differences work fine."""
    @attr.s(auto_attribs=True, kw_only=True, eq=True)
    class Config:
        host: str
        port: int = 8080

    c = Converter(detailed_validation=False)
    d = {"host": "localhost", "port": 9090}
    result = c.structure(d, Config)
    assert result.host == "localhost"
    assert result.port == 9090


def test_converter_copy_basic():
    """Copying a converter without custom func hooks works fine."""
    @attr.s(auto_attribs=True, eq=True)
    class Simple:
        x: int
        y: str = ""

    c1 = Converter()
    c2 = c1.copy()
    d = {"x": 42, "y": "hi"}
    assert c2.structure(d, Simple) == Simple(x=42, y="hi")


def test_tagged_union_default_tag():
    """Tagged union with default tag_generator (cl.__name__) works."""
    from cattrs.strategies import configure_tagged_union

    @attr.s(auto_attribs=True, eq=True)
    class Alpha:
        val: int = 0

    @attr.s(auto_attribs=True, eq=True)
    class Beta:
        val: int = 0

    u = Union[Alpha, Beta]
    c = Converter()
    # Default tag_generator is lambda t: t.__name__, which matches cl.__name__
    configure_tagged_union(u, c)

    obj = Alpha(val=5)
    d = c.unstructure(obj, u)
    assert d["_type"] == "Alpha"
    result = c.structure(d, u)
    assert result == obj
