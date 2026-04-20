#include <iostream>
#include "milvus/MilvusClient.h"

int main() {
    auto client = milvus::MilvusClient::Create();
    std::cout << "milvus-sdk-cpp test_package OK" << std::endl;
    return 0;
}
