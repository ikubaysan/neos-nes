#include <string>

extern "C" const char* get_string() {
    std::string str = "Hello from C++";
    return str.c_str();
}
