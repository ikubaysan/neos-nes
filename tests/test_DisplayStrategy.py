import pytest
import numpy as np
import random
import time
import cv2
from Helpers.GeneralHelpers import *
from libs.DisplayStrategies.AdvancedDisplayStrategy import *
from libs.CtypesLibs.CPPFrameToString import FrameToString

HOST = '10.0.0.147'
PORT = 9001

@pytest.fixture
def advanced_display_strategy():
    display_strategy = AdvancedDisplayStrategy(host=HOST, port=PORT, scale_percentage=100)
    return display_strategy

@pytest.fixture
def frame_to_string():
    frame_to_string = FrameToString()
    return frame_to_string


def message_to_color_dictionary(message, offset):
    # Initialize output dictionary
    color_dict = {}

    # End of color and row delimiters
    delim_a = chr(1)
    delim_b = chr(2)

    i = 0  # Initialize index for looping through the message

    while i < len(message):

        # this is affected by current_state[10:50, 100:150], will start at 10 in this case
        row_idx = ord(message[i]) - offset
        i += 1

        color_dict[row_idx] = {}

        while i < len(message) and message[i] != delim_b:
            color_codepoint = utf8_to_rgb(message[i])
            i += 1

            color_dict[row_idx][color_codepoint] = []

            while i < len(message) and message[i] != delim_a:
                range_start = ord(message[i]) - offset
                i += 1
                range_span = ord(message[i]) - offset
                i += 1
                color_dict[row_idx][color_codepoint].append([range_start, range_span])

            i += 1  # Skip delim_a

        i += 1  # Skip delim_b

    return color_dict




def test_update_canvas_1(advanced_display_strategy: AdvancedDisplayStrategy):
    OFFSET = advanced_display_strategy.OFFSET

    delim_a = chr(1) # end of color
    delim_b = chr(2) # end of row

    message = ""

    # row 0
    message += chr(0 + OFFSET)
    # color 0
    message += rgb_to_utf8(r=12, g=5, b=50, offset=OFFSET)

    # range 0 column start
    message += chr(3 + OFFSET)
    # range 0 span
    message += chr(2 + OFFSET)

    # range 1 column start
    message += chr(13 + OFFSET)
    # range 1 span
    message += chr(4 + OFFSET)

    # delim a <?>
    message += delim_a

    # Done applying color 0 to this row. Are there any other colors?
    # yes.
    # color 1
    message += rgb_to_utf8(r=120, g=50, b=250, offset=OFFSET)
    # range 0 column start
    message += chr(23 + OFFSET)
    # range 0 span
    message += chr(5 + OFFSET)

    # range 1 column start
    message += chr(33 + OFFSET)
    # range 1 span
    message += chr(2 + OFFSET)

    message += delim_a
    # Done applying color 0 to this row. Are there any other colors?
    # no
    message += delim_b

    update_canvas(message=message, canvas=advanced_display_strategy.canvas, offset=OFFSET)
    advanced_display_strategy.display()
    return


def test_update_canvas_2(advanced_display_strategy: AdvancedDisplayStrategy):
    OFFSET = advanced_display_strategy.OFFSET
    FRAME_WIDTH = DEFAULT_FRAME_WIDTH
    FRAME_HEIGHT = DEFAULT_FRAME_HEIGHT

    delim_a = chr(1)  # end of color
    delim_b = chr(2)  # end of row
    message = ""

    data = {}

    for row in range(FRAME_HEIGHT):
        # Append row
        message += chr(row + OFFSET)

        # Randomly select the number of colors for this row
        num_colors = random.randint(1, 3)
        data[row] = num_colors

        for _ in range(num_colors):
            # Randomly select RGB values
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)

            # Append color
            message += rgb_to_utf8(r, g, b, offset=OFFSET)

            # Randomly select the number of color ranges for this color
            num_ranges = random.randint(1, 3)

            for _ in range(num_ranges):
                # Randomly select start of color range
                start = random.randint(0, FRAME_WIDTH - 2)

                # Randomly select range span. It must not exceed the amount of columns from the start
                span = random.randint(1, FRAME_WIDTH - start - 1)

                # Append range start and span
                message += chr(start + OFFSET)
                message += chr(span + OFFSET)

            # Append end of color delimiter
            message += delim_a

        # Append end of row delimiter
        message += delim_b

    # Update and display canvas
    advanced_display_strategy.update_canvas(message=message)
    advanced_display_strategy.display()
    time.sleep(3)
    return



