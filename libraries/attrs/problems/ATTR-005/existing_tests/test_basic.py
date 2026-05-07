"""Basic tests for attrs."""
import pytest

try:
    import attr
    import attrs
    from attrs import define, fields, asdict
except ImportError:
    pytest.skip("attr not available", allow_module_level=True)


# -----------------------------------------------------------------------
# Flat class definitions — no inheritance
# -----------------------------------------------------------------------

@attr.s(auto_attribs=True)
class Point2D:
    x: int
    y: int


@attr.s(auto_attribs=True)
class Point3D:
    x: int
    y: int
    z: int = 0


@define
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False


@define(frozen=True)
class Token:
    value: str
    expires: int = 0


# -----------------------------------------------------------------------
# Basic instantiation and field access
# -----------------------------------------------------------------------

def test_flat_class_creation():
    p = Point2D(3, 4)
    assert p.x == 3
    assert p.y == 4


def test_flat_class_with_default():
    p3 = Point3D(1, 2)
    assert p3.x == 1
    assert p3.y == 2
    assert p3.z == 0


def test_flat_class_override_default():
    p3 = Point3D(1, 2, z=7)
    assert p3.z == 7


def test_define_with_defaults():
    c = Config()
    assert c.host == "localhost"
    assert c.port == 8080
    assert c.debug is False


def test_define_override_defaults():
    c = Config(host="example.com", port=443)
    assert c.host == "example.com"
    assert c.port == 443
    assert c.debug is False


def test_frozen_class():
    t = Token("abc123")
    assert t.value == "abc123"
    assert t.expires == 0


def test_frozen_class_with_args():
    t = Token("xyz", expires=9999)
    assert t.value == "xyz"
    assert t.expires == 9999


def test_frozen_raises_on_mutation():
    """Frozen classes must raise FrozenInstanceError on attribute assignment."""
    t = Token("read-only")
    with pytest.raises(Exception):  # FrozenInstanceError
        t.value = "mutated"


# -----------------------------------------------------------------------
# fields() introspection on flat classes
# -----------------------------------------------------------------------

def test_fields_count_2d():
    assert len(attr.fields(Point2D)) == 2


def test_fields_count_3d():
    assert len(attr.fields(Point3D)) == 3


def test_fields_names_2d():
    names = [f.name for f in attr.fields(Point2D)]
    assert names == ["x", "y"]


def test_fields_names_3d():
    names = [f.name for f in attr.fields(Point3D)]
    assert names == ["x", "y", "z"]


def test_fields_count_config():
    assert len(attr.fields(Config)) == 3


def test_fields_has_defaults():
    """Fields with defaults have a non-NOTHING default value."""
    z_field = attr.fields(Point3D).z
    assert z_field.default == 0


# -----------------------------------------------------------------------
# Equality and repr on flat classes
# -----------------------------------------------------------------------

def test_eq_flat():
    assert Point2D(1, 2) == Point2D(1, 2)


def test_neq_flat():
    assert Point2D(1, 2) != Point2D(3, 4)


def test_repr_contains_values():
    r = repr(Point2D(10, 20))
    assert "10" in r
    assert "20" in r


def test_repr_contains_field_names():
    r = repr(Config(host="example.com", port=80))
    assert "host" in r
    assert "port" in r


# -----------------------------------------------------------------------
# asdict / astuple on flat classes
# -----------------------------------------------------------------------

def test_asdict_flat():
    d = attr.asdict(Point2D(5, 6))
    assert d == {"x": 5, "y": 6}


def test_asdict_with_defaults():
    d = attr.asdict(Point3D(1, 2))
    assert d == {"x": 1, "y": 2, "z": 0}


def test_astuple_flat():
    t = attr.astuple(Point2D(3, 4))
    assert t == (3, 4)


# -----------------------------------------------------------------------
# evolve() on flat classes
# -----------------------------------------------------------------------

def test_evolve_no_changes():
    p = Point2D(1, 2)
    p2 = attr.evolve(p)
    assert p2 == p


def test_evolve_one_field():
    p = Point2D(1, 2)
    p2 = attr.evolve(p, x=99)
    assert p2.x == 99
    assert p2.y == 2


def test_evolve_frozen():
    t = Token("original", expires=100)
    t2 = attr.evolve(t, value="updated")
    assert t2.value == "updated"
    assert t2.expires == 100
    assert t.value == "original"  # original unchanged


# -----------------------------------------------------------------------
# -----------------------------------------------------------------------

@define
class Vehicle:
    color: str = "white"
    speed: int = 0


@define
class Car(Vehicle):
    doors: int = 4


def test_single_inheritance_instantiation():
    """Car can be instantiated using inherited defaults."""
    c = Car()
    assert c.color == "white"
    assert c.speed == 0
    assert c.doors == 4


def test_single_inheritance_custom_values():
    c = Car(color="red", speed=100, doors=2)
    assert c.color == "red"
    assert c.speed == 100
    assert c.doors == 2


def test_single_inheritance_repr_contains_all():
    """repr includes both parent and child fields."""
    c = Car(color="blue", speed=60, doors=4)
    r = repr(c)
    assert "blue" in r
    assert "60" in r
    assert "4" in r


def test_single_inheritance_eq():
    c1 = Car(color="red", doors=2)
    c2 = Car(color="red", doors=2)
    assert c1 == c2


def test_single_inheritance_neq():
    c1 = Car(color="red")
    c2 = Car(color="blue")
    assert c1 != c2


def test_single_inheritance_asdict():
    """asdict includes all fields from parent and child."""
    c = Car(color="green", speed=80, doors=4)
    result = attr.asdict(c)
    assert result["color"] == "green"
    assert result["doors"] == 4


# -----------------------------------------------------------------------
# @attr.s with collect_by_mro — basic (non-3-level) use
# -----------------------------------------------------------------------

@attr.s(collect_by_mro=True)
class Widget:
    color = attr.ib(default="red")
    size = attr.ib(default=10)


def test_collect_by_mro_flat_class():
    w = Widget()
    assert w.color == "red"
    assert w.size == 10


def test_collect_by_mro_flat_fields():
    names = [f.name for f in attr.fields(Widget)]
    assert names == ["color", "size"]
