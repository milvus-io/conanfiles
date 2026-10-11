# RE2 with a public necessary-literal API

`re2/20230301-milvus-regex1@milvus/dev` builds upstream RE2 **2023-03-01**
with the additive `RE2::RequiredLiterals()` API. The package preserves the
`RE2` object layout and matcher behavior. Consumers include only `re2/re2.h`;
AST headers and traversal stay inside the rebuilt dependency.

## Consume the package

```python
def requirements(self):
    self.requires("re2/20230301-milvus-regex1@milvus/dev#<recipe-revision>",
                  force=True)
```

`force=True` selects this RE2 consistently for transitive consumers such as
gRPC and Arrow. The CMake package and target remain `re2` and `re2::re2`.
Resolve the published revision from the Milvus Conan 2 remote, then replace
`<recipe-revision>` with that exact revision. If a matching binary is absent,
use `conan install --build=missing` to build from the published recipe.

```cpp
#include <re2/re2.h>

RE2 regexp("foo.*bar|baz.*qux");
RE2::LiteralRequirements required = regexp.RequiredLiterals();
```

`RE2_REQUIRED_LITERALS_API_VERSION` is `1`. The public value types are:

- `LiteralCondition::op`: `True`, `Literal`, `And`, or `Or`.
- `LiteralCondition::literal`: original case-sensitive bytes for a `Literal`.
- `LiteralCondition::children`: operands of an `And` or `Or`.
- `LiteralRequirements::condition`: a necessary condition for every match.
- `LiteralRequirements::literal`: one mandatory scan substring, or empty.

Evaluate `Literal` with byte-substring membership, `And` with all children,
and `Or` with any child. `True` imposes no restriction. The condition is a
superset of actual matches: **always run the original RE2 matcher on
candidates**, with its original encoding and options. The scan substring may
be one byte; index atoms are at least two bytes. Byte fragments from a bounded
Unicode literal are valid mandatory byte substrings, not standalone text.

## Bounds and conservative cases

The signature is:

```cpp
RE2::LiteralRequirements RequiredLiterals(size_t max_nodes = 127,
                                        size_t max_atom_bytes = 64,
                                        size_t max_literal_bytes = 4096,
                                        size_t max_visits = 4096) const;
```

Requests are capped at those defaults. Invalid regexps or budgets return an
empty scan literal and a `True` condition. Optional bodies, case folding,
non-singleton classes and unknown operators conservatively contribute no
required bytes. Zero-width assertions remain the original matcher's concern.
AND may omit requirements to satisfy its node budget; OR never drops a viable
branch. Exhausting the traversal budget returns `True` for the whole regexp.

Traversal reserves all immediate child visits **before** RE2's walker
allocates their result array. The reservation includes children handled with
`ShortVisit`, so a wide AST cannot allocate unbounded summaries after a small
visit budget is exhausted. The API neither recompiles regexps nor enumerates
literal subsets. Each call constructs its own scratch state and can run
concurrently on the same immutable `RE2` object.

## Package validation

`test_package` includes only installed public headers. Its runtime checks stay
enabled in Release and cover AND/OR candidate supersets, optional and folded
branches, short OR branches, UTF-8/Latin1, anchors, embedded NULs, invalid and
custom budgets, generated canonical differential cases and concurrent calls.
A deterministic resource regression compares allocations for AST widths 64
and 4096 at `max_visits=1`, independently of machine timing.

```sh
conan create recipes/re2/regex-v1 \
  --version=20230301-milvus-regex1 --user=milvus --channel=dev \
  -s build_type=Release -s compiler.cppstd=20
```

Upstream RE2 is BSD-3-Clause. The API implementation is Apache-2.0. Both
licenses are included in the package.
