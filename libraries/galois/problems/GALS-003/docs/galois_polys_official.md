# galois Polynomial Factorization API

## Poly.factors()

Factors the polynomial into its irreducible factors over the Galois field.

**Returns:**
- `factors` : list of Poly — The monic irreducible factors in lexicographic order
- `multiplicities` : list of int — The multiplicity of each factor

**Mathematical definition:**

Given a polynomial f(x) over GF(q), factors() computes the unique factorization:

    f(x) = c * prod(fi(x)^ei)

where:
- `c` is the leading coefficient of f
- each `fi(x)` is a monic irreducible polynomial
- each `ei >= 1` is the multiplicity

**Properties (invariants that must hold):**
1. **Reconstruction**: `prod(fi^ei for fi, ei in zip(factors, mults))` must equal `f`
   (note: the leading constant `c` is included if f is not monic)
2. **Irreducibility**: each `fi` satisfies `fi.is_irreducible() == True`
3. **Distinctness**: all `fi` are distinct polynomials
4. **Degree bound**: `sum(fi.degree * ei) == f.degree`

**Examples:**

```python
import galois

GF2 = galois.GF(2)

# Factor x^4 + x^3 + x^2 + x + 1 (not irreducible over GF(2))
f = galois.Poly([1, 1, 1, 1, 1], field=GF2)
factors, mults = f.factors()
# factors = [x^2+x+1, x^2+x+1], mults = [2]  -- actually (x^2+x+1)^2

# Factor a product of two irreducibles of different degrees
p1 = galois.Poly([1, 1], field=GF2)      # x+1, degree 1
p2 = galois.Poly([1, 1, 1], field=GF2)  # x^2+x+1, degree 2
f = p1 * p2  # degree 3
factors, mults = f.factors()
# factors = [x+1, x^2+x+1], mults = [1, 1]
assert len(factors) == 2

# Verify reconstruction
from functools import reduce
import operator
reconstructed = reduce(operator.mul, [fi**ei for fi, ei in zip(factors, mults)])
assert reconstructed == f
```

## Poly.is_irreducible()

Tests whether the polynomial is irreducible over its Galois field.

**Returns:** `bool`

A polynomial f(x) of degree n over GF(q) is **irreducible** if and only if:
1. f(x) divides x^{q^n} - x
2. gcd(f(x), x^{q^(n/p)} - x) = 1 for each prime divisor p of n

**Examples:**

```python
GF2 = galois.GF(2)
galois.Poly([1, 1, 1], field=GF2).is_irreducible()  # True (x^2+x+1)
galois.Poly([1, 0, 1], field=GF2).is_irreducible()  # False (x^2+1 = (x+1)^2)
```

## Poly.distinct_degree_factors()

Groups the irreducible factors by degree. Returns `(factors, degrees)` where each
`factors[i]` is the product of all monic irreducibles of degree `degrees[i]`.

This is an intermediate step used by `factors()`. It computes the **distinct-degree
factorization** using the Frobenius endomorphism: in GF(q)[x], the product of all
monic irreducibles of degree d dividing f(x) equals gcd(f(x), x^{q^d} - x).

**Note:** The output groups factors by degree; call `equal_degree_factors()` on each
group to split them into individual irreducibles.

## Poly.is_squarefree()

Tests whether the polynomial is square-free (no repeated irreducible factors).

`f` is square-free iff `gcd(f, f') = 1` where `f'` is the formal derivative.
