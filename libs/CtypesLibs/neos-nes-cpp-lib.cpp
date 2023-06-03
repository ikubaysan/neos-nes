#include <string>
#include <vector>
#include <cstring>
#include <sstream>
#include <iostream>
#include <unordered_map>
#include <unordered_set>

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

    typedef std::vector<std::vector<int>> FrameRGBInts; // NEW: For storing rgb_int of each pixel

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

    /*
        get_pixel_color_code() is used to compute a unique integer value for a pixel's color based on its RGB values.
        It takes a pointer to an array of three unsigned chars, which represent the red, green, and blue values of the pixel color.

        It first shifts the RGB values to the right by 2 bits, effectively dividing them by 4 and thereby reducing the
        precision from 256 possible values to 64. This is done to compress the color data so it can fit into a single integer.

        The resulting RGB values are then packed into a single integer, with blue occupying the highest order bits,
        green the next highest, and red the lowest. This is done by shifting the blue value left by 10 bits and the green value left
        by 5 bits, then bitwise OR-ing these with the red value.

        The output is a single integer that is a unique representation of the pixel's color, taking into account the lower
        precision of the RGB values.

        Parameters:
            pixel_data - pointer to an array of three unsigned chars, representing the RGB values of a pixel color.
        Return:
            An integer that uniquely represents the pixel's color.
     */
    int get_pixel_color_code(unsigned char *pixel_data)
    {
        int r = pixel_data[0] >> 2;
        int g = pixel_data[1] >> 2;
        int b = pixel_data[2] >> 2;
        return b << 10 | g << 5 | r;
    }

    void find_identical_rows(Array3D *current_frame, std::unordered_map<int, int> *identical_rows)
    {
        // Calculate the size of a row in bytes
        int row_size_bytes = current_frame->shape[1] * current_frame->shape[2];
        std::vector<unsigned char> row_data(row_size_bytes);
        std::vector<unsigned char> prev_row_data(row_size_bytes);

        int identical_row_start = -1;
        int identical_row_count = 0;

        for (int row_idx = 1; row_idx < current_frame->shape[0]; ++row_idx)
        {
            std::copy(current_frame->data + row_idx * row_size_bytes,
                      current_frame->data + (row_idx + 1) * row_size_bytes,
                      row_data.begin());

            std::copy(current_frame->data + (row_idx - 1) * row_size_bytes,
                      current_frame->data + row_idx * row_size_bytes,
                      prev_row_data.begin());

            if (row_data == prev_row_data)
            {
                // The row is identical to the previous one
                if (identical_row_start == -1)
                {
                    identical_row_start = row_idx - 1;
                }
                identical_row_count++;
            }
            else
            {
                // The row is not identical to the previous one
                if (identical_row_start != -1)
                {
                    // We have just left a range of identical rows
                    (*identical_rows)[identical_row_start] = identical_row_count;

                    identical_row_start = -1;
                    identical_row_count = 0;
                }
            }
        }

        if (identical_row_start != -1)
        {
            // Last row(s) were part of a range of identical rows
            (*identical_rows)[identical_row_start] = identical_row_count;
        }
    }

    // Function to generate RGBInts for a given frame
    void create_frame_rgb_ints(Array3D *frame, FrameRGBInts &frame_rgb_ints, const FrameRGBInts *compare_frame_rgb_ints = nullptr, std::unordered_set<int> *changed_rows = nullptr)
    {
        // Iterate over each row and column of the frame
        for (int i = 0; i < frame->shape[0]; ++i)
        {
            for (int j = 0; j < frame->shape[1]; ++j)
            {
                // Get the pixel data (RGB values) of the current pixel
                unsigned char *pixel_data = frame->data + (i * frame->shape[1] + j) * frame->shape[2];

                // Convert the pixel data to an RGB integer value and store it in the frame_rgb_ints vector
                frame_rgb_ints[i][j] = get_pixel_color_code(pixel_data);

                // If a comparison frame_rgb_ints and a changed_rows set are provided
                if (compare_frame_rgb_ints && changed_rows)
                {
                    // If the color at this pixel is different
                    if (frame_rgb_ints[i][j] != (*compare_frame_rgb_ints)[i][j])
                    {
                        // Add the row index to the changed_rows set
                        changed_rows->insert(i);
                    }
                }
            }
        }
    }

    void frame_to_string(Array3D *current_frame_unmodified, Array3D *previous_frame_unmodified, char *output)
    {
        // Create RGBInts for the current frame
        FrameRGBInts current_frame_rgb_ints(current_frame_unmodified->shape[0], std::vector<int>(current_frame_unmodified->shape[1]));
        create_frame_rgb_ints(current_frame_unmodified, current_frame_rgb_ints);

        FrameRGBInts previous_frame_rgb_ints;

        // Define a set to store rows with at least one changed pixel
        std::unordered_set<int> changed_rows;

        // Find ranges of identical rows
        std::unordered_map<int, int> identical_rows;
        find_identical_rows(current_frame_unmodified, &identical_rows);

        static Array3D *cached_previous_frame_unmodified = nullptr;
        static Array3D *current_frame_modified = nullptr;

        static std::string cached_output;

        // If the current frame is identical to the previous frame, we can reuse the previous output
        if (cached_previous_frame_unmodified != nullptr && cached_previous_frame_unmodified == previous_frame_unmodified)
        {
            std::strncpy(output, cached_output.c_str(), cached_output.size());
            output[cached_output.size()] = '\0';
            return;
        }

        if (previous_frame_unmodified)
        {
            previous_frame_rgb_ints.resize(previous_frame_unmodified->shape[0], std::vector<int>(previous_frame_unmodified->shape[1]));
            create_frame_rgb_ints(previous_frame_unmodified, previous_frame_rgb_ints, &current_frame_rgb_ints, &changed_rows);
        }

        std::ostringstream ss;

        int total_pixels = current_frame_unmodified->shape[0] * current_frame_unmodified->shape[1];
        unsigned char *current_pixel = current_frame_unmodified->data;
        unsigned char *previous_pixel = previous_frame_unmodified ? previous_frame_unmodified->data : nullptr;
        bool changes_made_for_previous_row = false;

        std::unordered_map<int, std::vector<std::pair<int, int>>> color_ranges_map;
        int range_current_color = -1;

        bool first_row = true;
        bool range_is_ongoing = false;

        int skip_to_row_index = -1;
        // std::cout << "hello" << std::endl;

        for (int i = 0; i < total_pixels; ++i, current_pixel += current_frame_unmodified->shape[2])
        {
            int row_idx = i / current_frame_unmodified->shape[1]; // Row index
            int col_idx = i % current_frame_unmodified->shape[1]; // Column index
            bool color_changed_at_current_pixel = true;
            if (previous_frame_unmodified)
            {
                // If the current row is in the changed_rows set, then we will consider all pixels in the row to have changed (to prevent artifacting)
                if (changed_rows.find(row_idx) != changed_rows.end())
                {
                    color_changed_at_current_pixel = true;
                }
                else
                {
                    color_changed_at_current_pixel = false;
                }

                // If you don't care about artifacting and want more speed, you can just do this:
                //color_changed_at_current_pixel = current_frame_rgb_ints[row_idx][col_idx] != previous_frame_rgb_ints[row_idx][col_idx];
            }

            if (skip_to_row_index != -1)
            {
                if (row_idx < skip_to_row_index)
                {
                    continue;
                }
                else
                {
                    // We have reached the row we were skipping to, so reset the skip_to_row_index
                    skip_to_row_index = -1;
                }
            }

            if (col_idx == 0)
            {
                // We are at the start of a new row
                if (!color_ranges_map.empty())
                {
                    // Write the row index of the previous row, which we have finished evaluating.
                    // But if the row index is the start of repeated rows, then account for that.
                    changes_made_for_previous_row = true;
                    if (identical_rows.find(row_idx - 1) != identical_rows.end())
                    {
                        int combined_row_number = (row_idx - 1) * 1000 + (identical_rows[row_idx - 1] + 1);
                        skip_to_row_index = row_idx + identical_rows[row_idx - 1];
                        ss << encode_utf8(combined_row_number);
                        // std::cout << "Set skip_to_row_index to " << skip_to_row_index << " for row " << row_idx - 1 << ". start index: " << row_idx - 1 << " count: " << identical_rows[row_idx - 1] << std::endl;
                    }
                    else
                    {
                        // ss << encode_utf8((row_idx - 1) * 1000); // Add 3 zeros if the row isn't a start of a range of identical rows
                        ss << encode_utf8((row_idx - 1) * 1000 + 1);
                        // std::cout << "Row " << row_idx - 1 << " is not a start of a range of identical rows" << std::endl;
                    }
                }

                for (auto &color_ranges : color_ranges_map)
                {
                    // Write the color's unicode codepoint (SURROGATE_RANGE_SIZE may be added if this value is >= 0xD800)
                    ss << encode_utf8(color_ranges.first);
                    for (auto &range : color_ranges.second)
                    {
                        int combined = range.first * 1000 + range.second; // Combine start and span into a single integer
                        // std::cout << range.first << " " << range.second << " " << combined << std::endl;
                        ss << encode_utf8(combined);
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
            if (color_changed_at_current_pixel && rgb_int != range_current_color)
            {
                // The color changed, and the pixel changed since the last frame, so we need to add a new range for this row starting at this column
                color_ranges_map[rgb_int].push_back({col_idx, 1});
                range_current_color = rgb_int;
                range_is_ongoing = true;
            }
            else if (color_changed_at_current_pixel && color_ranges_map.find(range_current_color) != color_ranges_map.end() && range_is_ongoing)
            {
                color_ranges_map[range_current_color].back().second++;
            }
            else
            {
                range_is_ongoing = false;
                range_current_color = -1;
            }
        }

        // TODO: handle last row

        cached_previous_frame_unmodified = current_frame_unmodified;
        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';

        // After finishing the frame, update the previous RGBInts
        previous_frame_rgb_ints = std::move(current_frame_rgb_ints);
    }
}