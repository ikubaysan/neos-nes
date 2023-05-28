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
    const int OFFSET = 2;

    std::string encode_utf8(int unicode)
    {
        std::string color;
        if (unicode == 0)
        {
            color.push_back(0x1);
        }
        else
        {
            if (0xD800 <= unicode && unicode <= 0xDFFF)
            {
                if (unicode < 0xDC00)
                    unicode = 0xD7FF;
                else
                    unicode = 0xE000;
            }

            if (unicode < 0x80)
            {
                color.push_back(unicode);
            }
            else if (unicode < 0x800)
            {
                color.push_back(0xC0 | (unicode >> 6));
                color.push_back(0x80 | (unicode & 0x3F));
            }
            else if (unicode < 0x10000)
            {
                color.push_back(0xE0 | (unicode >> 12));
                color.push_back(0x80 | ((unicode >> 6) & 0x3F));
                color.push_back(0x80 | (unicode & 0x3F));
            }
            else
            {
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
        static Array3D *cached_last_frame = nullptr;
        static std::string cached_output;
        if (last_frame == cached_last_frame)
        {
            std::strncpy(output, cached_output.c_str(), cached_output.size());
            output[cached_output.size()] = '\0';
            return;
        }

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
                changed = memcmp(current_pixel, last_pixel, current_frame->shape[2]) != 0;
                last_pixel += last_frame->shape[2];
            }

            if (i % current_frame->shape[1] == 0 && i > 0)
            {
                ss << encode_utf8(row_index) << encode_utf8(2);
                row_index++;
            }

            if (changed)
            {
                int r = current_pixel[0] >> 2;
                int g = current_pixel[1] >> 2;
                int b = current_pixel[2] >> 2;
                int rgb_int = b << 10 | g << 5 | r;
                rgb_int += OFFSET;

                if (rgb_to_utf8_cache.count(rgb_int) == 0)
                {
                    rgb_to_utf8_cache[rgb_int] = encode_utf8(rgb_int);
                }

                if (last_color == rgb_to_utf8_cache[rgb_int] && same_color_start != -1)
                {
                    continue;
                }

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
                }

                same_color_start = i;
                last_color = rgb_to_utf8_cache[rgb_int];
                ss << last_color;
            }
        }

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
        }

        cached_output = ss.str();
        std::strncpy(output, cached_output.c_str(), cached_output.size());
        output[cached_output.size()] = '\0';
        cached_last_frame = last_frame;
    }
}
