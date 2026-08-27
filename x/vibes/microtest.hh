#pragma once
// microtest.hpp — a single-header, zero-dependency C++20 test harness.
//
// Usage:
//
//     #include "microtest.hpp"
//
//     TEST("addition works") {
//         CHECK(1 + 1 == 2);      // records failure, keeps going
//         REQUIRE(1 + 1 == 2);    // records failure, aborts this test
//         CHECK_THROWS(risky());  // passes iff an exception is thrown
//     }
//
//     TEST_MAIN                   // expands to main()
//
// Build:   g++ -std=c++20 -Wall -Wextra -O2 tests.cpp -o tests
// Run:     ./tests                  all tests
//          ./tests vector           only tests whose name contains "vector"
//          NO_COLOR=1 ./tests       plain output
// Exit code is 0 when everything passes, 1 otherwise (CI-friendly).
//
// Caveat (shared with Catch2/doctest): the decomposer splits one top-level comparison, so logical operators need extra
// parens: CHECK((a && b)).
#include <chrono>
#include <concepts>
#include <cstdio>
#include <cstdlib>
#include <format>
#include <iterator>
#include <source_location>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

namespace mt {

// output
//

inline bool colour() {
    static const bool on = std::getenv("NO_COLOR") == nullptr;
    return on;
}

inline std::string_view red() {
    return colour() ? "\x1b[31m" : "";
}

inline std::string_view green() {
    return colour() ? "\x1b[32m" : "";
}

inline std::string_view dim() {
    return colour() ? "\x1b[2m"  : "";
}

inline std::string_view reset() {
    return colour() ? "\x1b[0m"  : "";
}

inline void out(std::string_view s) {
    std::fwrite(s.data(), 1, s.size(), stdout);
}

// value rendering
//

// A type is printable if std::formatter is specialized for it. The standard guarantees disabled formatter
// specializations are not default-constructible, which gives us a clean C++20 detection idiom (std::formattable is
// C++23).

template <class T>
concept Formattable =
    std::is_default_constructible_v<std::formatter<std::remove_cvref_t<T>, char>>;

template <class T>
std::string repr(const T& v) {
    using U = std::remove_cvref_t<T>;

    if constexpr (std::same_as<U, bool>){
        return v ? "true" : "false";
    } else if constexpr (std::same_as<U, char>) {
        return std::format("'{}'", v);
    } else if constexpr (std::convertible_to<const T&, std::string_view>) {
        return std::format("\"{}\"", std::string_view(v));
    } else if constexpr (Formattable<T>) {
        return std::format("{}", v);
    } else {
        return "<unprintable>";  // specialize std::formatter<T> to fix
    }
}

// comparisons
//

// Integer comparisons go through std::cmp_* so that signed/unsigned mixes compare mathematically (CHECK(-1 ==
// 4294967295u) fails, as it should) and -Wsign-compare stays quiet. Everything else uses the plain operator.

template <class T>
concept SafeInt =
    std::integral<T> &&
    !std::same_as<T, bool> &&
    !std::same_as<T, char> &&
    !std::same_as<T, wchar_t> &&
    !std::same_as<T, char8_t> &&
    !std::same_as<T, char16_t> &&
    !std::same_as<T, char32_t>;

template <class A, class B> constexpr bool eq(const A& a, const B& b) {
    if constexpr (SafeInt<A> && SafeInt<B>) {
        return std::cmp_equal(a, b);
    } else {
        return a == b;
    }
}

template <class A, class B> constexpr bool ne(const A& a, const B& b) {
    if constexpr (SafeInt<A> && SafeInt<B>) {
        return std::cmp_not_equal(a, b);
    } else {
        return a != b;
    }
}

template <class A, class B> constexpr bool lt(const A& a, const B& b) {
    if constexpr (SafeInt<A> && SafeInt<B>) {
        return std::cmp_less(a, b);
    } else {
        return a < b;
    }
}

template <class A, class B> constexpr bool le(const A& a, const B& b) {
    if constexpr (SafeInt<A> && SafeInt<B>) {
        return std::cmp_less_equal(a, b);
    } else {
        return a <= b;
    }
}

template <class A, class B> constexpr bool gt(const A& a, const B& b) {
    if constexpr (SafeInt<A> && SafeInt<B>) {
        return std::cmp_greater(a, b);
    } else {
        return a > b;
    }
}

template <class A, class B> constexpr bool ge(const A& a, const B& b) {
    if constexpr (SafeInt<A> && SafeInt<B>) {
       return std::cmp_greater_equal(a, b);
   } else {
       return a >= b;
   }
}

// expression decomposer
//

// CHECK(a == b) expands to  check_impl(Decomposer{} << a == b, ...). operator<< binds tighter than every comparison
// operator, so this parses as (Decomposer{} << a) == b: the decomposer captures the left-hand side, then our operator==
// runs the real comparison and remembers both values. This is the same trick Catch2 and doctest use to print
// "left/right" on failure.

struct Outcome {
    bool ok;
    std::string lhs, op, rhs;  // filled in only on failure; op empty => bare bool
};

template <class A, class B>
Outcome outcome(bool ok, std::string_view op, const A& a, const B& b) {
    if (ok) {
        return {true, {}, {}, {}};  // lazy: format only on failure
    } else {
        return {false, repr(a), std::string(op), repr(b)};
    }
}

template <class L>
struct Bound {
    const L& lhs;

