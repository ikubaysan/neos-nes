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

    std::string encode_utf8(int unicode) {
    std::string result;
    if (unicode < 0x80) {
        result.push_back(unicode);
    } else if (unicode < 0x800) {
        result.push_back(0xC0 | (unicode >> 6));
        result.push_back(0x80 | (unicode & 0x3F));
    } else if (unicode < 0x10000) {
        result.push_back(0xE0 | (unicode >> 12));
        result.push_back(0x80 | ((unicode >> 6) & 0x3F));
        result.push_back(0x80 | (unicode & 0x3F));
    } else {
        result.push_back(0xF0 | (unicode >> 18));
        result.push_back(0x80 | ((unicode >> 12) & 0x3F));
        result.push_back(0x80 | ((unicode >> 6) & 0x3F));
        result.push_back(0x80 | (unicode & 0x3F));
    }
    return result;
}

    void frame_to_string(Array3D* array, BoolArray* changed_pixels, char* output) {
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

            //std::string color(1, rgb_int);
            std::string color = encode_utf8(rgb_int);

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

        std::string s = ss.str();
        //std::cout << s << std::endl;
        std::strncpy(output, s.c_str(), s.size());
        output[s.size()] = '\0';  // Null-terminate the output string
    }
}