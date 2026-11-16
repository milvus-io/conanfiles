#include <cstdint>
#include <stdexcept>
#include <string_view>

#include <folly/Uri.h>
#include <folly/tracing/AsyncStack.h>

#if defined(__linux__) && defined(__x86_64__) && defined(__GNUC__) && !defined(__clang__)
namespace {

// Throwing with an active async stack must still allow the caller to catch it.
__attribute__((noinline)) bool catchWithAsyncRoot() {
    folly::detail::ScopedAsyncStackRoot root;
    folly::AsyncStackFrame frame;
    root.activateFrame(frame);
    bool caught = false;
    try {
        throw std::runtime_error("expected exception");
    } catch (const std::runtime_error& error) {
        caught = std::string_view(error.what()) == "expected exception";
    }
    folly::deactivateAsyncStackFrame(frame);
    return caught;
}

// Without frame pointers, RBP is a general-purpose callee-saved register.
__attribute__((noinline, optimize("omit-frame-pointer"))) bool catchWithoutFramePointer() {
    std::uintptr_t stack_marker = 0;
    register std::uintptr_t data asm("rbp") =
        (reinterpret_cast<std::uintptr_t>(&stack_marker) & 0xffffffff00000000ULL) +
        0x100000001ULL;
    asm volatile("" : "+r"(data));
    const bool caught = catchWithAsyncRoot();
    asm volatile("" : "+r"(data));
    return caught;
}

} // namespace
#endif

int main() {
    if (folly::Uri("https://github.com/facebook/folly").host() != "github.com") {
        return 1;
    }
#if defined(__linux__) && defined(__x86_64__) && defined(__GNUC__) && !defined(__clang__)
    if (!catchWithoutFramePointer()) {
        return 1;
    }
#endif
}
