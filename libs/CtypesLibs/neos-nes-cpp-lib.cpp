#include <string>
#include <cstring>
#include <sstream>
#include <iostream>
#include <unordered_map>

extern "C" {

    typedef struct {
        int shape[3];
        unsigned char* data;
    } Array3D;

    typedef struct {
        int size;
        bool* data;
    } BoolArray;

    std::unordered_map<int, std::string> rgb_to_utf8_cache;

    std::string encode_utf8(int unicode) {
        std::string color;
        if (unicode == 0) {
            // Replace null terminate symbol with a different unicode character
            color.push_back(0x1);
        }
        else {
            // Handle surrogate pairs
            if (0xD800 <= unicode && unicode <= 0xDFFF) {
                if (unicode < 0xDC00)
                    unicode = 0xD7FF;
                else
                    unicode = 0xE000;
            }

            if (unicode < 0x80) {
                color.push_back(unicode);
            } else if (unicode < 0x800) {
                color.push_back(0xC0 | (unicode >> 6));
                color.push_back(0x80 | (unicode & 0x3F));
            } else if (unicode < 0x10000) {
                color.push_back(0xE0 | (unicode >> 12));
                color.push_back(0x80 | ((unicode >> 6) & 0x3F));
                color.push_back(0x80 | (unicode & 0x3F));
            } else {
                color.push_back(0xF0 | (unicode >> 18));
                color.push_back(0x80 | ((unicode >> 12) & 0x3F));
                color.push_back(0x80 | ((unicode >> 6) & 0x3F));
                color.push_back(0x80 | (unicode & 0x3F));
            }
        }
        return color;
    }

    // Function to convert the array of pixels to a string representation
    void frame_to_string(Array3D* current_frame, Array3D* last_frame, char* output) {
        static Array3D* cached_last_frame = nullptr;
        static std::string cached_output;
        if (last_frame == cached_last_frame) {
            std::strncpy(output, cached_output.c_str(), cached_output.size());
            output[cached_output.size()] = '\0';
            return;
        }

        std::ostringstream ss;
        std::string last_color = "";
        int same_color_start = -1;
        int total_pixels = current_frame->shape[0] * current_frame->shape[1];
        bool changed;

        unsigned char* current_pixel = current_frame->data;
        unsigned char* last_pixel = last_frame ? last_frame->data : nullptr;

        for (int i = 0; i < total_pixels; ++i, current_pixel += current_frame->shape[2]) {
            changed = true;
            if (last_frame) {
                changed = memcmp(current_pixel, last_pixel, current_frame->shape[2]) != 0;
                last_pixel += last_frame->shape[2];
            }

            if (changed) {
                int r = current_pixel[0] >> 2;
                int g = current_pixel[1] >> 2;
                int b = current_pixel[2] >> 2;
                int rgb_int = b << 10 | g << 5 | r;

                auto cached = rgb_to_utf8_cache.find(rgb_int);
                std::string color;
                if (cached != rgb_to_utf8_cache.end()) {
                    color = cached->second;
                } else {
                    color = encode_utf8(rgb_int);
                    rgb_to_utf8_cache[rgb_int] = color;
                }

                if (color != last_color) {
                    if (!last_color.empty() && same_color_start != -1) {
                        ss << encode_utf8(same_color_start + 0x80) << encode_utf8(i - 1 - same_color_start + 0x80) << last_color;
                    }
                    same_color_start = i;
                    last_color = color;
                }
            } else if (same_color_start != -1 && !changed) {
                ss << encode_utf8(same_color_start + 0x80) << encode_utf8(i - 1 - same_color_start + 0x80) << last_color;
                same_color_start = -1;
                last_color = "";
            }
        }

        if (same_color_start != -1) {
            ss << encode_utf8(same_color_start + 0x80) << encode_utf8(total_pixels - 1 - same_color_start + 0x80) << last_color;
        }

        cached_output = ss.str();
        cached_last_frame = last_frame;
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';
    }


}