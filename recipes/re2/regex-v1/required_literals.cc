// Copyright (C) 2026 Zilliz. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
// with the License. You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software distributed under the License
// is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
// or implied. See the License for the specific language governing permissions and limitations under the License

// This file is compiled inside the pinned RE2 dependency. Only the public
// value types declared in re2.h cross the dependency boundary.
#include "re2/re2.h"

#include <limits.h>
#include <algorithm>
#include <memory>
#include <utility>

#include "re2/regexp.h"
#include "re2/walker-inl.h"
#include "util/utf.h"

namespace re2 {
namespace {

typedef RE2::LiteralCondition Condition;
typedef Condition::Op Op;

size_t NodeCount(const Condition& node) {
  size_t count = 1;
  for (const auto& child : node.children)
    count += NodeCount(child);
  return count;
}

bool Equal(const Condition& a, const Condition& b) {
  if (a.op != b.op || a.literal != b.literal ||
      a.children.size() != b.children.size())
    return false;
  for (size_t i = 0; i < a.children.size(); ++i) {
    if (!Equal(a.children[i], b.children[i]))
      return false;
  }
  return true;
}

// Summaries describe every possible match of a subtree, including PartialMatch
// in external row context. Zero-width assertions consume no bytes; character
// classes, folding and optional subtrees conservatively contribute no bytes.
struct Summary {
  std::string prefix;
  std::string suffix;
  std::string best;
  bool exact = true;
  Condition condition;
};

class LiteralWalker : public Regexp::Walker<Summary*> {
 public:
  LiteralWalker(size_t max_nodes, size_t max_atom_bytes,
                size_t max_literal_bytes, size_t max_visits)
      : max_nodes_(max_nodes), max_atom_bytes_(max_atom_bytes),
        max_literal_bytes_(max_literal_bytes), max_visits_(max_visits) {}

  Summary* PreVisit(Regexp* re, Summary*, bool* stop) override {
    // Do not visit optional bodies: their literals are not mandatory. Likewise,
    // folding must not leak a canonical spelling into a byte-sensitive index.
    switch (re->op()) {
      case kRegexpStar:
      case kRegexpQuest:
        *stop = true;
        return Unknown();
      case kRegexpRepeat:
        if (re->max() == 0) {
          *stop = true;
          return new Summary;
        }
        if (re->min() == 0) {
          *stop = true;
          return Unknown();
        }
        break;
      default:
        break;
    }
    // Walker budgets PreVisit calls, but schedules all children of a visited
    // node before checking the next visit. Reserve their summaries before the
    // walker can allocate its child array, including eventual ShortVisits.
    // Optional bodies above are skipped and need no reservation.
    const size_t children = static_cast<size_t>(re->nsub());
    if (children > max_visits_ - scheduled_nodes_) {
      exhausted_ = true;
      *stop = true;
      return Unknown();
    }
    scheduled_nodes_ += children;
    return nullptr;
  }

  bool exhausted() const { return exhausted_; }

  Summary* ShortVisit(Regexp*, Summary*) override { return Unknown(); }

  Summary* PostVisit(Regexp* re, Summary*, Summary*, Summary** children,
                     int nchildren) override {
    std::unique_ptr<Summary> result(new Summary);
    switch (re->op()) {
      case kRegexpLiteral:
      case kRegexpLiteralString:
        if (re->parse_flags() & Regexp::FoldCase) {
          result->exact = false;
        } else if (re->op() == kRegexpLiteral) {
          Rune rune = re->rune();
          *result = Literal(&rune, 1, re->parse_flags());
        } else {
          *result = Literal(re->runes(), re->nrunes(), re->parse_flags());
        }
        break;
      case kRegexpCharClass:
        // A singleton class is exactly one rune. Wider classes remain unknown.
        if (re->cc()->size() == 1) {
          Rune rune = re->cc()->begin()->lo;
          *result = Literal(&rune, 1, re->parse_flags());
        } else {
          result->exact = false;
        }
        break;
      case kRegexpConcat:
        for (int i = 0; i < nchildren; ++i)
          *result = Concat(std::move(*result), *children[i]);
        break;
      case kRegexpAlternate:
        if (nchildren == 0) {
          result->exact = false;
          break;
        }
        *result = std::move(*children[0]);
        for (int i = 1; i < nchildren; ++i)
          *result = Alternate(std::move(*result), *children[i]);
        break;
      case kRegexpCapture:
        *result = std::move(*children[0]);
        break;
      case kRegexpPlus:
        *result = Repeat(*children[0], 1, -1);
        break;
      case kRegexpRepeat:
        *result = Repeat(*children[0], re->min(), re->max());
        break;
      case kRegexpEmptyMatch:
      case kRegexpBeginLine:
      case kRegexpEndLine:
      case kRegexpBeginText:
      case kRegexpEndText:
      case kRegexpWordBoundary:
      case kRegexpNoWordBoundary:
      case kRegexpHaveMatch:
        // Assertions leave adjacent byte runs adjacent. Their truth still
        // belongs to the original RE2 matcher, not this necessary condition.
        break;
      default:
        result->exact = false;
        break;
    }
    for (int i = 0; i < nchildren; ++i)
      delete children[i];
    return result.release();
  }

