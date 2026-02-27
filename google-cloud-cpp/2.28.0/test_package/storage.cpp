#include <google/cloud/storage/client.h>
#include <iostream>

int main(int argc, char* argv[]) {
  if (argc != 1) {
    std::cerr << "Usage: storage\n";
    return 1;
  }

  namespace gcs = google::cloud::storage;

  std::cout << "Testing google-cloud-cpp::storage library " << google::cloud::version_string() << "\n";
  auto client = gcs::Client();
  return 0;
}
