# neos-nes
NES emulation for NeosVR.

Frame data and controller inputs are transferred via websocket.

## Getting started:

Install 64-bit Python 3

Install GNU C++ Compiler - MinGW-w64 

Download the online installer from here:
https://github.com/niXman/mingw-builds-binaries

* Choose 64-bit architecture
* Choose win32 thread model

`pip3 install -r requirements.txt`

`g++ -shared -o neos-nes-cpp-lib.so neos-nes-cpp-lib.cpp`

If the .so file is not found, you may need to install or repair your x64 Microsoft Visual C++ Redistributable packages.
Go here and download VS_redist.x64.exe:
https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170

# How it works
## Message format

Neos/Logix does not support reading bytes via websocket, only strings. 
Logix also does not support reading bits from a character's bytes. 

We need to use Logix's "String to UTF" node which takes a character 
of a string by index and returns its unicode codepoint.

We reserve 2 delimiters:
* Delimiter A: end of color
* Delimiter B: end of row

Messages are formatted as such:

```
- row 0
    - color 0
        - range 0 column start
        - range 0 span
        - range 1 column start
        - range 1 span
        - delim A
    - color 1
        - range 0 column start
        - range 0 span
        - range 1 column start
        - range 1 span
        - delim A
    - delim B
- row 1
    - color 0
        - range 0 column start
        - range 0 span
        - range 1 column start
        - range 1 span
        - delim A
    - color 1
        - range 0 column start
        - range 0 span
        - range 1 column start
        - range 1 span
        - delim A
    - delim B

```

A range's start and span are both 3 digits, and are combined into a single UTF8 character.


When decoding the messages in python/logix to display our frame, we need to iterate over the characters of the message and:
* Read the first character, which will be a row number
* Next character will be a color. Decode the color to get the RGB values
* After a color character, we read a range's start column as a character, and the next character will be the span. Apply the color to the pixels in that range for the row, and then the next character will be another range's start column UNLESS it's delim A, which indicates there are no more ranges of columns of pixels to apply this color to in this row.
* If the character was delim A, then we need to check if the next character is delim B. If so, then we are done applying all the colors to this row. But if not, then the character is a color, and the next characters are ranges of columns we need to apply this color to for this row, like before.
* Once we're done applying all the colors to this row, then the next character will be a different row index, and the cycle repeats.


## Running tests

Run a specific test:

`python -m pytest -k test_smb_title_demo_messages_artifacting_debug test_DisplayStrategy.py`