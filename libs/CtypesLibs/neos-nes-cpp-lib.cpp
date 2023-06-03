#include <string>
#include <vector>
#include <cstring>
#include <sstream>
#include <iostream>
#include <unordered_map>
#include <unordered_set>

struct pair_hash
{
    template <class T1, class T2>
    std::size_t operator()(const std::pair<T1, T2> &p) const
    {
        auto h1 = std::hash<T1>{}(p.first);
        auto h2 = std::hash<T2>{}(p.second);

        return h1 ^ h2;
    }
};

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

    std::pair<int, int> get_pixel_color_codes(unsigned char *pixel_data)
    {
        // Had to switch r and b so the colors appear correctly
        int b = pixel_data[0];
        int g = pixel_data[1];
        int r = pixel_data[2];

        // Combine R and G values into one integer and B into another
        int rg = r * 1000 + g; // Assuming r and g are each < 1000
        int b_val = b;

        return std::make_pair(rg, b_val);
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

    void frame_to_string(Array3D *current_frame, Array3D *previous_frame, char *output)
    {
        // Find ranges of identical rows
        std::unordered_map<int, int> identical_rows;
        find_identical_rows(current_frame, &identical_rows);

        static Array3D *cached_previous_frame = nullptr;
        static std::string cached_output;

        // Keep track of the rows where color_changed_at_current_pixel was true
        static bool use_color_changed_rows = false;
        static std::unordered_set<int> color_changed_rows;
        std::unordered_set<int> new_color_changed_rows;

        if (previous_frame != nullptr && previous_frame == cached_previous_frame)
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

        std::unordered_map<std::pair<int, int>, std::vector<std::pair<int, int>>, pair_hash> color_ranges_map;
        std::pair<int, int> range_current_color = {-1, -1};

        bool first_row = true;
        bool range_is_ongoing = false;

        int skip_to_row_index = -1;

        for (int i = 0; i < total_pixels; ++i, current_pixel += current_frame->shape[2])
        {
            bool color_changed_at_current_pixel = false;
            if (previous_frame)
            {
                for (int j = 0; j < current_frame->shape[2]; j++)
                {
                    if (current_pixel[j] != previous_pixel[j])
                    {
                        color_changed_at_current_pixel = true;
                        break;
                    }
                }
                previous_pixel += previous_frame->shape[2];
            }
            else
            {
                // previous_frame is nullptr, meaning a full frame update was sent, so we consider all pixels changed
                color_changed_at_current_pixel = true;
            }

            int row_idx = i / current_frame->shape[1]; // Row index
            int col_idx = i % current_frame->shape[1]; // Column index

            // If color_changed_at_current_pixel is true for this pixel, add its row to the new set
            if (color_changed_at_current_pixel)
            {
                new_color_changed_rows.insert(row_idx);
            }

            // Check if color_changed_at_current_pixel was true once at this row during the previous frame
            // If so, then we need to update the entire row. This is unfortunate and I probably don't need to send the entire row,
            // but this was a way I could guarantee no artifacting.
            // TODO: find a way to not send entire row. Maybe just neighboring pixels?
            if (use_color_changed_rows && !color_changed_at_current_pixel && color_changed_rows.count(row_idx) > 0)
            {
                color_changed_at_current_pixel = true;
            }

            if (skip_to_row_index != -1)
            {
                if (row_idx < skip_to_row_index)
                {
                    continue;
                }
                else
                {
                    skip_to_row_index = -1;
                }
            }

            if (col_idx == 0)
            {
                if (!color_ranges_map.empty())
                {
                    changes_made_for_previous_row = true;
                    if (identical_rows.find(row_idx - 1) != identical_rows.end())
                    {
                        int combined_row_number = (row_idx - 1) * 1000 + (identical_rows[row_idx - 1] + 1);
                        skip_to_row_index = row_idx + identical_rows[row_idx - 1];
                        ss << encode_utf8(combined_row_number);
                    }
                    else
                    {
                        ss << encode_utf8((row_idx - 1) * 1000 + 1);
                    }
                }

                for (auto &color_ranges : color_ranges_map)
                {
                    ss << encode_utf8(color_ranges.first.first);
                    ss << encode_utf8(color_ranges.first.second);
                    for (auto &range : color_ranges.second)
                    {
                        int combined = range.first * 1000 + range.second;
                        ss << encode_utf8(combined);
                    }
                    ss << '\x01';
                }

                color_ranges_map.clear();

                if (changes_made_for_previous_row)
                {
                    ss << '\x02';
                    first_row = false;
                }
                changes_made_for_previous_row = false;
                range_is_ongoing = false;
                range_current_color = {-1, -1};
            }

            std::pair<int, int> rgb_int = get_pixel_color_codes(current_pixel);
            if (color_changed_at_current_pixel && rgb_int != range_current_color)
            {
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
                range_current_color = {-1, -1};
            }
        }

        // Handle the last row if necessary
        if (!color_ranges_map.empty())
        {
            // Write the index of the final row, which is the total amount of rows - 1
            int row_idx = current_frame->shape[0] - 1;
            ss << encode_utf8((row_idx - 1) * 1000 + (identical_rows[row_idx - 1] + 1));

            for (auto &color_ranges : color_ranges_map)
            {
                ss << encode_utf8(color_ranges.first.first);
                ss << encode_utf8(color_ranges.first.second);
                for (auto &range : color_ranges.second)
                {
                    int combined = range.first * 1000 + range.second;
                    ss << encode_utf8(combined);
                }
                ss << '\x01';
            }
            ss << '\x02';
        }

        // At the end of the function, assign new_color_changed_rows to color_changed_rows
        color_changed_rows = new_color_changed_rows;
        // We only need to update entire rows every other frame; it still looks fine.
        use_color_changed_rows == true ? use_color_changed_rows = false : use_color_changed_rows = true;

        cached_previous_frame = previous_frame;
        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';
    }
}