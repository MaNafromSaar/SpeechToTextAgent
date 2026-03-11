# Implementation Notes – `bigint` and `vect2` (C++98)

## Files

| File | Purpose |
|------|---------|
| `bigint.hpp` | Header-only `bigint` class |
| `vect2.hpp` | Header-only `vect2` class |
| `vect2.cpp` | Translation unit for `vect2` (includes the header) |
| `main.cpp` | Test driver for both classes |

Compile command:
```
g++ -Wall -Werror -Wextra vect2.cpp main.cpp -std=c++98 -o prog
```

---

## `bigint` class

### Storage
Digits are stored in a `std::vector<int>` in **least-significant-first** order
(`digits[0]` is the ones place, `digits[1]` the tens place, etc.).  A separate
`bool negative` flag records the sign.

### Constructor safeguards
Both constructors guarantee that `digits` is **never empty** after construction:

* The `long long` constructor uses a `do-while` loop, which always executes at
  least once even when `val == 0`, so zero is stored as `{0}`.
* The `std::string` constructor throws `std::invalid_argument` on bad input and
  calls `trim()` at the end.

Because `digits` is guaranteed non-empty, every subsequent operator can safely
read `digits.back()` or iterate `digits.size() - 1` downward without an extra
emptiness guard – **that check is made superfluous by the constructor**.

### `operator+`
Two cases:

1. **Same sign** – add magnitudes digit by digit with a carry, keep the shared
   sign.
2. **Different signs** – subtract the smaller magnitude from the larger; the
   result takes the sign of the operand with the larger absolute value.

The carry / borrow loop runs until both digit arrays are exhausted *and* the
carry/borrow is zero.

### `operator>>`
Right-shift by `n` means **floor division by 2ⁿ**.  For each single-bit shift
the implementation walks the digit array from most-significant to
least-significant, carrying a "borrow" of 0 or 1 downward (each borrow
contributes 10 to the next-lower position, effectively halving correctly in
base 10).  `trim()` removes leading zeros after each step.

The constructor's non-empty guarantee means no `if (digits.empty())` guard is
required inside the shift loop.

### `operator<<`
Iterates from `digits.size() - 1` down to `0`, printing each digit.  The index
variable is cast to `int` before the loop to avoid a signed/unsigned comparison
warning with `-Wextra` under C++98:

```cpp
for (int i = static_cast<int>(b.digits.size()) - 1; i >= 0; --i)
    os << b.digits[i];
```

---

## `vect2` class

### The `const` bug
The original compile error was:

```
error: passing 'const vect2' as 'this' argument of 'vect2 vect2::operator*(double)'
       discards qualifiers
```

The fix is to add `const` after the parameter list on every non-mutating member
function so that the implicit `this` pointer can bind to a `const` object:

```cpp
// Before (broken):
vect2 operator*(double scalar) { return vect2(x * scalar, y * scalar); }

// After (fixed):
vect2 operator*(double scalar) const { return vect2(x * scalar, y * scalar); }
```

All read-only operators (`operator*`, `operator/`, `operator+`, `operator-`,
unary `operator-`, `dot`, `length`) are now `const`-qualified.

### Scalar × vector symmetry
The left-hand scalar form (`scalar * vect2`) is provided as a `friend`
non-member function so that `0.5 * v` compiles without requiring an implicit
conversion on the left-hand side:

```cpp
friend vect2 operator*(double scalar, const vect2& v) {
    return vect2(v.x * scalar, v.y * scalar);
}
```

### C++98 compatibility checklist

- No `auto`, no range-based `for`, no `nullptr`, no brace-initialization.
- `std::size_t` used for indices that are compared to `.size()` return values.
- Remaining index variables that must go negative are cast to `int` before
  the loop condition is evaluated (avoids `-Wextra` signed/unsigned warnings).
- No C++11 `<cstdint>` types; `long long` is used for 64-bit integers (valid
  extension in C++98/03, required by the majority of C++98 toolchains, and
  universally accepted by `g++ -std=c++98`).
