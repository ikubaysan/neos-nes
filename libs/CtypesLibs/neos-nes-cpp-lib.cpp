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
            // The range from 0xD800 to 0xDFFF is reserved for surrogate pairs in UTF-16 encoding.
            // Therefore, if our code falls within this range, we set it to either 0xD7FF or 0xE000.
            if (0xD800 <= unicode_codepoint && unicode_codepoint <= 0xDFFF)
            {
                if (unicode_codepoint < 0xDC00)
                    unicode_codepoint = 0xD7FF;
                else
                    unicode_codepoint = 0xE000;
            }

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

    void frame_to_string(Array3D *current_frame, Array3D *previous_frame, char *output)
    {
        //frame->shape[0] = width
        //frame->shape[1] = height
        //frame->shape[2] = RGB channels
        
        // std::cout << "width: " << current_frame->shape[1] << std::endl;
        // std::cout << "height: " << current_frame->shape[0] << std::endl;
        // std::cout << "channels: " << current_frame->shape[2] << std::endl;

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

        // Use a map to store color and its associated ranges
        std::unordered_map<std::string, std::vector<std::pair<int, int>>> color_ranges_map;
        std::string current_color;

        bool first_row = true;
        bool ongoing_range = false;

        // Iterate over each pixel
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

            // Check for the start of a new row
            if (col_idx == 0)
            {
                
                // Write the index of the previous row
                if (!color_ranges_map.empty())
                {
                    ss << encode_utf8(row_idx - 1);
                    changes_made_for_previous_row = true;
                }

                // Write out the color and its ranges for the previous row
                for (auto &color_ranges : color_ranges_map)
                {
                    ss << color_ranges.first;
                    for (auto &range : color_ranges.second)
                    {
                        ss << encode_utf8(range.first) << encode_utf8(range.second);
                    }
                    ss << '\x01'; // Delimiter A (end of color)
                }

                // Clear color_ranges_map
                color_ranges_map.clear();

                if (changes_made_for_previous_row)
                {
                    ss << '\x02'; // Delimiter B (end of row)
                    first_row = false;
                }
                changes_made_for_previous_row = false;
                ongoing_range = false;
            }

            // Only want ranges of changed pixels.
            if (changed)
            {
                // Get color code
                int r = current_pixel[0] >> 2;
                int g = current_pixel[1] >> 2;
                int b = current_pixel[2] >> 2;
                int rgb_int = b << 10 | g << 5 | r;
                std::string color = encode_utf8(rgb_int);

                // Start a new range
                color_ranges_map[color].push_back({col_idx, 1});
                current_color = color;
                ongoing_range = true;
            }
            else if (changed && color_ranges_map.find(current_color) != color_ranges_map.end() && ongoing_range)
            {
                // Extend the ongoing range
                color_ranges_map[current_color].back().second++;
            }
            else
            {
                // No change and no ongoing range
                ongoing_range = false;
            }
        }

        // // Write out the color and its ranges for the final row
        if (!color_ranges_map.empty())
        {
            // We need to write colors for the final row, whose index is total rows - 1
            ss << encode_utf8(current_frame->shape[0] - 1);
            changes_made_for_previous_row = true;
        }

        for (auto &color_ranges : color_ranges_map)
        {
            ss << color_ranges.first;
            for (auto &range : color_ranges.second)
            {
                ss << encode_utf8(range.first) << encode_utf8(range.second);
            }
            ss << '\x01'; // Delimiter A (end of color)
        }

        if (changes_made_for_previous_row)
            ss << '\x02'; // Delimiter B (end of row)
        changes_made_for_previous_row = false;
        ongoing_range = false;

        // Cache the output
        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';
        cached_previous_frame = previous_frame;
    }
}