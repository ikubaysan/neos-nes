#include <string>
#include <vector>
#include <sstream>
#include <iostream>
#include <tuple>

typedef std::tuple<int, int, int> Pixel;

extern "C" {
    std::string frame_to_string_common(std::vector<Pixel> frame, std::vector<bool> changed_pixels);
}

std::string frame_to_string_common(std::vector<Pixel> frame, std::vector<bool> changed_pixels) {
    std::string last_color;
    int same_color_start = -1;
    std::ostringstream message;
    int total_pixels = frame.size();

    for (int i = 0; i < total_pixels; i++) {
        Pixel pixel = frame[i];
        int r = std::get<0>(pixel) >> 2;
        int g = std::get<1>(pixel) >> 2;
        int b = std::get<2>(pixel) >> 2;
        
        int rgb_int = (b << 10) | (g << 5) | r;

        if (0xD800 <= rgb_int && rgb_int <= 0xDFFF) {
            std::cout << "Avoiding Unicode surrogate range" << std::endl;
            if (rgb_int < 0xDC00) {
                rgb_int = 0xD7FF;  // Maximum value just before the surrogate range
            } else {
                rgb_int = 0xE000;  // Minimum value just after the surrogate range
            }
        }
        // C++ does not have an equivalent to Python's chr function for getting a single character
        // string from a Unicode code point. So we use a workaround.
        std::string color(1, rgb_int <= 0xFF ? char(rgb_int) : '?'); 

        bool changed = (i < changed_pixels.size()) ? changed_pixels[i] : true;

        if (changed && color != last_color) {
            if (!last_color.empty() && same_color_start != -1) {
                message << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color;
            }
            same_color_start = i;
            last_color = color;
        } else if (!changed && same_color_start != -1) {
            message << same_color_start << "+" << i - 1 - same_color_start << "_" << last_color;
            same_color_start = -1;
            last_color = "";
        }

        if (i == total_pixels - 1 && same_color_start != -1) {
            message << same_color_start << "+" << i - same_color_start << "_" << last_color;
        }
    }
    return message.str();
}
