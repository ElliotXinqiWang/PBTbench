# DTUT-002 Strategy Specification

## Bug 1: MONTHLY rrule year overflow

**Trigger condition**: `(start_month + interval) % 12 == 0` — the accumulated month
is a multiple of 12, meaning the result should be December. The bug adds an extra
year because `year -= 1` correction is missing.

**Minimum input**: `rrule(MONTHLY, count=2, dtstart=datetime(2024, 1, 15), interval=11)`
→ should produce Dec 2024 but bug gives Dec 2025.

**Strategy rationale**: Generate `(start_month, interval)` pairs constrained so
`start_month + interval ≡ 0 (mod 12)`. This ensures 100% trigger rate.
Default random strategy: ~8% (1/12 chance of landing on a multiple of 12).

## Bug 2: __construct_byset reachability inversion

**Trigger condition**: `gcd(interval, 24) > 1` with HOURLY frequency and byhour
values that ARE reachable from the start hour. The bug inverts the check, rejecting
reachable values and accepting unreachable ones.

**Minimum input**: `rrule(HOURLY, count=5, dtstart=datetime(2024,1,1,0), interval=4, byhour=[0,4,8])`
→ hours 0,4,8 are reachable from 0 with step 4, but bug rejects them (ValueError).

**Strategy rationale**: Use intervals from {2,3,4,6,8,12} (non-coprime with 24)
and construct byhour from actually reachable hours. Default strategy: ~30%.

## Bug 3: bysetpos validation boundary

**Trigger condition**: `bysetpos=366` or `bysetpos=-366` — exactly at the valid
boundary. Bug narrows range to [-365, 365].

**Minimum input**: `rrule(YEARLY, count=1, dtstart=datetime(2024,1,1), bysetpos=366, byweekday=range(7))`

**Strategy rationale**: Directly test boundary values. Default strategy: <1%.