  Condition Required(const Summary& s) const {
    if (s.exact)
      return Atom(s.prefix);
    return Combine(Op::And,
                   Combine(Op::And, s.condition, Atom(s.prefix)),
                   Atom(s.suffix));
  }

 private:
  static Summary* Unknown() {
    Summary* s = new Summary;
    s->exact = false;
    return s;
  }

  Condition Combine(Op op, Condition a, Condition b) const {
    if (a.op == Op::True || b.op == Op::True) {
      if (op == Op::Or)
        return Condition();
      return a.op == Op::True ? std::move(b) : std::move(a);
    }
    if (Equal(a, b))
      return a;
    if (op == Op::And) {
      if (a.op != Op::And) {
        if (NodeCount(a) == max_nodes_)
          return a;
        Condition parent;
        parent.op = Op::And;
        parent.children.push_back(std::move(a));
        a = std::move(parent);
      }
      auto add = [&](Condition child) {
        for (const auto& existing : a.children) {
          if (Equal(existing, child) ||
              (existing.op == Op::Literal && child.op == Op::Literal &&
               existing.literal.find(child.literal) != std::string::npos))
            return;
        }
        if (child.op == Op::Literal) {
          a.children.erase(
              std::remove_if(a.children.begin(), a.children.end(),
                             [&](const Condition& existing) {
                               return existing.op == Op::Literal &&
                                      child.literal.find(existing.literal) !=
                                          std::string::npos;
                             }),
              a.children.end());
        }
        if (NodeCount(a) + NodeCount(child) <= max_nodes_)
          a.children.push_back(std::move(child));
      };
      if (b.op == Op::And) {
        for (auto& child : b.children)
          add(std::move(child));
      } else {
        add(std::move(b));
      }
      if (a.children.size() == 1)
        return std::move(a.children.front());
      return a;
    }
    // An AND may omit a requirement; an OR may never omit a viable branch.
    if (NodeCount(a) + NodeCount(b) + 1 > max_nodes_)
      return Condition();
    Condition result;
    result.op = Op::Or;
    result.children.push_back(std::move(a));
    result.children.push_back(std::move(b));
    return result;
  }

  Condition Atom(const std::string& bytes) const {
    if (bytes.size() < 2)
      return Condition();
    Condition first;
    first.op = Op::Literal;
    first.literal = bytes.substr(0, max_atom_bytes_);
    if (bytes.size() <= max_atom_bytes_)
      return first;
    Condition last;
    last.op = Op::Literal;
    last.literal = bytes.substr(bytes.size() - max_atom_bytes_);
    return Combine(Op::And, std::move(first), std::move(last));
  }

  static std::string RuneBytes(Rune rune, Regexp::ParseFlags flags) {
    if (flags & Regexp::Latin1)
      return std::string(1, static_cast<char>(rune));
    char bytes[UTFmax];
    return std::string(bytes, runetochar(bytes, &rune));
  }

  Summary Literal(const Rune* runes, int nrunes,
                  Regexp::ParseFlags flags) const {
    Summary result;
    int i = 0;
    for (; i < nrunes && result.prefix.size() <= max_literal_bytes_; ++i)
      result.prefix += RuneBytes(runes[i], flags);
    result.exact = i == nrunes && result.prefix.size() <= max_literal_bytes_;
    if (result.exact) {
      result.suffix = result.best = result.prefix;
      return result;
    }
    result.prefix.resize(std::min(result.prefix.size(), max_literal_bytes_));
    // Decode at most the bounded suffix, avoiding work proportional to a very
    // long rune run. Truncated byte fragments are still mandatory substrings.
    for (int j = nrunes - 1;
         j >= 0 && result.suffix.size() < max_literal_bytes_; --j)
      result.suffix.insert(0, RuneBytes(runes[j], flags));
    if (result.suffix.size() > max_literal_bytes_)
      result.suffix.erase(0, result.suffix.size() - max_literal_bytes_);
    result.best = result.prefix;
    result.condition =
        Combine(Op::And, Atom(result.prefix), Atom(result.suffix));
    return result;
  }

