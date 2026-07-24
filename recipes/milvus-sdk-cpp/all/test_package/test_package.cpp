#include <iostream>
#include "milvus/MilvusClient.h"

#if __has_include(<milvus/thirdparty/nlohmann/json.hpp>)
#include <milvus/thirdparty/nlohmann/json.hpp>
#else
#include <nlohmann/json.hpp>
#endif

int main() {
    auto client = milvus::MilvusClient::Create();
    const nlohmann::json result = {{"created", client != nullptr}};
    std::cout << "milvus-sdk-cpp test_package OK" << std::endl;
    return result.at("created").get<bool>() ? 0 : 1;
}
