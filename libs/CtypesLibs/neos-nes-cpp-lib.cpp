#include <string>
#include <vector>
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
    const int OFFSET = 16;
    const int SURROGATE_RANGE_SIZE = 2048;

    std::string encode_utf8(int unicode_codepoint)
    {
        std::string utf8_char;

        if (unicode_codepoint == 0)
        {
            // Be careful of this hitting when there is no offset. 
            // The codepoint would be 0, which is reserved for null and will cause problems.
            // The offset should also account for special character like delimiters.
            utf8_char.push_back(unicode_codepoint + OFFSET);
        }
        else
        {
            // Add the offset to the unicode_codepoint. This offset is used to avoid the reserved values at the beginning.
            unicode_codepoint += OFFSET;

            // Handling surrogates that are not legal unicode_codepoint values.
            // If the unicode_codepoint is the lowest part of the surrogate range or higher, we add the size of the surrogate range to it.
            // This will make it fall outside of the surrogate range. 
            // The decoding code must subtract the offset and add the surrogate range size back.
            if (unicode_codepoint >= 0xD800)
                unicode_codepoint += SURROGATE_RANGE_SIZE;

            // Encoding the unicode to UTF-8 following the standard rules.
            if (unicode_codepoint < 0x80)
            {
                // For unicode values less than 0x80, UTF-8 encoding is the same as the unicode value and is done with one byte.
                utf8_char.push_back(unicode_codepoint);
            }
            else if (unicode_codepoint < 0x800)
            {
                // For unicode values less than 0x800, the UTF-8 encoding is done with two bytes.
                // The first byte starts with '110' followed by the 5 most significant bits of the unicode value.
                // The second byte starts with '10' followed by the 6 least significant bits of the unicode value.
                utf8_char.push_back(0xC0 | (unicode_codepoint >> 6));
                utf8_char.push_back(0x80 | (unicode_codepoint & 0x3F));
            }
            else if (unicode_codepoint < 0x10000)
            {
                // For unicode values less than 0x10000, the UTF-8 encoding is done with three bytes.
                // The first byte starts with '1110' followed by the 4 most significant bits of the unicode value.
                // The remaining bytes start with '10' followed by the 6 next most significant bits of the unicode value.
                utf8_char.push_back(0xE0 | (unicode_codepoint >> 12));
                utf8_char.push_back(0x80 | ((unicode_codepoint >> 6) & 0x3F));
                utf8_char.push_back(0x80 | (unicode_codepoint & 0x3F));
            }
            else
            {
                // For unicode values greater than or equal to 0x10000, the UTF-8 encoding is done with four bytes.
                // The first byte starts with '11110' followed by the 3 most significant bits of the unicode value.
                // The remaining bytes start with '10' followed by the 6 next most significant bits of the unicode value.
                utf8_char.push_back(0xF0 | (unicode_codepoint >> 18));
                utf8_char.push_back(0x80 | ((unicode_codepoint >> 12) & 0x3F));
                utf8_char.push_back(0x80 | ((unicode_codepoint >> 6) & 0x3F));
                utf8_char.push_back(0x80 | (unicode_codepoint & 0x3F));
            }
        }
        return utf8_char;
    }

    int get_pixel_color_code(unsigned char *pixel_data)
    {
        int r = pixel_data[0] >> 2;
        int g = pixel_data[1] >> 2;
        int b = pixel_data[2] >> 2;
        return b << 10 | g << 5 | r;
    }

    void frame_to_string(Array3D *current_frame, Array3D *previous_frame, char *output)
    {
        static Array3D *cached_previous_frame = nullptr;
        static std::string cached_output;

        if (previous_frame == cached_previous_frame)
        {
            std::strncpy(output, cached_output.c_str(), cached_output.size());
            output[cached_output.size()] = '\0';
            return;
        }

        std::ostringstream ss;

        int total_pixels = current_frame->shape[0] * current_frame->shape[1];
        unsigned char *current_pixel = current_frame->data;
        unsigned char *previous_pixel = previous_frame ? previous_frame->data : nullptr;
        bool changes_made_for_previous_row = false;

        std::unordered_map<int, std::vector<std::pair<int, int>>> color_ranges_map;
        int range_current_color = -1;

        bool first_row = true;
        bool range_is_ongoing = false;

        for (int i = 0; i < total_pixels; ++i, current_pixel += current_frame->shape[2])
        {
            bool changed = true;
            if (previous_frame)
            {
                changed = memcmp(current_pixel, previous_pixel, current_frame->shape[2]) != 0;
                previous_pixel += previous_frame->shape[2];
            }

            int row_idx = i / current_frame->shape[1]; // Row index
            int col_idx = i % current_frame->shape[1]; // Column index

            if (col_idx == 0)
            {
                if (!color_ranges_map.empty())
                {
                    ss << encode_utf8(row_idx - 1);
                    changes_made_for_previous_row = true;
                }

                for (auto &color_ranges : color_ranges_map)
                {
                    // Write the color's unicode codepoint (SURROGATE_RANGE_SIZE may be added if this value is >= 0xD800)
                    ss << encode_utf8(color_ranges.first);
                    for (auto &range : color_ranges.second)
                    {
                        ss << encode_utf8(range.first) << encode_utf8(range.second);
                        //std::cout << range.first << " " << range.second << std::endl;
                    }
                    ss << '\x01'; // Delimiter A (end of color)
                }

                color_ranges_map.clear();

                if (changes_made_for_previous_row)
                {
                    ss << '\x02'; // Delimiter B (end of row)
                    first_row = false;
                }
                changes_made_for_previous_row = false;
                range_is_ongoing = false;
                range_current_color = -1;
            }

            int rgb_int = get_pixel_color_code(current_pixel);
            if (changed && rgb_int != range_current_color)
            {
                // The color changed, and the pixel changed since the last frame, so we need to add a new range
                color_ranges_map[rgb_int].push_back({col_idx, 1});
                range_current_color = rgb_int;
                range_is_ongoing = true;
            }
            else if (changed && color_ranges_map.find(range_current_color) != color_ranges_map.end() && range_is_ongoing)
            {
                color_ranges_map[range_current_color].back().second++;
            }
            else
            {
                range_is_ongoing = false;
                range_current_color = -1;
            }
        }

        // Handle the last row if necessary
        if (!color_ranges_map.empty())
        {
            ss << encode_utf8(current_frame->shape[0] - 1);
            for (auto &color_ranges : color_ranges_map)
            {
                // Write the color's unicode codepoint (SURROGATE_RANGE_SIZE may be added if this value is >= 0xD800)
                ss << encode_utf8(color_ranges.first);
                for (auto &range : color_ranges.second)
                {
                    ss << encode_utf8(range.first) << encode_utf8(range.second);
                }
                ss << '\x01'; // Delimiter A (end of color)
            }
            ss << '\x02'; // Delimiter B (end of row)
        }

        cached_previous_frame = previous_frame;
        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';
    }
}