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
    void frame_to_string(Array3D* array, BoolArray* changed_pixels, char* output) {
        std::stringstream ss;
        std::string last_color = "";
        int same_color_start = -1;
        int total_pixels = array->shape[0] * array->shape[1];
        bool changed;
        //int change_count = 0;
        //int range_count = 0;
        //int passed_in_change_count = 0;

        // Iterate over each pixel in the array
        for (int i = 0; i < total_pixels; ++i) {
            // Check if the pixel has changed
            if (changed_pixels == nullptr)
                changed = true;
            else
                changed = changed_pixels->data[i];

            if (changed) {
                // passed_in_change_count++;

                // Access the RGB values of the pixel
                unsigned char* pixel = array->data + i * array->shape[2];
                int r = pixel[0] >> 2;
                int g = pixel[1] >> 2;
                int b = pixel[2] >> 2;

                // Combine RGB values to obtain an integer representation of the color
                int rgb_int = b << 10 | g << 5 | r;  // Swap red and blue channels

                // Adjust if in the Unicode surrogate range
                if (0xD800 <= rgb_int && rgb_int <= 0xDFFF) {
                    if (rgb_int < 0xDC00)
                        rgb_int = 0xD7FF;  // Maximum value just before the surrogate range
                    else
                        rgb_int = 0xE000;  // Minimum value just after the surrogate range
                }

                std::string color = encode_utf8(rgb_int);
                if (color != last_color)
                {
                    if (!last_color.empty() && same_color_start != -1) {
                    ss << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color;
                    //range_count++;
                    //std::cout << "Found Range: " << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color << std::endl;
                    }
                    same_color_start = i;
                    last_color = color;
                    //change_count++;
                }
         
            } else if (!changed && same_color_start != -1) {
                ss << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color;
                //range_count++;
                //std::cout << "Found interesting Range: " << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color << std::endl;
                same_color_start = -1;
                last_color = "";
            }

        }

        // After all pixels have been processed, handle any remaining color streak
        if (same_color_start != -1) {
            ss << same_color_start << "+" << total_pixels - 1 - same_color_start << "_" << last_color;
            //range_count++;
            //std::cout << "Found Range: " << same_color_start << "+" << total_pixels - 1 - same_color_start << "_" << last_color << std::endl;
        }

        // Convert the stringstream to a string
        std::string s = ss.str();

        // Copy the string to the output buffer and null-terminate it
        std::strncpy(output, s.c_str(), s.size());
        output[s.size()] = '\0';

        // Get the maximum number of bytes and characters for the output buffer
        size_t max_bytes = sizeof(output);
        size_t max_chars = max_bytes / sizeof(char) - 1;  // Exclude the null-terminator

        // // Print the number of changes, total pixels, range count, maximum bytes, and maximum characters
        // std::cout << "Passed-in Changes: " << passed_in_change_count << std::endl;
        // std::cout << "Found Changes: " << change_count << std::endl;
        // std::cout << "Total Pixels: " << total_pixels << std::endl;
        // std::cout << "Range Count: " << range_count << std::endl;
        // std::cout << "Maximum Bytes: " << max_bytes << std::endl;
        // std::cout << "Maximum Characters: " << max_chars << std::endl;
        // std::cout << "ss: " << ss.str() << std::endl;
        // std::cout << "Output: " << output << std::endl;
        // std::cout << "Done!" << std::endl;
    }
}