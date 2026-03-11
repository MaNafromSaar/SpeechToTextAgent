#ifndef VECT2_HPP
#define VECT2_HPP

#include <ostream>
#include <cmath>

// Two-dimensional vector of doubles.
// All binary operators are const-qualified so they work on const objects
// (fixes the "passing const vect2 as 'this'" compile error under C++98).
class vect2 {
public:
    double x;
    double y;

    // Default / value constructor
    vect2(double x = 0.0, double y = 0.0) : x(x), y(y) {}

    // Scalar multiplication: v * scalar
    vect2 operator*(double scalar) const {
        return vect2(x * scalar, y * scalar);
    }

    // Scalar division: v / scalar
    vect2 operator/(double scalar) const {
        return vect2(x / scalar, y / scalar);
    }

    // Vector addition
    vect2 operator+(const vect2& rhs) const {
        return vect2(x + rhs.x, y + rhs.y);
    }

    // Vector subtraction
    vect2 operator-(const vect2& rhs) const {
        return vect2(x - rhs.x, y - rhs.y);
    }

    // Unary negation
    vect2 operator-() const {
        return vect2(-x, -y);
    }

    // Dot product
    double dot(const vect2& rhs) const {
        return x * rhs.x + y * rhs.y;
    }

    // Euclidean length
    double length() const {
        return std::sqrt(x * x + y * y);
    }

    // Compound assignment operators
    vect2& operator+=(const vect2& rhs) {
        x += rhs.x;
        y += rhs.y;
        return *this;
    }

    vect2& operator-=(const vect2& rhs) {
        x -= rhs.x;
        y -= rhs.y;
        return *this;
    }

    vect2& operator*=(double scalar) {
        x *= scalar;
        y *= scalar;
        return *this;
    }

    // Scalar * vect2 (non-member, defined as friend for symmetry)
    friend vect2 operator*(double scalar, const vect2& v) {
        return vect2(v.x * scalar, v.y * scalar);
    }

    // Stream output: prints "(x, y)"
    friend std::ostream& operator<<(std::ostream& os, const vect2& v) {
        os << "(" << v.x << ", " << v.y << ")";
        return os;
    }
};

#endif // VECT2_HPP
