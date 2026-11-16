#include <iostream>
#include <folly/Uri.h>

#ifdef __linux__
#include <linux/time_types.h>
#include <folly/io/async/IoUringBackend.h>

static_assert(FOLLY_HAS_LIBURING, "Folly must expose io_uring support on Linux");
#endif

int main() {
    std::cout << folly::Uri("https://github.com/facebook/folly").host() << '\n';
#ifdef __linux__
    std::cout << "liburing major version: " << io_uring_major_version() << '\n';
    // Building and linking must work even when the host disables io_uring.
    std::cout << "io_uring available: " << folly::IoUringBackend::isAvailable() << '\n';
#endif
}
