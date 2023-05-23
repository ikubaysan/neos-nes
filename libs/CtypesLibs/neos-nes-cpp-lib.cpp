#include <string>
#include <cstring>
#include <sstream>
#include <vector>
#include <iostream>
#include <algorithm>
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
            // TODO: I might want to change this to something else. For now this is fine.
            // I definitely need this, otherwise my strings will be cut off.
            color.push_back(0x1);
        }
        else if (unicode < 0x80) {
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
        return color;
    }

    // Function to convert the array of pixels to a string representation
    void frame_to_string(Array3D* array, BoolArray* changed_pixels, char* output) 
    {
        std::string s;
        std::string last_color = "";
        int same_color_start = -1;
        int total_pixels = array->shape[0] * array->shape[1];
        bool changed;
        bool next_changed;
        bool prev_changed;

        // Create a vector of indices of changed pixels
        std::vector<int> changed_indices;
        for (int i = 0; i < total_pixels; ++i) {
            if (changed_pixels == nullptr)
                changed_indices.push_back(i);
            else if (changed_pixels->data[i])
                changed_indices.push_back(i);
        }

        int i = 0;
        int j = 0;
        bool regular_increment = false;
        bool just_added_changed_pixel = false;
        bool just_added_unchanged_pixel = false;

        // Find the next changed pixel
        while (j < changed_indices.size() && i < total_pixels) 
        {
            if (j < changed_indices.size() && (just_added_unchanged_pixel))
            {
                // Skip ahead to the next changed pixel
                i = changed_indices[j];
                std::cout << "skipping to " << i << std::endl;
                regular_increment = false;
            }
            else
            {
                // Simple iteration (we already incremented i once before)
                i = i;
                regular_increment = true;
            }

            if (changed_pixels == nullptr)
                changed = true;
            else
                changed = changed_pixels->data[i];

            just_added_changed_pixel = false;
            just_added_unchanged_pixel = false;

            if (changed) 
            {
                unsigned char* pixel = array->data + i * array->shape[2];
                int r = pixel[0] >> 2;
                int g = pixel[1] >> 2;
                int b = pixel[2] >> 2;
                int rgb_int = b << 10 | g << 5 | r;

                if (0xD800 <= rgb_int && rgb_int <= 0xDFFF) 
                {
                    if (rgb_int < 0xDC00)
                        rgb_int = 0xD7FF;
                    else
                        rgb_int = 0xE000;
                }

                auto cached = rgb_to_utf8_cache.find(rgb_int);
                std::string color;
                if (cached != rgb_to_utf8_cache.end()) 
                {
                    color = cached->second;
                } else 
                {
                    color = encode_utf8(rgb_int);
                    rgb_to_utf8_cache[rgb_int] = color;
                }

                if (color != last_color) 
                {
                    if (!last_color.empty() && same_color_start != -1) {
                        s += std::to_string(same_color_start) + "+" + std::to_string(i - 1 - same_color_start) + "_" + last_color;
                    }
                    same_color_start = i;
                    last_color = color;
                    just_added_changed_pixel = true;
                }
            }
            else if (same_color_start != -1 && !changed) 
            {
                s += std::to_string(same_color_start) + "+" + std::to_string(i - 1 - same_color_start) + "_" + last_color;
                same_color_start = -1;
                last_color = "";
                just_added_unchanged_pixel = true;
            }

            if (regular_increment)
            {
                i++;
                if (i > changed_indices[j])
                    j++;
            }
            else
            {
                j++;
            }
        }

        if (same_color_start != -1)
        {
            s += std::to_string(same_color_start) + "+" + std::to_string(total_pixels - 1 - same_color_start) + "_" + last_color;
        }
        std::strncpy(output, s.c_str(), s.size());
        output[s.size()] = '\0';
    }
}