    template <class R> Outcome operator==(const R& r) const {
        return outcome(eq(lhs, r), "==", lhs, r);
    }

    template <class R> Outcome operator!=(const R& r) const {
        return outcome(ne(lhs, r), "!=", lhs, r);
    }

    template <class R> Outcome operator< (const R& r) const {
        return outcome(lt(lhs, r), "<",  lhs, r);
    }

    template <class R> Outcome operator<=(const R& r) const {
        return outcome(le(lhs, r), "<=", lhs, r);
    }

    template <class R> Outcome operator> (const R& r) const {
        return outcome(gt(lhs, r), ">",  lhs, r);
    }

    template <class R> Outcome operator>=(const R& r) const {
        return outcome(ge(lhs, r), ">=", lhs, r);
    }
};

struct Decomposer {
    template <class L> Bound<L> operator<<(const L& l) const {
        return {l};
    }
};

// per-test bookkeeping
//

struct Context {
    int checks = 0;
    int failures = 0;
    std::string log;  // failure details, printed under the test's FAIL line
};

inline thread_local Context* current = nullptr;

inline Context& ctx() {
    if (!current) {
        std::fputs("microtest: assertion used outside a TEST\n", stderr);
        std::abort();
    }
    return *current;
}

struct require_failed {};  // thrown by REQUIRE to abort the current test

// assertions
//

inline bool record(
    const Outcome& o,
    std::string_view macro,
    std::string_view text,
    std::string_view note,
    std::source_location loc
) {
    Context& c = ctx();

    ++c.checks;
    if (o.ok) {
        return true;
    }
    ++c.failures;

    auto sink = std::back_inserter(c.log);

    std::format_to(
        sink,
        "    {}{}:{}:{} {}( {} ) failed{}{}\n",
        dim(),
        loc.file_name(),
        loc.line(),
        reset(),
        macro,
        text,
        note.empty() ? "" : " — ",
        note
    );

    if (!o.op.empty()) {
        std::format_to(
            sink,
             "        left:  {}\n        right: {}\n",
             o.lhs,
             o.rhs
         );
    }

    return false;
}

// Binary comparison path: the decomposer already produced an Outcome.
inline bool check_impl(
    const Outcome& o,
    std::string_view macro,
    std::string_view text,
    std::source_location loc
) {
    return record(
        o,
        macro,
        text,
        {},
        loc
    );
}

// Bare condition path: no comparison operator fired, e.g. CHECK(s.empty()).
template <class L>
    requires std::convertible_to<const L&, bool>
bool check_impl(
    const Bound<L>& b,
    std::string_view macro,
    std::string_view text,
    std::source_location loc
) {
    return record(
        {static_cast<bool>(b.lhs),{}, {}, {}},
        macro,
        text,
        {},
        loc
    );
}

template <class F>
bool throws_impl(F&& body, std::string_view text, std::source_location loc) {
    bool threw = false;

    try {
        body();
    } catch (...) {
        threw = true;
    }

    return record(
        {threw, {}, {}, {}},
        "CHECK_THROWS",
        text,
        "no exception was thrown",
        loc
    );
}

// registry
//

struct Test {
    std::string_view name;
    void (*fn)();
};

inline std::vector<Test>& registry() {
    static std::vector<Test> r;  // function-local static: safe across TUs
    return r;
}

struct Registrar {
    Registrar(std::string_view name, void (*fn)()) { registry().push_back({name, fn}); }
};

// runner
//

inline int run(int argc = 1, char** argv = nullptr) {
    const std::string_view filter = (argc > 1 && argv) ? std::string_view{argv[1]} : std::string_view{};

    int passed = 0, failed = 0, filtered_out = 0, total_checks = 0;
    const auto t0 = std::chrono::steady_clock::now();

    for (const Test& t : registry()) {
        if (!filter.empty() && t.name.find(filter) == std::string_view::npos) {
            ++filtered_out;
            continue;
        }

        Context c;
        current = &c;

        try {
            t.fn();

        } catch (const require_failed&) {
            // the failing REQUIRE already recorded itself

        } catch (const std::exception& e) {
            ++c.failures;
            std::format_to(
                std::back_inserter(c.log),
                "    unhandled exception: {}\n",
                e.what()
            );

        } catch (...) {
            ++c.failures;
            c.log += "    unhandled exception (not derived from std::exception)\n";
        }

        current = nullptr;
        total_checks += c.checks;

        if (c.failures == 0) {
            ++passed;

            out(std::format(
                "{}\u2713{} {} {}({} check{}){}\n",
                green(),
                reset(),
                t.name,
                dim(),
                c.checks,
                c.checks == 1 ? "" : "s",
                reset()
            ));

        } else {
            ++failed;

            out(std::format(
                "{}\u2717{} {}\n{}",
                red(),
                reset(),
                t.name,
                c.log
            ));

        }
    }

    const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();

    out(std::format(
        "\n{}{} passed, {} failed{}{} {}({} checks in {:.2f} ms){}\n",
        failed ? red() : green(),
        passed,
        failed,
        reset(),
        filtered_out ? std::format(", {} filtered out", filtered_out) : "",
        dim(),
        total_checks,
        ms,
        reset()
    ));

    return failed == 0 ? 0 : 1;
}

}  // namespace mt