def test_update_canvas_from_cpp(frame_to_string: FrameToString, advanced_display_strategy: AdvancedDisplayStrategy):
    # Initialize the arrays to be all the same color, say, bright red.
    last_state = np.full((250, 250, 3), [0, 0, 0], dtype=np.uint8)  # Initialize last_state with black color

    current_state = np.copy(last_state)  # Create a copy of last_state as current_state

    # Modify specific regions in current_state

    current_state[10:50, 100:150] = [94, 13, 73]  # Change row 10 to 49 and column 100 to 149.
    current_state[100:150, 50:100] = [23, 37, 201]  # Change row 100 to 149 and column 50 to 99.
    current_state[200:250, 150:200] = [19, 120, 9]  # Change row 200 to 249 and column 150 to 199.
    current_state[125:175, 200:250] = [190, 37, 59]  # Change row 200 to 249 and column 200 to 249.
    current_state[0:50, 0:50] = [75, 150, 30]  # Change row 0 to 49 and column 0 to 49.

    # Since the last state, we added colors, which are in the current state.

    cv2.imshow("current_state", current_state)
    current_state_constructed_by_message = last_state

    message = frame_to_string.get_string(current_state, last_state)

    message_to_codepoints = [(ord(utf8char) - advanced_display_strategy.OFFSET) for utf8char in message]

    message_len = len(message)
    result_dict = message_to_color_dictionary(message=message, offset=16)

    advanced_display_strategy.update_canvas(message=message,
                                            canvas=current_state_constructed_by_message)
    cv2.imshow("Current state constructed by message", current_state_constructed_by_message)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return




