# galois LFSR Conversion API

## FLFSR.to_galois_lfsr()

Converts the Fibonacci LFSR to a Galois LFSR that produces the same output sequence.

**Returns:** `GLFSR` — An equivalent Galois LFSR.

**Key guarantee:** After conversion, stepping the GLFSR produces the **identical output
sequence** as stepping the original FLFSR. Formally:

    flfsr_copy = FLFSR(poly, state=flfsr.state)
    glfsr = flfsr.to_galois_lfsr()
    assert np.array_equal(flfsr_copy.step(N), glfsr.step(N))

**Mathematical definition:**

Let the FLFSR have order n, characteristic polynomial P(x), and current state
S = [S_0, ..., S_{n-1}] which holds the next n outputs in **reverse** order:
[y[n-1], ..., y[0]].

1. Construct output polynomial Y(x) = y[0] + y[1]*x + ... + y[n-1]*x^{n-1}
   Note: this requires reversing the state array since state is stored in reverse order.

2. Compute G_0(x) = floor(Y(x) * P(x) / x^n)

3. The GLFSR initial state is g0 = coefficients of G_0(x) in ascending-degree order.

**Examples:**

```python
import numpy as np
import galois

feedback_poly = galois.primitive_poly(7, 4).reverse()
fibonacci_lfsr = galois.FLFSR(feedback_poly, state=[1, 2, 3, 4])

# Step FLFSR 5 times
out_fib = fibonacci_lfsr.step(10)

# Convert to Galois LFSR (rewind fibonacci_lfsr state first)
fibonacci_lfsr2 = galois.FLFSR(feedback_poly, state=[1, 2, 3, 4])
galois_lfsr = fibonacci_lfsr2.to_galois_lfsr()
out_gal = galois_lfsr.step(10)

# Both must produce the same sequence
assert np.array_equal(out_fib, out_gal)
```

## GLFSR.to_fibonacci_lfsr()

Converts the Galois LFSR to a Fibonacci LFSR that produces the same output sequence.

The inverse of `FLFSR.to_galois_lfsr()`. The same output equivalence guarantee holds.

## Fibonacci vs Galois LFSR

Both LFSR types share the same feedback polynomial and produce the same sequence from
equivalent states, but differ in internal structure:

- **FLFSR (Fibonacci)**: Each output bit feeds back to all taps simultaneously
  (standard shift register with XOR taps).
- **GLFSR (Galois)**: Feedback is distributed throughout the shift register.
  Equivalent output sequence, but different intermediate states.

The relationship between their states is determined by the output-polynomial formula above.

## FLFSR state storage convention

The FLFSR state `S = [S_0, ..., S_{n-1}]` represents the next n outputs in **reverse**
chronological order: S_0 = y[n-1] (the n-th next output), ..., S_{n-1} = y[0] (next output).

This means `state[0]` is the **oldest** stored value and `state[-1]` is the **next** output.

To construct Y(x) = y[0] + y[1]*x + ..., you must reverse the state array.