  Summary Concat(Summary a, const Summary& b) const {
    const bool exact = a.exact && b.exact &&
                       a.prefix.size() + b.prefix.size() <= max_literal_bytes_;
    const size_t bridge_size = std::min(
        max_literal_bytes_, a.suffix.size() + b.prefix.size());
    Condition condition;
    if (!exact) {
      condition = a.condition;
      if (!b.exact) {
        condition = Combine(Op::And, Required(a), Required(b));
        if (!a.suffix.empty() && !b.prefix.empty()) {
          std::string bridge = a.suffix;
          bridge.append(b.prefix, 0, max_literal_bytes_ - bridge.size());
          condition = Combine(Op::And, std::move(condition), Atom(bridge));
        }
      }
    }
    if (bridge_size > std::max(a.best.size(), b.best.size())) {
      a.best = a.suffix;
      a.best.append(b.prefix, 0, bridge_size - a.suffix.size());
    } else if (b.best.size() > a.best.size()) {
      a.best = b.best;
    }
    if (a.exact)
      a.prefix.append(b.prefix, 0, max_literal_bytes_ - a.prefix.size());
    if (b.exact) {
      const size_t keep = std::min(a.suffix.size(),
                                   max_literal_bytes_ - b.suffix.size());
      a.suffix.erase(0, a.suffix.size() - keep);
      a.suffix += b.suffix;
    } else {
      a.suffix = b.suffix;
    }
    a.exact = exact;
    a.condition = std::move(condition);
    return a;
  }

  Summary Alternate(Summary a, const Summary& b) const {
    Condition condition = Combine(Op::Or, Required(a), Required(b));
    const bool exact = a.exact && b.exact && a.prefix == b.prefix;
    size_t prefix = 0;
    while (prefix < a.prefix.size() && prefix < b.prefix.size() &&
           a.prefix[prefix] == b.prefix[prefix])
      ++prefix;
    size_t suffix = 0;
    while (suffix < a.suffix.size() && suffix < b.suffix.size() &&
           a.suffix[a.suffix.size() - suffix - 1] ==
               b.suffix[b.suffix.size() - suffix - 1])
      ++suffix;
    a.prefix.resize(prefix);
    a.suffix.erase(0, a.suffix.size() - suffix);
    a.best = a.prefix.size() >= a.suffix.size() ? a.prefix : a.suffix;
    a.exact = exact;
    a.condition = std::move(condition);
    return a;
  }

  Summary Repeat(Summary atom, int minimum, int maximum) const {
    if (maximum == 0 || (atom.exact && atom.prefix.empty()))
      return Summary();
    if (minimum == 1) {
      atom.condition = Required(atom);
      atom.exact = atom.exact && maximum == 1;
      return atom;
    }
    Summary result;
    // Exponentiation bounds preparation even for nested counted repetition.
    for (int n = minimum; n != 0; n >>= 1) {
      if (n & 1)
        result = Concat(std::move(result), atom);
      if (n > 1)
        atom = Concat(atom, atom);
    }
    if (minimum != maximum) {
      result.condition = Required(result);
      result.exact = false;
    }
    return result;
  }

  const size_t max_nodes_;
  const size_t max_atom_bytes_;
  const size_t max_literal_bytes_;
  const size_t max_visits_;
  size_t scheduled_nodes_ = 1;
  bool exhausted_ = false;
};

}  // namespace

RE2::LiteralRequirements RE2::RequiredLiterals(
    size_t max_nodes, size_t max_atom_bytes, size_t max_literal_bytes,
    size_t max_visits) const {
  LiteralRequirements result;
  if (!ok() || max_nodes == 0 || max_atom_bytes < 2 ||
      max_literal_bytes < max_atom_bytes || max_visits == 0)
    return result;
  max_nodes = std::min(max_nodes, size_t{127});
  max_atom_bytes = std::min(max_atom_bytes, size_t{64});
  max_literal_bytes = std::min(max_literal_bytes, size_t{4096});
  max_visits = std::min(max_visits, size_t{4096});
  LiteralWalker walker(max_nodes, max_atom_bytes, max_literal_bytes,
                       max_visits);
  std::unique_ptr<Summary> summary(walker.WalkExponential(
      entire_regexp_, nullptr,
      static_cast<int>(std::min(max_visits, static_cast<size_t>(INT_MAX)))));
  if (walker.exhausted() || walker.stopped_early())
    return result;
  result.condition = walker.Required(*summary);
  result.literal = std::move(summary->best);
  return result;
}

}  // namespace re2
