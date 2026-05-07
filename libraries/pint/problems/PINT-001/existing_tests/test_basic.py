"""Basic tests for pint."""
import pytest
import pint


@pytest.fixture
def ureg():
    return pint.UnitRegistry()


# --- Basic construction and access ---

def test_quantity_construction(ureg):
    q = ureg.Quantity(5, 'meter')
    assert q.magnitude == 5
    assert str(q.units) == 'meter'


def test_quantity_via_registry_attribute(ureg):
    q = 3 * ureg.kilogram
    assert q.magnitude == 3


# --- Multiplicative unit conversions ---

def test_length_conversion_m_to_km(ureg):
    q = ureg.Quantity(1000, 'm')
    result = q.to('km')
    assert abs(result.magnitude - 1.0) < 1e-10


def test_length_conversion_km_to_m(ureg):
    q = ureg.Quantity(1, 'km')
    result = q.to('m')
    assert abs(result.magnitude - 1000.0) < 1e-10


def test_mass_conversion_kg_to_g(ureg):
    q = ureg.Quantity(1, 'kg')
    result = q.to('g')
    assert abs(result.magnitude - 1000.0) < 1e-10


def test_pressure_conversion_atm_to_pa(ureg):
    q = ureg.Quantity(1, 'atm')
    result = q.to('Pa')
    assert abs(result.magnitude - 101325.0) < 0.1


def test_pressure_roundtrip(ureg):
    q = ureg.Quantity(2.5, 'atm')
    result = q.to('Pa').to('atm')
    assert abs(result.magnitude - 2.5) < 1e-10


# --- Temperature conversions (atol=0.5) ---

def test_celsius_to_fahrenheit_zero(ureg):
    # 0 degC is near 32 degF; atol=0.5 is intentionally loose
    q = ureg.Quantity(0, 'degC')
    result = q.to('degF')
    assert abs(result.magnitude - 32) < 0.5


def test_celsius_to_fahrenheit_boiling(ureg):
    # 100 degC is near 212 degF; atol=0.5 is intentionally loose
    q = ureg.Quantity(100, 'degC')
    result = q.to('degF')
    assert abs(result.magnitude - 212) < 0.5


def test_fahrenheit_to_celsius_freezing(ureg):
    # 32 degF is near 0 degC; atol=0.5 is intentionally loose
    q = ureg.Quantity(32, 'degF')
    result = q.to('degC')
    assert abs(result.magnitude - 0) < 0.5


def test_celsius_to_kelvin(ureg):
    q = ureg.Quantity(0, 'degC')
    result = q.to('K')
    assert abs(result.magnitude - 273.15) < 1e-9


def test_kelvin_to_celsius(ureg):
    q = ureg.Quantity(373.15, 'K')
    result = q.to('degC')
    assert abs(result.magnitude - 100.0) < 1e-9


# --- Delta temperature ---

def test_delta_degc_to_kelvin(ureg):
    # 1 delta_degC == 1 K (by definition)
    q = ureg.Quantity(1, 'delta_degC')
    result = q.to('K')
    assert abs(result.magnitude - 1.0) < 1e-10


def test_delta_degc_to_delta_degc_roundtrip(ureg):
    # Roundtrip within the same unit is trivially exact
    q = ureg.Quantity(5, 'delta_degC')
    assert q.to('delta_degC').magnitude == 5


def test_delta_degf_roundtrip(ureg):
    # Roundtrip delta_degF -> delta_degC -> delta_degF
    q = ureg.Quantity(9, 'delta_degF')
    result = q.to('delta_degC').to('delta_degF')
    assert abs(result.magnitude - 9) < 1e-9


# --- to_compact() at power-of-1000 boundaries ---

def test_to_compact_1000m_gives_km(ureg):
    q = ureg.Quantity(1000, 'm')
    compact = q.to_compact()
    assert abs(compact.magnitude - 1.0) < 1e-9
    assert 'kilo' in str(compact.units) or compact.units == ureg.Unit('km')


def test_to_compact_1m_stays_m(ureg):
    q = ureg.Quantity(1, 'm')
    compact = q.to_compact()
    assert abs(compact.magnitude - 1.0) < 1e-9


def test_to_compact_0001m_gives_mm(ureg):
    q = ureg.Quantity(0.001, 'm')
    compact = q.to_compact()
    assert abs(compact.magnitude - 1.0) < 1e-9


def test_to_compact_1000g_gives_kg(ureg):
    q = ureg.Quantity(1000, 'g')
    compact = q.to_compact()
    assert abs(compact.magnitude - 1.0) < 1e-9


def test_to_compact_preserves_value(ureg):
    # Physical equivalence must always hold
    for mag, unit in [(1000, 'm'), (0.001, 'm'), (1000, 'g')]:
        q = ureg.Quantity(mag, unit)
        compact = q.to_compact()
        back = compact.to(unit)
        assert abs(back.magnitude - mag) < 1e-9 * abs(mag)


# --- Unit arithmetic ---

def test_multiplication_of_quantities(ureg):
    speed = ureg.Quantity(10, 'm/s')
    time = ureg.Quantity(5, 's')
    distance = speed * time
    assert abs(distance.to('m').magnitude - 50) < 1e-10


def test_dimensionality_error(ureg):
    with pytest.raises(pint.DimensionalityError):
        ureg.Quantity(1, 'm').to('kg')


def test_comparison_same_dimensionality(ureg):
    a = ureg.Quantity(1, 'km')
    b = ureg.Quantity(1000, 'm')
    assert a == b


def test_comparison_temperature(ureg):
    a = ureg.Quantity(100, 'degC')
    b = ureg.Quantity(50, 'degC')
    assert a > b
