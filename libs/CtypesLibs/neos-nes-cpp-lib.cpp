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

    std::string encode_utf8(int unicode)
    {
        std::string color;

        if (unicode == 0)
        {
            // Be careful of this hitting when there is no offset. 
            // The codepoint would be 0, which is reserved for null and will cause problems.
            color.push_back(OFFSET);
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

    void frame_to_string(Array3D *current_frame, Array3D *previous_frame, char *output)
    {
        /*
            frame->shape[0] = width
            frame->shape[1] = height
            frame->shape[2] = RGB channels
        */

        // std::cout << "width: " << current_frame->shape[1] << std::endl;
        // std::cout << "height: " << current_frame->shape[0] << std::endl;
        // std::cout << "channels: " << current_frame->shape[2] << std::endl;
        // std::cout << "hello!!!" << std::endl;
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


        int i_since_last_row = 0;
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

            //if (first_row) std::cout << "Row: " << row_idx << "Column:" << col_idx << std::endl;

            // std::cout << row_idx << " " << col_idx << std::endl;
            //  These are correct

            // Check for the start of a new row
            if (col_idx == 0)
            {
                
                // Write the index of the previous row
                if (!color_ranges_map.empty())
                {
                    ss << encode_utf8(row_idx - 1);
                    changes_made_for_previous_row = true;
                    //if (first_row) {std::cout << "Row: " << row_idx - 1 << std::endl;}

                    // Print the contents of color_ranges_map
                    // if (first_row)
                    // {
                    //     std::cout << "printing color_ranges_map" << std::endl;
                    //     for (const auto &color_ranges : color_ranges_map)
                    //     {
                    //         std::string color = color_ranges.first;
                    //         const std::vector<std::pair<int, int>> &ranges = color_ranges.second;
                    //         std::cout << "Color: " << color << std::endl;
                    //         std::cout << color_ranges.first << std::endl;
                    //         for (auto &range : color_ranges.second)
                    //         {
                    //             std::cout << range.first << " " << range.second << std::endl;
                    //         }
                    //     }
                    // }
                }

                // Write out the color and its ranges for the previous row
                for (auto &color_ranges : color_ranges_map)
                {
                    ss << color_ranges.first;
                    if (first_row && !color_ranges_map.empty())
                    {
                        //std::cout << color_ranges.first << std::endl;
                    }
                    for (auto &range : color_ranges.second)
                    {
                        // std::cout << range.first << " " << range.second << std::endl;
                        //   These are correct
                        ss << encode_utf8(range.first) << encode_utf8(range.second);
                        if (first_row && !color_ranges_map.empty())
                        {
                            //std::cout << color_ranges.first << " " << range.first << " " << range.second << std::endl;
                        }
                    }
                    ss << '\x11'; // Delimiter A (end of color)
                }

                // Clear color_ranges_map
                color_ranges_map.clear();

                if (changes_made_for_previous_row)
                {
                    ss << '\x12'; // Delimiter B (end of row)
                    first_row = false;
                }
                changes_made_for_previous_row = false;
                ongoing_range = false;
                //std::cout << "i_since_last_row: " << i_since_last_row << std::endl;
                i_since_last_row = 0;
            }
            i_since_last_row++;
            

            // Only want ranges of changed pixels.
            if (changed && !ongoing_range)
            {
                // Get color code
                int r = current_pixel[0] >> 2;
                int g = current_pixel[1] >> 2;
                int b = current_pixel[2] >> 2;
                int rgb_int = b << 10 | g << 5 | r;
                // for testing
                //rgb_int = 30;
                std::string color = encode_utf8(rgb_int);

                // Start a new range
                color_ranges_map[color].push_back({col_idx, 1});
                // std::cout << col_idx << std::endl;
                current_color = color;
                ongoing_range = true;
            }
            else if (changed && color_ranges_map.find(current_color) != color_ranges_map.end() && ongoing_range)
            {
                // Extend the previous range
                color_ranges_map[current_color].back().second++;
            }
            else
            {
                // No change and no ongoing range
                ongoing_range = false;
            }
        }

        // // Write out the color and its ranges for the final row
        // if (!color_ranges_map.empty())
        // {
        //     ss << encode_utf8(current_frame->shape[0] - 1);
        //     changes_made_for_previous_row = true;
        // }

        // for (auto &color_ranges : color_ranges_map)
        // {
        //     ss << color_ranges.first;
        //     for (auto &range : color_ranges.second)
        //     {
        //         ss << encode_utf8(range.first) << encode_utf8(range.second);
        //     }
        //     ss << '\x11'; // Delimiter A (end of color)
        // }

        // if (changes_made_for_previous_row)
        //     ss << '\x12'; // Delimiter B (end of row)

        // Cache the output
        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';

        cached_previous_frame = previous_frame;
    }
}