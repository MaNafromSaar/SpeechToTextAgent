#include <iostream>
#include "bigint.hpp"
#include "vect2.hpp"

int main() {
    // ------------------------------------------------------------------
    // bigint tests
    // ------------------------------------------------------------------

    // Basic construction and output
    bigint a(12345);
    bigint b(67890);
    std::cout << "a = " << a << std::endl;
    std::cout << "b = " << b << std::endl;

    // Addition
    bigint c = a + b;
    std::cout << "a + b = " << c << std::endl;   // expected: 80235

    // Right shift (floor division by 2)
    bigint d(100);
    bigint e = d >> 1;
    std::cout << "100 >> 1 = " << e << std::endl; // expected: 50

    bigint f(1000);
    bigint g = f >> 3;
    std::cout << "1000 >> 3 = " << g << std::endl; // expected: 125

    // Negative numbers
    bigint neg(-42);
    std::cout << "neg = " << neg << std::endl;    // expected: -42

    // Mixed-sign addition (subtraction of magnitudes)
    bigint h(100);
    bigint i(-30);
    bigint j = h + i;
    std::cout << "100 + (-30) = " << j << std::endl; // expected: 70

    // String constructor
    bigint big(std::string("999999999999999999999999"));
    bigint one(1LL);
    std::cout << "big + 1 = " << (big + one) << std::endl;

    // ------------------------------------------------------------------
    // vect2 tests
    // ------------------------------------------------------------------

    vect2 v1(3.0, 4.0);
    std::cout << "v1 = " << v1 << std::endl;

    // v * scalar  (requires operator* to be const-qualified)
    vect2 v2 = v1 * 2.0;
    std::cout << "v1 * 2 = " << v2 << std::endl; // expected: (6, 8)

    // scalar * v  (uses friend operator*)
    vect2 v3 = 0.5 * v1;
    std::cout << "0.5 * v1 = " << v3 << std::endl; // expected: (1.5, 2)

    // const vect2 – this was the compile error; must work after fix
    const vect2 cv(1.0, 2.0);
    vect2 v4 = cv * 3.0;
    std::cout << "cv * 3 = " << v4 << std::endl; // expected: (3, 6)

    // Vector addition
    vect2 v5 = v1 + cv;
    std::cout << "v1 + cv = " << v5 << std::endl; // expected: (4, 6)

    // Dot product
    std::cout << "v1.dot(cv) = " << v1.dot(cv) << std::endl; // expected: 11

    // Length of v1 == 5 (3-4-5 triangle)
    std::cout << "v1.length() = " << v1.length() << std::endl; // expected: 5

    return 0;
}