// macros
//

// Macros survive here for the two things C++20 still can't do in a library: stringifying the checked expression
// (#__VA_ARGS__) and pasting unique names for auto-registration. File/line come from std::source_location instead of
// __FILE__/__LINE__, and __VA_ARGS__ keeps commas inside CHECK(f(a, b) == c) intact.

#define MT_CONCAT_(a, b) a##b
#define MT_CONCAT(a, b) MT_CONCAT_(a, b)

#define TEST(name)                                              \
    static void MT_CONCAT(mt_test_, __LINE__)();                \
    [[maybe_unused]]                                            \
    static const ::mt::Registrar MT_CONCAT(mt_reg_, __LINE__){  \
        name,                                                   \
        &MT_CONCAT(mt_test_, __LINE__)                          \
    };                                                          \
    static void MT_CONCAT(mt_test_, __LINE__)()

#define MT_ASSERT(MACRO, ...)               \
    ::mt::check_impl(                       \
        ::mt::Decomposer{} << __VA_ARGS__,  \
        MACRO,                              \
        #__VA_ARGS__,                       \
        std::source_location::current()     \
    )

#define CHECK(...) MT_ASSERT("CHECK", __VA_ARGS__)

#define REQUIRE(...)                               \
    do {                                           \
        if (!MT_ASSERT("REQUIRE", __VA_ARGS__)) {  \
            throw ::mt::require_failed{};          \
        }                                          \
    } while (0)

#define CHECK_THROWS(...)                \
    ::mt::throws_impl(                   \
        [&] { (void)(__VA_ARGS__); },    \
        #__VA_ARGS__,                    \
        std::source_location::current()  \
    )

#define TEST_MAIN                       \
    int main(int argc, char** argv) {   \
        return ::mt::run(argc, argv);   \
    }
