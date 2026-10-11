// Tests only the installed public API and canonical RE2 matcher.
#include <re2/re2.h>

#include <algorithm>
#include <atomic>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <new>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

// Count allocations made by RequiredLiterals(), excluding regexp compilation
// and test assertions. Thread-local counters keep the concurrent API test
// independent. A wide AST must not allocate a summary for every sibling after
// exhausting its visit budget.
namespace allocation_probe {
thread_local bool enabled = false;
thread_local size_t count = 0;
thread_local size_t bytes = 0;
}

void* operator new(size_t size) {
  if (void* pointer = std::malloc(size == 0 ? 1 : size)) {
    if (allocation_probe::enabled) {
      ++allocation_probe::count;
      allocation_probe::bytes += size;
    }
    return pointer;
  }
  throw std::bad_alloc();
}

void operator delete(void* pointer) noexcept { std::free(pointer); }
void* operator new[](size_t size) { return ::operator new(size); }
void operator delete[](void* pointer) noexcept { ::operator delete(pointer); }
#if __cplusplus >= 201402L
void operator delete(void* pointer, size_t) noexcept { ::operator delete(pointer); }
void operator delete[](void* pointer, size_t) noexcept { ::operator delete(pointer); }
#endif

namespace {
typedef RE2::LiteralCondition Condition;
typedef Condition::Op Op;
size_t checks = 0;
size_t matching_rows = 0;

void Check(bool passed, const char* message) {
  if (!passed)
    throw std::runtime_error(message);
  ++checks;
}

bool Satisfies(const Condition& condition, const std::string& row) {
  switch (condition.op) {
    case Op::True:
      return true;
    case Op::Literal:
      return row.find(condition.literal) != std::string::npos;
    case Op::And:
      for (const auto& child : condition.children)
        if (!Satisfies(child, row)) return false;
      return true;
    case Op::Or:
      for (const auto& child : condition.children)
        if (Satisfies(child, row)) return true;
      return false;
  }
  return false;
}

size_t Nodes(const Condition& condition) {
  size_t count = 1;
  for (const auto& child : condition.children)
    count += Nodes(child);
  return count;
}

bool HasOp(const Condition& condition, Op op) {
  if (condition.op == op) return true;
  for (const auto& child : condition.children)
    if (HasOp(child, op)) return true;
  return false;
}

bool HasAtom(const Condition& condition, const std::string& atom) {
  if (condition.op == Op::Literal && condition.literal == atom) return true;
  for (const auto& child : condition.children)
    if (HasAtom(child, atom)) return true;
  return false;
}

void Shape(const Condition& condition, size_t max_atom_bytes) {
  if (condition.op == Op::Literal) {
    Check(condition.literal.size() >= 2, "index atom is too short");
    Check(condition.literal.size() <= max_atom_bytes, "index atom exceeds budget");
    Check(condition.children.empty(), "literal unexpectedly has children");
  } else {
    Check(condition.literal.empty(), "non-literal unexpectedly has bytes");
    if (condition.op == Op::True)
      Check(condition.children.empty(), "TRUE unexpectedly has children");
    else
      Check(condition.children.size() >= 2, "boolean operator has too few children");
  }
  for (const auto& child : condition.children)
    Shape(child, max_atom_bytes);
}

void Superset(const RE2& regexp, const RE2::LiteralRequirements& requirements,
              const std::vector<std::string>& rows) {
  for (const auto& row : rows) {
    if (!RE2::PartialMatch(re2::StringPiece(row.data(), row.size()), regexp))
      continue;
    ++matching_rows;
    Check(Satisfies(requirements.condition, row), "condition excluded a canonical match");
    Check(requirements.literal.empty() ||
              row.find(requirements.literal) != std::string::npos,
          "scan literal excluded a canonical match");
  }
}

void DirectCases() {
  Check(RE2_REQUIRED_LITERALS_API_VERSION == 1, "unexpected public API version");
  RE2 both("foo.*bar");
  const auto required = both.RequiredLiterals();
  Check(HasOp(required.condition, Op::And), "AND relationship was lost");
  Check(HasAtom(required.condition, "foo") && HasAtom(required.condition, "bar"),
        "mandatory AND literals were lost");
  Superset(both, required, {"foobar", "xxfoo123barxx", "barfoo", "nothing"});

  RE2 either("foo.*bar|baz.*qux");
  const auto alternatives = either.RequiredLiterals();
  Check(HasOp(alternatives.condition, Op::Or), "OR relationship was lost");
  Superset(either, alternatives, {"foo123bar", "baz123qux", "nothing"});
  Check(Satisfies(alternatives.condition, "baz123qux"), "OR branch was dropped");

  RE2 suffix("(ERROR|WARN).*timeout");
  const auto suffix_requirements = suffix.RequiredLiterals();
  Check(HasAtom(suffix_requirements.condition, "timeout"), "mandatory suffix was lost");
  Superset(suffix, suffix_requirements, {"ERROR timeout", "WARN timeout"});

  RE2 optional("(?:foo)?bar");
  const auto optional_requirements = optional.RequiredLiterals();
  Check(!HasAtom(optional_requirements.condition, "foo"), "optional literal became mandatory");
  Superset(optional, optional_requirements, {"bar", "foobar", "xxxbar"});

  for (const std::string& pattern : {"(?i:foo)|bar", "ab|c", "foo|", ".*"}) {
    RE2 regexp(pattern);
    const auto requirements = regexp.RequiredLiterals();
    Check(requirements.condition.op == Op::True, "unsafe OR branch did not weaken to TRUE");
    Superset(regexp, requirements, {"FOO", "foo", "bar", "ab", "c", "", "anything"});
  }

  RE2 anchored("^foo$");
  Superset(anchored, anchored.RequiredLiterals(), {"foo", "foo\n", "xfoo"});
  RE2 repeated("(foo.*bar){2,3}");
  Superset(repeated, repeated.RequiredLiterals(), {"foobarfoobar", "fooxbarfooybarfoozbar"});
  RE2 unicode("汉字.*東京");
  const auto unicode_requirements = unicode.RequiredLiterals();
  Check(HasAtom(unicode_requirements.condition, "汉字"), "Unicode bytes were changed");
  Superset(unicode, unicode_requirements, {"汉字--東京", "prefix汉字suffix東京"});

  RE2::Options insensitive;
  insensitive.set_case_sensitive(false);
  RE2 folded("foo.*bar", insensitive);
  const auto folded_requirements = folded.RequiredLiterals();
  Check(folded_requirements.condition.op == Op::True, "folded bytes became mandatory");
  Superset(folded, folded_requirements, {"FOO BAR", "fOo bAr"});

  RE2::Options latin1;
  latin1.set_encoding(RE2::Options::EncodingLatin1);
  const std::string latin_atom("\xe9\xf6", 2);
  RE2 latin(latin_atom + ".*fin", latin1);
  const auto latin_requirements = latin.RequiredLiterals();
  Check(HasAtom(latin_requirements.condition, latin_atom), "Latin1 bytes were re-encoded");
  Superset(latin, latin_requirements, {latin_atom + "--fin", "x" + latin_atom + "fin"});

  const std::string nul_atom("ab\0cd", 5);
  const std::string nul_pattern = nul_atom + ".*ef";
  RE2 nul(re2::StringPiece(nul_pattern.data(), nul_pattern.size()));
  const auto nul_requirements = nul.RequiredLiterals();
  Check(HasAtom(nul_requirements.condition, nul_atom), "embedded NUL was truncated");
  Superset(nul, nul_requirements, {nul_atom + "xyzef"});

  RE2::Options quiet;
  quiet.set_log_errors(false);
  RE2 invalid("[", quiet);
  const auto invalid_requirements = invalid.RequiredLiterals();
  Check(!invalid.ok() && invalid_requirements.condition.op == Op::True &&
            invalid_requirements.literal.empty(), "invalid regexp exposed requirements");
}

void BudgetCases() {
  RE2 regexp("foo.*bar|baz.*qux");
  const RE2::LiteralRequirements invalid[] = {
      regexp.RequiredLiterals(0), regexp.RequiredLiterals(127, 1),
      regexp.RequiredLiterals(127, 64, 63), regexp.RequiredLiterals(127, 64, 4096, 0)};
  for (const auto& requirements : invalid)
    Check(requirements.condition.op == Op::True && requirements.literal.empty(),
          "invalid budget did not fail open");

  const std::vector<std::string> rows = {"foo123bar", "baz123qux", "xxxfoobaryyy"};
  for (size_t nodes : {size_t(1), size_t(3), size_t(7), size_t(127)}) {
    const auto requirements = regexp.RequiredLiterals(nodes, 2, 16, 4096);
    Check(Nodes(requirements.condition) <= nodes, "node budget exceeded");
    Shape(requirements.condition, 2);
    Check(requirements.literal.size() <= 16, "scan literal budget exceeded");
    Superset(regexp, requirements, rows);
  }
  const size_t unlimited = std::numeric_limits<size_t>::max();
  const auto capped = regexp.RequiredLiterals(unlimited, unlimited, unlimited, unlimited);
  Check(Nodes(capped.condition) <= 127, "hard node cap exceeded");
  Shape(capped.condition, 64);
  Superset(regexp, capped, rows);

  const std::string long_literal(5000, 'x');
  RE2::Options quiet;
  quiet.set_log_errors(false);
  RE2 long_regexp(long_literal, quiet);
  const auto long_requirements = long_regexp.RequiredLiterals();
  Check(long_requirements.literal.size() <= 4096, "long literal exceeded scan bound");
  Shape(long_requirements.condition, 64);
  Superset(long_regexp, long_requirements, {long_literal, "p" + long_literal + "s"});
}

struct AllocationCount { size_t count; size_t bytes; };

AllocationCount WideBudget(size_t width) {
  std::string pattern;
  for (size_t i = 0; i < width; ++i)
    pattern += "literal" + std::to_string(i) + ".*";
  pattern += "tail";
  RE2::Options options;
  options.set_max_mem(128 << 20);
  RE2 regexp(pattern, options);
  Check(regexp.ok(), "wide regexp did not compile");
  allocation_probe::count = allocation_probe::bytes = 0;
  allocation_probe::enabled = true;
  const auto requirements = regexp.RequiredLiterals(127, 64, 4096, 1);
  allocation_probe::enabled = false;
  const AllocationCount allocated = {allocation_probe::count, allocation_probe::bytes};
  std::cout << "AST width=" << width << ": allocations=" << allocated.count
            << " bytes=" << allocated.bytes << '\n';
  Check(requirements.condition.op == Op::True && requirements.literal.empty(),
        "exhausted wide traversal did not fail open");
  // RE2's std::stack uses a standard-library deque with a fixed initial block
  // (typically 4096 bytes on libc++). Allow that constant scratch allocation;
  // the equality across widths below rejects sibling-proportional allocation.
  Check(allocated.count <= 16 && allocated.bytes <= 16384,
        "wide traversal allocated beyond its visit budget");
  return allocated;
}

void ResourceCases() {
  const auto small = WideBudget(64);
  const auto large = WideBudget(4096);
  Check(large.count == small.count && large.bytes == small.bytes,
        "exhausted traversal allocation grew with AST width");
  std::cout << "wide_visit_budget=1: allocations=" << large.count
            << " bytes=" << large.bytes << " at widths 64 and 4096\n";
}

unsigned Next(unsigned& state) {
  state ^= state << 13;
  state ^= state >> 17;
  state ^= state << 5;
  return state;
}

void DifferentialCases() {
  std::vector<std::string> rows = {
      "", "foo", "bar", "foobar", "fooxbar", "bazxqux", "ERROR timeout",
      "WARN timeout", "FOO BAR", "foo\nbar", "ab", "c", "汉字東京",
      "foo123bar", "xxfoo12barxx", "foobazbarqux", "ababfoo",
      std::string("ab\0cd", 5), std::string("foo\0bar", 7)};
  unsigned state = 12345;
  const std::string alphabet = "abcfoxyz0123";
  for (size_t i = 0; i < 512; ++i) {
    std::string row;
    const size_t length = Next(state) % 80;
    for (size_t j = 0; j < length; ++j)
      row += alphabet[Next(state) % alphabet.size()];
    if (i % 3 == 0) row += "foo" + row + "bar";
    if (i % 5 == 0) row += "baz" + row + "qux";
    rows.push_back(row);
  }
  std::vector<std::string> patterns = {
      "foo.*bar", "foo.*bar|baz.*qux", "(ERROR|WARN).*timeout",
      "(?:foo)?bar", "(?:foo)*bar", "(?:foo){0,2}bar", "foo+bar",
      "foo{2,4}bar", "(foo.*bar){1,3}", "ab|c", "(?i:foo)|bar",
      "(?i:foo).*bar", "foo\\bbar", "^foo$", "[x]foo.*bar",
      "[ab]+foo", "\\Cfoo", "\\Qfoo.bar\\E.*baz", "汉字.*東京",
      "(?:ab|abc).*foo", "(?:foo|bar){2}", "foo.*", ".*bar", ".*", ""};
  const std::vector<std::string> atoms = {"foo", "bar", "baz", "qux"};
  for (const auto& a : atoms) {
    for (const auto& b : atoms) {
      patterns.push_back(a + ".*" + b);
      patterns.push_back("(?:" + a + "|" + b + ").*foo");
    }
  }
  for (const auto& pattern : patterns) {
    RE2 regexp(pattern);
    Check(regexp.ok(), "generated regexp did not compile");
    for (size_t nodes : {size_t(1), size_t(3), size_t(127)}) {
      const auto requirements = regexp.RequiredLiterals(nodes, 8, 128, 4096);
      Check(Nodes(requirements.condition) <= nodes, "differential node budget exceeded");
      Shape(requirements.condition, 8);
      Superset(regexp, requirements, rows);
    }
  }
}

void ConcurrentCases() {
  RE2 shared("foo.*bar|baz.*qux");
  std::atomic<bool> failed(false);
  std::vector<std::thread> threads;
  for (int i = 0; i < 4; ++i) {
    threads.emplace_back([&]() {
      for (int iteration = 0; iteration < 200; ++iteration) {
        const auto requirements = shared.RequiredLiterals();
        for (const std::string& row : {"foo123bar", "baz456qux"}) {
          if (!RE2::PartialMatch(row, shared) ||
              !Satisfies(requirements.condition, row) ||
              (!requirements.literal.empty() &&
               row.find(requirements.literal) == std::string::npos))
            failed.store(true);
        }
      }
    });
  }
  for (auto& thread : threads) thread.join();
  Check(!failed.load(), "concurrent calls disagreed with canonical RE2");
}
}  // namespace

int main() {
  try {
    DirectCases();
    BudgetCases();
    ResourceCases();
    DifferentialCases();
    ConcurrentCases();
    Check(matching_rows > 10000, "differential cases had insufficient positive matches");
    std::cout << "PASS: " << checks << " runtime checks; " << matching_rows
              << " canonical positive rows; 4 concurrent readers x 200 calls\n";
    return 0;
  } catch (const std::exception& error) {
    allocation_probe::enabled = false;
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
