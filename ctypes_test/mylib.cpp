#include <string>
#include <sstream>

extern "C" {

    typedef struct {
        int shape[3];
        unsigned char* data;
    } Array3D;

    const char* process_array(Array3D* array) {
        std::stringstream ss;

        for (int i = 0; i < array->shape[0]; ++i) {
            unsigned char* row = array->data + i * array->shape[1] * array->shape[2];
            ss << (int)row[1 * array->shape[2] + 0] << ",";  // R
            ss << (int)row[1 * array->shape[2] + 1] << ",";  // G
            ss << (int)row[1 * array->shape[2] + 2] << "\n"; // B

            if (i < array->shape[0] - 1)
                ss << ",";
        }

        static std::string s = ss.str();
        return s.c_str();
    }
}