def test_update_canvas_from_hardcoded_message(frame_to_string: FrameToString, advanced_display_strategy: AdvancedDisplayStrategy):
    # Initialize the arrays to be all the same color, say, bright red.
    current_state_constructed_by_message = np.full((250, 250, 3), [0, 0, 0], dtype=np.uint8)  # Initialize last_state with black color
    message = """)䕏ú+䕏,䕏)-䕏9.䕏I2뛌W3뛌fﱪ4뛌v%5뛌56뛌A7ﱪVª뛌Q¦8ﱪf뛌¶b9뛌Æu:ጉêõý뛌Öâï;ጉ-:û뛌"æñÿ<ጉ+=K¥뛌1ö=ጉ%-;M[µ뛌A>ጉ,5=L]lÅ뛌 /P?ጉ<\|EMmÕ뛌&0?`@ጉMmU]}å뛌6?Aጉ]}emõ뛌FOBጉm­u}뛌V_Cጉ}®뛌fo·v¥µ½Dጉ뛌v§·Ç%¥­µ¼ÅÍEጉ뛌·Ç×5¥­µ½ÅÌÕÝFጉ®뛌 Ç×çE«µ½ÅÌÕÜåìGጉ¼ìþ뛌¦¿×çï÷U°ÅÍÕÜåõûHጉÌî뛌¶ÃÏç÷eÀÕÝåëõüIጉÝþuÑåíõû뛌ÆÕ÷Jጉí%-áõý뛌'ÖçKጉ-=ý%(5뛌7æïLጉ-=M%(E¥뛌öÿMጉ<M]-58Uµ뛌?NጉL]-=EHemÅ뛌OOጉ[m<LUXu}Õ뛌&0`PL\e}å뛌6@pQጉ^nP[kuõ뛌FRጉn~`k{¥­뛌VSጉ}뛌fqz¡­µ½Tጉ¦¾ÆÎ뛌v% ±Uጉ¬¶ÎÖÞ뛌5¢°ÂVጉ¬¼ÆÞæî뛌E¢²ÀÒWጉ»ËÖîöþ뛌¦U³ÃÐãX뛌¶eY뛌ÆuZ뛌Ö[뛌æ\뛌ö¥]ጉ"2BMZr¢µ뛌*7GRgw^ጉ(3CS]k£³Å뛌!,9GWaw©_ጉ8CScm{£³ÃÕ뛌&1<IWgq©¹`ጉITdt}¤´ÄÔå뛌6@Xgw§¸ÈaጉYdt´ÄÔäõ뛌FPhw§·ÈØbጉu­ÅÕåõ뛌V_·cጉ¥½Õåõ뛌foÇ­d뛌v×%½ጉ¥µÍåõe뛌ç5¥­µ½ÅÍÕÝíõýጉ%f%-5E¥­µ½ÅÍÕÝåíý뛌÷g%-5=EUµ½ÅÍÕÝåíõý뛌¦¯h%-5=EMUeÅÍÕÝåíõý뛌¶¿i-5=EMU]euÕÝåíõý뛌'ÆÏj%-=EMU]emuåíõý뛌7Ößk%-5=MU]emu}õý뛌Gæïl%-5=EM]emu}¥뛌Wöÿm%-5=EMU]mu}¥µ뛌gnጉ®¶%-5=EMU]em}¥Å뛌Owoጉ¿Æ5=EMU]emu}¥­µÕ뛌&/_pጉÖEMU]emu}¥­µ½ÅÑå뛌6?o¯qጉæU]emu}­´½ÄÍÕãõ뛌FO§¯¿rጉÆÖôemu}¥­½ÃÍÓÝå뛌V_·¿Ïs뛌foÇÏßûu}¤­µ½ÍÔÝäíõt뛌v¯×ßï%¥­µ½ÅÍÝåíõýጉuጉ%Åõ5¥­µ½ÍÕÝíý뛌¿çïÿv뛌/÷%)E¥­µÅÍÝåíýጉ5Õwጉ%Eå-5=Uµ½ÅÕÝíõý뛌¦¯xጉ%5U-=EMeÅÍÕåíõý뛌¶¿yጉ]-5=EMUeuÕÝåõý뛌'ÆÏzጉm%-=EMU]euåíõ뛌7Öß{뛌Gæï%-5=MU]emu}õý|%-5=EM]emu}¥뛌Wöÿ}%5=EMU]mu}¥µ뛌g~%-5EMU]em}¥­µÅ뛌wጉÍ5=EMU]em}¥µÅÕ뛌&/ጉÝEMU]emu}¥­µÅÕå뛌6?ጉíU]emu}­µ½ÅÕåõ뛌FO§¯ጉýemu}¬½ÄÍÕäô뛌V_·¿뛌foÇÏu}¥­¼ÍÔÝåôጉÎæ뛌v×ß%¥­µ½ËÝãíõጉ&Þö뛌çï#-5¥­µ½ÅÍÛíóýጉ&6í#3=E¥­µ½ÅÍÕÝáêý뛌÷ÿጉ5E¶¾ÆÎÖÞæîý뛌¦%)29BMU°ñጉ%.6EU^ÆÎÖÞæîöþ뛌¶ (9IXeÀጉ.4>FTdnÖÞæîöþ뛌Æ(08JZhuÐጉ,>DNVdt~æîöþ뛌Ö"8@HZjxàጉ&.;NS^fs뛌æ3HPXk{ﱪ¦ú뛌¡öﱪ¶²Å뛌ﱪÕ'ﱪ|µÅÍÛä뛌x¦«·»ÇÏÓ×ßﱪ¹Éá뛌£§¶ÁÆÑÖÞçóﱪ¼ÊÚò뛌¡¦«¯³·ÆÌÑÖÜáæîô÷ûÿ뛌¦­±·ËÖáæñöﱪª¯½ÄÝíü뛌#¶½ÁËÏÓÛæêñöúﱪº¿íýﱪ%ÈÏý뛌"'+/3ÆÑÚãçëöﱪ5ÙÞåëôü뛌!&.7C×Üï÷ﱪ%=KTì뛌'+16?CGOè©𐀏ùﱪìጉèªጉ¯÷ﱪ+=DU[mý𐀏(/7?PX^cg«ጉ¾ﱪqu𐀏&+7;?GNS_gksw¬𐀏)6;FKW^cnv{ﱪጉÎ­𐀏9FKV[`~ﱪ.dluጉ&Þ®𐀏IV_fqv~¤§ﱪ>\mጉ6î¯𐀏Yfov{§«¯³·ﱪNጉFþ°ﱪm¥µÍ𐀏gv°·»¿ÃÇW\±ﱪl뛌hጉ²ጉ.³ጉ>´ጉNµጉ^¶ጉn·ጉ~¸ጉ¹ጉº®»ﱪ,;MTek}𐀏&/8?GO`hnsw¼ﱪ𐀏&+6;GKOW^cow{½ﱪ=𐀏:FKV[gns~¾ﱪLt|¥¬𐀏HV[fkp§¿ﱪ[l}­𐀏Wfov£§¯´·Àﱪi¤𐀏fv¢¯·»¿ÃÇÁﱪ}­µÅÝ𐀏v¡¦¯ÀÇËÏÓ×Èﱪ¹³ÉﱪÌՐÃÀÉÊÎÜËՐíÝëÌՐýìúÍûﱪÎՐ ÏՐ-*1ÐՐ=)7;BÑՐM8GSÒGWdÓVguÔﱪµ¼ÄÛãëóû𐀏¯ØàèðøeÕtﱪéñù𐀏ÁÆËÏÓçï÷ÿÖ¨𐀏ÑÖÛßãöûÿﱪ!×¹𐀏#'+/3áæëïóﱪýØ¡Ê𐀏#'+/37;?CñöûÿÙ°Û𐀏&+/37;?CGKOSﱪÚ¿ìﱪ=EMU]e𐀏7?GOW_ÛÎýﱪ,KS[cks𐀏!'HPX`hpÜՐíÝëÝﱪ¨¸ÈՐý¤´ÄìúÞȎKﱪFՐ%"/³¸ÃÈÓØûßȎ^ﱪUՐ52@ÁÉÑÙáéà䕏jϻhﱪeÝíýՐ-E*BQÐÙàéðùá䕏z~ﱪtíýՐ=U)7;OSbàêðúâ῾ù䕏ϻﱪՐMe÷8G_sðýã䕏ϻﱪ῾)Ր'-GWoÿä䕏­ﱪ¦-=VgՐ#(38῾ *0:åϻ·»ﱪ³῾$4DՐ"2B-=Me¦æȎÊϻÇﱪcÁÍ῾.+^t·çȎÜ䕏Úϻ×ﱪsÑ῾q:nÈèȎìϻåﱪá῾IÙéȎýϻöﱪô¡ê῾Yêﱪ¦g£°ûëՐÀvµϻﱪìﱪ"ÅÏíጉíýϻ7ﱪ2-ÔÞç÷îϻGጉ-=M]m}­½ÍÝí'7Wgw§·Ç×ç÷ý뛌Cï'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉð'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉñ'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉò'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉ:JZjzªºÊÚêúó'-7=GJWZgjwz§ª·ºÇÊ×Úçê÷úጉ*:MP]`mp} ­°½ÀÍÐÝàíðýô'*7:GJW]gmw}§­·½ÇÍ×Ýçí÷ýጉ -0=@MP_o¯¿Ïßïÿõ'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉ/?O_ö'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉ÷'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉø'-7=GMW]gmw}¦­¶½ÆÍÖÝæíöýጉ °ÀÐàðù&-6=FMV]fmv} ¦­¶½ÆÍÖÝæíöýጉ 0@P`pú뛌±¶ÁÆÑÖáæñö&-6=FMV]fmv}¦­½ÍÝíýûጉÇ×ç÷-=M]m}­½ÅÍÕÝåíõý뛌!&16AFQVafqv¡¦±¶ÂÒâòü%-5=EMU]emu}¥­µ½ÅÍÕÜåìõü뛌"2BRbr¢²Âጉ'7GWgw§·Çý%,5<ELU\elu|¥¬µ¼ÅÌÕÜጉåíõýþጉ%-5=EMU]emu}¥­µ½ÅÍÕÝåíý÷ÿጉ-=M]m}­½ÍÝíý'7GWgw§·Ç×ç÷뛌Ā'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉā'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉĂ'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉă'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉJZjzªºÊÚêúĄ'-7=GMWZgjwz§ª·ºÇÊ×Úçê÷úጉ*:J]`mp} ­°½ÀÍÐÝàíðýą'*7:GJWZgmw}§­·½ÇÍ×Ýçí÷ýጉ -0=@MP]`o¯¿ÏßïÿĆ'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉ/?O_oć'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉĈ'-7=GMW]gmw}§­·½ÇÍ×Ýçí÷ýጉĉ'-7=GMW]gmw}¦­¶½ÆÍÖÝæíöýጉ°ÀÐàðĊ&-6=FMV]fmv}¦­°¶½ÆÍÖÝæíöýጉ 0@P`p ċ뛌ÁÆÑÖáæñö&-6=FMV]fmv}¦­¶½ÍÝíýČጉ×ç÷-=M]m}­½ÍÕÝåíõý뛌!&16AFQVafqv¡¦±¶ÁÆÒâòč%-5=EMU]emu}¥­µ½ÅÍÕÝåìõü뛌"2BRbr¢²ÂÒጉ'7GWgw§·Ç×Ď%,5<ELU\elu|¥¬µ¼ÅÌÕÜåìጉõý"""
    advanced_display_strategy.update_canvas(message=message,
                                            canvas=current_state_constructed_by_message)
    cv2.imshow("Current state constructed by message", current_state_constructed_by_message)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return




def test_rgb_utf8_conversion():
    # Test case 1: Red color
    r = 255
    g = 0
    b = 0
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)

    # Test case 2: Green color
    r = 0
    g = 255
    b = 0
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)

    # Test case 3: Blue color
    r = 0
    g = 0
    b = 255
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)


    # Test case 4: Custom color
    r = 128
    g = 64
    b = 192
    utf8_char = rgb_to_utf8(r, g, b)
    rgb_tuple = utf8_to_rgb(utf8_char)
    return


def test_unicode_utf8_conversion():
    # Convert Unicode codepoint to UTF-8 char
    codepoint1 = 990
    utf8_char = chr(codepoint1)
    print(utf8_char)  # Output: Ϟ

    # Convert UTF-8 char to Unicode codepoint
    utf8_char = "Ϟ"
    codepoint2 = ord(utf8_char)
    print(codepoint2)  # Output: 990
    assert codepoint1 == codepoint2