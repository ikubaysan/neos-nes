#include <string>
#include <cstring>
#include <sstream>
#include <iostream>

extern "C" {
    typedef struct {
        int shape[3];
        unsigned char* data;
    } Array3D;

    typedef struct {
        int size;
        bool* data;
    } BoolArray;

    void frame_to_string(Array3D* array, BoolArray* changed_pixels, char* output) {
        std::ostringstream oss;
        int last_color = -1;
        int same_color_start = -1;
        int total_pixels = array->shape[0] * array->shape[1];

        for (int i = 0; i < total_pixels; ++i) {
            unsigned char* pixel = array->data + i * array->shape[2];
            int r = pixel[0] >> 2;
            int g = pixel[1] >> 2;
            int b = pixel[2] >> 2;
            int rgb_int = b << 10 | g << 5 | r;  // Swap red and blue channels

            // Adjust if in the Unicode surrogate range
            if (0xD800 <= rgb_int && rgb_int <= 0xDFFF) {
                if (rgb_int < 0xDC00)
                    rgb_int = 0xD7FF;  // Maximum value just before the surrogate range
                else
                    rgb_int = 0xE000;  // Minimum value just after the surrogate range
            }

            bool changed = changed_pixels ? changed_pixels->data[i] : true;

            if (changed && rgb_int != last_color) {
                if (last_color != -1 && same_color_start != -1) {
                    oss << same_color_start << "!" << i - 1 - same_color_start << "_" << (char)last_color;
                }
                same_color_start = i;
                last_color = rgb_int;
            } else if (!changed && same_color_start != -1) {
                oss << same_color_start << "!" << i - 1 - same_color_start << "_" << (char)last_color;
                same_color_start = -1;
                last_color = -1;
            }

            if (i == total_pixels - 1 && same_color_start != -1) {
                oss << same_color_start << "!" << i - same_color_start << "_" << (char)last_color;
            }
        }

        std::string result = oss.str();
        strncpy(output, result.c_str(), result.size());
        output[result.size()] = '\0';
    }
}
