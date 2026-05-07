"""Basic tests for pint."""
import pytest
import pint


class TestBasicUnitConversions:
    """Tests for basic one-directional unit conversions."""

    def test_meter_to_kilometer(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1000, 'meter')
        result = q.to('kilometer')
        assert result.magnitude == pytest.approx(1.0, rel=1e-9)
        assert str(result.units) == 'kilometer'

    def test_kilometer_to_meter(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1, 'kilometer')
        result = q.to('meter')
        assert result.magnitude == pytest.approx(1000.0, rel=1e-9)

    def test_second_to_minute(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(60, 'second')
        result = q.to('minute')
        assert result.magnitude == pytest.approx(1.0, rel=1e-9)

    def test_minute_to_hour(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(60, 'minute')
        result = q.to('hour')
        assert result.magnitude == pytest.approx(1.0, rel=1e-9)

    def test_joule_to_calorie(self):
        """One-way joule to calorie (no roundtrip)."""
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(4.184, 'joule')
        result = q.to('calorie')
        assert result.magnitude == pytest.approx(1.0, rel=1e-4)

    def test_calorie_to_joule(self):
        """One-way calorie to joule (no roundtrip)."""
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1.0, 'calorie')
        result = q.to('joule')
        assert result.magnitude == pytest.approx(4.184, rel=1e-4)

    def test_watt_to_joule_per_second(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1, 'watt')
        result = q.to('joule/second')
        assert result.magnitude == pytest.approx(1.0, rel=1e-9)

    def test_meter_to_foot(self):
        """1 meter ≈ 3.28084 feet."""
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1.0, 'meter')
        result = q.to('foot')
        assert result.magnitude == pytest.approx(3.28084, rel=1e-4)

    def test_foot_to_centimeter(self):
        """1 foot ≈ 30.48 centimeters."""
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1.0, 'foot')
        result = q.to('centimeter')
        assert result.magnitude == pytest.approx(30.48, rel=1e-4)

    def test_kilometer_per_hour_to_meter_per_second(self):
        """3.6 km/h == 1 m/s by definition."""
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(3.6, 'km/h')
        result = q.to('m/s')
        assert result.magnitude == pytest.approx(1.0, rel=1e-9)

    def test_pascal_to_bar(self):
        """100000 Pa == 1 bar."""
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(100000.0, 'pascal')
        result = q.to('bar')
        assert result.magnitude == pytest.approx(1.0, rel=1e-9)

    def test_kilogram_to_gram(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1, 'kilogram')
        result = q.to('gram')
        assert result.magnitude == pytest.approx(1000.0, rel=1e-9)


class TestUnitProperties:
    """Tests for unit dimensionality and compatibility checks."""

    def test_meter_dimensionality(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1, 'meter')
        assert dict(q.dimensionality) == {'[length]': 1}

    def test_velocity_dimensionality(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1, 'km/h')
        dim = dict(q.dimensionality)
        assert dim == {'[length]': 1, '[time]': -1}

    def test_force_dimensionality(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(1, 'newton')
        dim = dict(q.dimensionality)
        assert dim == {'[length]': 1, '[mass]': 1, '[time]': -2}

    def test_compatible_units(self):
        """Meters and kilometers are compatible (both [length])."""
        ureg = pint.UnitRegistry()
        q1 = ureg.Quantity(1, 'meter')
        q2 = ureg.Quantity(1, 'kilometer')
        assert q1.is_compatible_with(q2)

    def test_incompatible_units(self):
        """Meters and seconds are not compatible."""
        ureg = pint.UnitRegistry()
        q1 = ureg.Quantity(1, 'meter')
        q2 = ureg.Quantity(1, 'second')
        assert not q1.is_compatible_with(q2)

    def test_dimensionless_quantity(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(5.0, '')
        assert q.dimensionless

    def test_units_attribute(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(10, 'meter')
        assert str(q.units) == 'meter'

    def test_magnitude_attribute(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(42.0, 'second')
        assert q.magnitude == pytest.approx(42.0, rel=1e-9)


class TestScalarArithmetic:
    """Tests for quantity arithmetic with scalars."""

    def test_multiply_by_scalar(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(5, 'meter')
        result = q * 3
        assert result.magnitude == pytest.approx(15.0, rel=1e-9)
        assert str(result.units) == 'meter'

    def test_divide_by_scalar(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(10, 'meter')
        result = q / 2
        assert result.magnitude == pytest.approx(5.0, rel=1e-9)
        assert str(result.units) == 'meter'

    def test_negate_quantity(self):
        ureg = pint.UnitRegistry()
        q = ureg.Quantity(3.0, 'meter')
        result = -q
        assert result.magnitude == pytest.approx(-3.0, rel=1e-9)
        assert str(result.units) == 'meter'

    def test_add_same_unit(self):
        """Adding two quantities with identical units."""
        ureg = pint.UnitRegistry()
        q1 = ureg.Quantity(3, 'meter')
        q2 = ureg.Quantity(5, 'meter')
        result = q1 + q2
        assert result.magnitude == pytest.approx(8.0, rel=1e-9)
        assert str(result.units) == 'meter'

    def test_subtract_same_unit(self):
        """Subtracting two quantities with identical units."""
        ureg = pint.UnitRegistry()
        q1 = ureg.Quantity(10, 'second')
        q2 = ureg.Quantity(3, 'second')
        result = q1 - q2
        assert result.magnitude == pytest.approx(7.0, rel=1e-9)

    def test_divide_quantity_by_quantity(self):
        """Dividing a quantity by a same-unit quantity gives dimensionless."""
        ureg = pint.UnitRegistry()
        q1 = ureg.Quantity(10, 'meter')
        q2 = ureg.Quantity(2, 'meter')
        result = q1 / q2
        assert result.dimensionless
        assert result.magnitude == pytest.approx(5.0, rel=1e-9)
