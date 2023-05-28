#include <string>
#include <cstring>
#include <sstream>
#include <iostream>
#include <unordered_map>

extern "C"
{

    typedef struct
    {
        int shape[3];
        unsigned char *data;
    } Array3D;

    typedef struct
    {
        int size;
        bool *data;
    } BoolArray;

    std::unordered_map<int, std::string> rgb_to_utf8_cache;
    const int OFFSET = 3;

    std::string encode_utf8(int unicode)
    {
        std::string color;

        if (unicode == 0)
        {
            // When unicode is 0, we cannot simply put 0x0 into the string as it's considered the null terminator.
            // Moreover, 0x1 and 0x2 are reserved for delimiters. So, we start our encoding from 0x3.
            // Here we add our OFFSET to the unicode value (0) before adding it to the string.
            color.push_back(0x3 + OFFSET);
        }
        else
        {
            // Add the offset to the unicode. This offset is used to avoid the reserved values at the beginning.
            unicode += OFFSET;

            // Handling surrogates that are not legal Unicode values.
            // The range from 0xD800 to 0xDFFF is reserved for surrogate pairs in UTF-16 encoding.
            // Therefore, if our code falls within this range, we set it to either 0xD7FF or 0xE000.
            if (0xD800 <= unicode && unicode <= 0xDFFF)
            {
                if (unicode < 0xDC00)
                    unicode = 0xD7FF;
                else
                    unicode = 0xE000;
            }

            // Encoding the unicode to UTF-8 following the standard rules.
            if (unicode < 0x80)
            {
                // For unicode values less than 0x80, UTF-8 encoding is the same as the unicode value.
                color.push_back(unicode);
            }
            else if (unicode < 0x800)
            {
                // For unicode values less than 0x800, the UTF-8 encoding is done with two bytes.
                // The first byte starts with '110' followed by the 5 most significant bits of the unicode value.
                // The second byte starts with '10' followed by the 6 least significant bits of the unicode value.
                color.push_back(0xC0 | (unicode >> 6));
                color.push_back(0x80 | (unicode & 0x3F));
            }
            else if (unicode < 0x10000)
            {
                // For unicode values less than 0x10000, the UTF-8 encoding is done with three bytes.
                // The first byte starts with '1110' followed by the 4 most significant bits of the unicode value.
                // The remaining bytes start with '10' followed by the 6 next most significant bits of the unicode value.
                color.push_back(0xE0 | (unicode >> 12));
                color.push_back(0x80 | ((unicode >> 6) & 0x3F));
                color.push_back(0x80 | (unicode & 0x3F));
            }
            else
            {
                // For unicode values greater than or equal to 0x10000, the UTF-8 encoding is done with four bytes.
                // The first byte starts with '11110' followed by the 3 most significant bits of the unicode value.
                // The remaining bytes start with '10' followed by the 6 next most significant bits of the unicode value.
                color.push_back(0xF0 | (unicode >> 18));
                color.push_back(0x80 | ((unicode >> 12) & 0x3F));
                color.push_back(0x80 | ((unicode >> 6) & 0x3F));
                color.push_back(0x80 | (unicode & 0x3F));
            }
        }
        return color;
    }

    void frame_to_string(Array3D *current_frame, Array3D *last_frame, char *output)
    {
        // Cached variables to optimize repeated calls with the same last_frame
        static Array3D *cached_last_frame = nullptr;
        static std::string cached_output;

        // If last_frame is the same as the cached_last_frame, return the cached output
        if (last_frame == cached_last_frame)
        {
            std::strncpy(output, cached_output.c_str(), cached_output.size());
            output[cached_output.size()] = '\0';
            return;
        }

        // String stream to build the output message
        std::ostringstream ss;

        std::string last_color = "";
        int same_color_start = -1;
        int row_index = 0;
        int total_pixels = current_frame->shape[0] * current_frame->shape[1];
        bool changed;

        unsigned char *current_pixel = current_frame->data;
        unsigned char *last_pixel = last_frame ? last_frame->data : nullptr;

        for (int i = 0; i < total_pixels; ++i, current_pixel += current_frame->shape[2])
        {
            changed = true;
            if (last_frame)
            {
                // Compare the current pixel with the corresponding pixel in the last frame
                changed = memcmp(current_pixel, last_pixel, current_frame->shape[2]) != 0;
                last_pixel += last_frame->shape[2];
            }

            // Check for the start of a new row
            if (i % current_frame->shape[1] == 0 && i > 0)
            {
                // Check if there was a continuous range of the same color in the previous row
                if (same_color_start != -1)
                {
                    // Encode the start and length of the range as UTF-8 characters and append to the string stream
                    if (i - same_color_start > 1)
                    {
                        ss << encode_utf8(same_color_start) << encode_utf8(i - same_color_start - 1);
                    }
                    else
                    {
                        ss << encode_utf8(same_color_start);
                    }
                    ss << '\x01'; // add delimiter A (end of color)
                }

                // Check if this is not the first row (no need to start with a row delimiter)
                if (row_index != 0)
                {
                    ss << '\x02'; // add delimiter B (end of row)
                }

                ss << encode_utf8(row_index);
                row_index++;
                same_color_start = -1;
            }

            if (changed)
            {
                // Extract the RGB values from the current pixel
                int r = current_pixel[0] >> 2;
                int g = current_pixel[1] >> 2;
                int b = current_pixel[2] >> 2;
                int rgb_int = b << 10 | g << 5 | r;
                rgb_int += OFFSET; // Add the offset here

                // Check if the RGB to UTF-8 conversion is already cached
                if (rgb_to_utf8_cache.count(rgb_int) == 0)
                {
                    rgb_to_utf8_cache[rgb_int] = encode_utf8(rgb_int);
                }

                // Check if the current color is the same as the previous color
                if (last_color == rgb_to_utf8_cache[rgb_int] && same_color_start != -1)
                {
                    continue;
                }

                // If there was a continuous range of the same color, encode it and append to the string stream
                if (same_color_start != -1)
                {
                    if (i - same_color_start > 1)
                    {
                        ss << encode_utf8(same_color_start) << encode_utf8(i - same_color_start - 1);
                    }
                    else
                    {
                        ss << encode_utf8(same_color_start);
                    }
                    ss << '\x01'; // add delimiter A (end of color)
                }

                same_color_start = i;
                last_color = rgb_to_utf8_cache[rgb_int];
                ss << last_color;
            }
        }

        // Check if there was a continuous range of the same color in the last row
        if (same_color_start != -1)
        {
            if (total_pixels - same_color_start > 1)
            {
                ss << encode_utf8(same_color_start) << encode_utf8(total_pixels - same_color_start - 1);
            }
            else
            {
                ss << encode_utf8(same_color_start);
            }
            ss << '\x01'; // add delimiter A (end of color)
        }
        ss << '\x02'; // add delimiter B (end of row)

        // Cache the output and copy it to the provided output buffer
        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';

        // Update the cached last_frame
        cached_last_frame = last_frame;
    }
}
