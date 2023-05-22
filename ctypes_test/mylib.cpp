#include <string>
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

    const char* frame_to_string(Array3D* array, BoolArray* changed_pixels) {
        std::stringstream ss;
        std::string last_color = "";
        int same_color_start = 0;
        int total_pixels = array->shape[0] * array->shape[1];
        bool changed;

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

            std::string color(1, rgb_int);

            // Check if pixel has changed
            if (changed_pixels == nullptr)
                changed = true;
            else
                changed = changed_pixels->data[i];

            if (changed && color != last_color) {
                if (!last_color.empty() && same_color_start >= 0) {
                    ss << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color;
                }
                same_color_start = i;
                last_color = color;
            } else if (!changed && same_color_start >= 0) {
                ss << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color;
                same_color_start = -1;
                last_color = "";
            }

            if (i == total_pixels - 1 && same_color_start >= 0) {  // the end of the pixels, add the last color
                ss << same_color_start << "+" << i - same_color_start << "_" << last_color;
            }
        }

        static std::string s = ss.str();
        std::cout << s << std::endl;
        return s.c_str();
    }


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