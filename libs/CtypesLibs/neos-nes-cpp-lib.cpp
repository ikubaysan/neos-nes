#include <string>
#include <cstring>
#include <sstream>
#include <iostream>
#include <vector>
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
    const int OFFSET = 16;
    const int DELIMITER_CODEPOINT_DECIMAL = 2;

    std::string encode_utf8(int unicode, int offset = OFFSET) {
        // Function to encode a Unicode code point into UTF-8 representation
        std::string color;
        if (unicode == 0) {
            // Replace null terminate symbol with a different Unicode character
            color.push_back(0x1);
        }
        else {
            unicode += offset;
            // Handle surrogate pairs
            if (0xD800 <= unicode && unicode <= 0xDFFF) {
                if (unicode < 0xDC00)
                    unicode = 0xD7FF;
                else
                    unicode = 0xE000;
            }

            // Encode the code point into UTF-8 bytes
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

    std::string encode_index(int index) {
        // Function to split and encode the index into two parts
        int part1 = std::min(55295, index);
        int part2 = index - part1;
        return encode_utf8(part1) + encode_utf8(part2);
    }

    void frame_to_string(Array3D* current_frame, Array3D* last_frame, char* output) {
        // Function to convert the array of pixels to a string representation
        static Array3D* cached_last_frame = nullptr;
        static std::string cached_output;

        if (last_frame == cached_last_frame) {
            // If the last frame is the same as the cached frame, return the cached output
            std::strncpy(output, cached_output.c_str(), cached_output.size());
            output[cached_output.size()] = '\0';
            return;
        }

        std::unordered_map<int, std::vector<std::pair<int, int>>> color_map;
        int total_pixels = current_frame->shape[0] * current_frame->shape[1];
        bool changed;
        int prev_rgb_int = -1; // track the previous pixel color

        unsigned char* current_pixel = current_frame->data;
        unsigned char* last_pixel = last_frame ? last_frame->data : nullptr;

        for (int i = 0; i < total_pixels; ++i, current_pixel += current_frame->shape[2]) {
            // Iterate through each pixel
            changed = true;
            if (last_frame) {
                changed = memcmp(current_pixel, last_pixel, current_frame->shape[2]) != 0;
                last_pixel += last_frame->shape[2];
            }

            if (changed) {
                // If the pixel has changed
                int r = current_pixel[0] >> 2;
                int g = current_pixel[1] >> 2;
                int b = current_pixel[2] >> 2;
                int rgb_int = (b << 10 | g << 5 | r);

                if (prev_rgb_int != -1 && rgb_int == prev_rgb_int && !color_map[rgb_int].empty()) {
                    // if the current pixel has the same color as the previous one
                    // increase the span length of the last entry for this color
                    color_map[rgb_int].back().second++;
                } else {
                    // otherwise start a new span
                    color_map[rgb_int].push_back(std::make_pair(i, 1));
                }

                prev_rgb_int = rgb_int;  // update the previous color
            }
        }

        std::ostringstream ss;
        for (const auto& color : color_map) {
            // Encode the RGB integer value and append it to the string stream
            ss << encode_utf8(color.first);

            // Iterate over the pairs (pixel index and span length) for the current color
            for (int pair_index = 0; pair_index < color.second.size(); pair_index++) {
                // Encode the pixel index and append it to the string stream
                ss << encode_index(color.second[pair_index].first);

                // Encode the span length and append it to the string stream
                ss << encode_utf8(color.second[pair_index].second);

                // Encode the difference between the current pixel index and the pixel index of the next pair
                int next_pixel_index;
                if (pair_index == color.second.size() - 1) {
                    // This is the last pair. The next pixel index is the total number of pixels
                    next_pixel_index = total_pixels - 1;
                } else {
                    // The next pixel index is the pixel index of the next pair
                    next_pixel_index = color.second[pair_index + 1].first;
                }

                int diff = next_pixel_index - color.second[pair_index].first;
                //std::cout << "Original diff value: " << diff << std::endl;
                ss << encode_utf8(diff);
                //std::cout << "Encoded diff value: " << encode_utf8(diff) << std::endl;
            }

            // Append the delimiter to the string stream
            ss << encode_utf8(DELIMITER_CODEPOINT_DECIMAL);  // delimiter
        }

        cached_output = ss.str();
        cached_last_frame = last_frame;
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';

        // Print the cached output
        //std::cout << cached_output << std::endl;

        //// Print the color_map
        std::cout << "Color Map:" << std::endl;
        for (const auto& color : color_map) {
            std::cout << "RGB Int: " << color.first << std::endl;
            for (const auto& pair : color.second) {
                std::cout << "Pixel Index: " << pair.first << ", Span Length: " << pair.second << std::endl;
            }
            break;
        }

    }

}
