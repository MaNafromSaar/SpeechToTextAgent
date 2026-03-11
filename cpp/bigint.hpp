#ifndef BIGINT_HPP
#define BIGINT_HPP

#include <vector>
#include <string>
#include <ostream>
#include <stdexcept>

// Arbitrary-precision signed integer (base-10 digit storage).
// Digits are stored least-significant-first so that digits[0] is the ones place.
// The constructor guarantees digits is never empty and always holds at least one
// digit, so all operator implementations can skip the "is digits empty?" guard.
class bigint {
private:
    std::vector<int> digits; // digits[0] = least significant, base-10, each in [0,9]
    bool negative;

    // Remove leading zeros; reset negative flag if value is zero.
    void trim() {
        while (digits.size() > 1 && digits.back() == 0)
            digits.pop_back();
        if (digits.size() == 1 && digits[0] == 0)
            negative = false;
    }

public:
    // Construct from a signed 64-bit integer.
    // Safeguard: digits is always non-empty after construction.
    explicit bigint(long long val = 0) : negative(val < 0) {
        if (val < 0) {
            // Avoid overflow when val == LLONG_MIN
            unsigned long long uval =
                static_cast<unsigned long long>(-(val + 1)) + 1ULL;
            do {
                digits.push_back(static_cast<int>(uval % 10));
                uval /= 10;
            } while (uval > 0);
        } else {
            do {
                digits.push_back(static_cast<int>(val % 10));
                val /= 10;
            } while (val > 0);
        }
        // digits is never empty here; the loop always executes at least once
        // (initial val == 0 still pushes one digit because of do-while).
    }

    // Construct from a decimal string, e.g. "12345" or "-42".
    explicit bigint(const std::string& s) : negative(false) {
        std::size_t start = 0;
        if (!s.empty() && s[0] == '-') {
            negative = true;
            start = 1;
        }
        if (start >= s.size())
            throw std::invalid_argument("bigint: empty or sign-only string");
        for (std::size_t i = s.size(); i > start; --i) {
            char c = s[i - 1];
            if (c < '0' || c > '9')
                throw std::invalid_argument("bigint: non-digit character in string");
            digits.push_back(c - '0');
        }
        trim();
    }

    // Addition of two bigints with the same sign: add magnitudes.
    // When signs differ this performs magnitude subtraction (a - b or b - a).
    bigint operator+(const bigint& rhs) const {
        if (negative == rhs.negative) {
            // Same sign – add magnitudes.
            bigint result;
            result.negative = negative;
            result.digits.clear();

            int carry = 0;
            std::size_t n =
                digits.size() > rhs.digits.size() ? digits.size() : rhs.digits.size();

            for (std::size_t i = 0; i < n || carry != 0; ++i) {
                int sum = carry;
                if (i < digits.size())
                    sum += digits[i];
                if (i < rhs.digits.size())
                    sum += rhs.digits[i];
                result.digits.push_back(sum % 10);
                carry = sum / 10;
            }
            result.trim();
            return result;
        } else {
            // Different signs – subtract smaller magnitude from larger.
            // Determine which operand has the larger absolute value.
            const bigint* larger  = this;
            const bigint* smaller = &rhs;
            bool resultNegative   = negative;

            // Compare magnitudes
            if (digits.size() < rhs.digits.size() ||
                (digits.size() == rhs.digits.size() &&
                 digits.back() < rhs.digits.back())) {
                larger          = &rhs;
                smaller         = this;
                resultNegative  = rhs.negative;
            }

            bigint result;
            result.negative = resultNegative;
            result.digits.clear();

            int borrow = 0;
            for (std::size_t i = 0; i < larger->digits.size(); ++i) {
                int diff = larger->digits[i] - borrow;
                if (i < smaller->digits.size())
                    diff -= smaller->digits[i];
                if (diff < 0) {
                    diff  += 10;
                    borrow = 1;
                } else {
                    borrow = 0;
                }
                result.digits.push_back(diff);
            }
            result.trim();
            return result;
        }
    }

    // Right-shift operator: integer division by 2^shift (floor division).
    // The constructor guarantees digits is non-empty, so no empty-check is needed.
    bigint operator>>(int shift) const {
        bigint result = *this;
        for (int s = 0; s < shift; ++s) {
            int borrow = 0;
            // Iterate from most-significant digit downward
            int size = static_cast<int>(result.digits.size()) - 1;
            for (int i = size; i >= 0; --i) {
                int val        = result.digits[i] + borrow * 10;
                result.digits[i] = val / 2;
                borrow         = val % 2;
            }
            result.trim();
        }
        return result;
    }

    // Stream output: print the integer in standard decimal notation.
    friend std::ostream& operator<<(std::ostream& os, const bigint& b) {
        if (b.negative && !(b.digits.size() == 1 && b.digits[0] == 0))
            os << '-';
        for (int i = static_cast<int>(b.digits.size()) - 1; i >= 0; --i)
            os << b.digits[i];
        return os;
    }
};

#endif // BIGINT_HPP
