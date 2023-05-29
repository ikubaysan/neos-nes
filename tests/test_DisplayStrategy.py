import pytest
import random
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
    cv2.waitKey(0)
    cv2.destroyAllWindows()
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
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return



def test_update_canvas_from_cpp(frame_to_string: FrameToString, advanced_display_strategy: AdvancedDisplayStrategy):
    # Initialize the arrays to be all the same color, say, bright red.
    last_state = np.full((350, 350, 3), [0, 0, 0], dtype=np.uint8)  # Initialize last_state with black color

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
    advanced_display_strategy.update_canvas(message=message,
                                            canvas=current_state_constructed_by_message)
    cv2.imshow("Current state constructed by message", current_state_constructed_by_message)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return




def test_update_canvas_from_hardcoded_message(frame_to_string: FrameToString, advanced_display_strategy: AdvancedDisplayStrategy):
    # Initialize the arrays to be all the same color, say, bright red.
    current_state_constructed_by_message = np.full((240, 256, 3), [0, 0, 0], dtype=np.uint8)  # Initialize last_state with black color
    message = """(²j)²i*²i+²i,²i-²i.²j0ﱪÃ뛌1Ã뛌2Ã뛌3뛌¿4ﱪÄ뛌¿5ﱪÄÀ뛌6Ã뛌7Ã뛌8ጉ(3;H[hÃ뛌 -P9ጉ)3;I[iÃ뛌-O:ጉ)3;I[iÃ뛌-O;ጉ*3;J[jÃ뛌-N<ጉ*Jj3;[Ã뛌-N=ጉ+Kk3;[Ã뛌>ጉ+Kk3;[Ã뛌?ጉ+Kk3;[Ã뛌@ጉ+\$3;CKSckÃ뛌EeAጉ,%3;CKSZckÃ뛌EUeBጉ,'3;CKSZckÃ뛌EUeCጉ,)3;CJSZcjÃ뛌EUeDጉ*Zl3;CJSciÃ뛌-EU]eEጉ*L3;CISZcjÃ뛌!-EUeFጉ+L3;CISZckÃ뛌#EUeGጉ+K[k3;CHSVcÃ뛌%EeHጉ+K[k;CFcÃ뛌Iጉ+J[k;CFcÃ뛌MJጉJ[+;CFckÃ뛌MKጉI[*:CFckÃ뛌NL*:C[ckÃ뛌NMጉ,<)9CN[ckÃ뛌Nጉ,<)9CN[ckÃ뛌Oጉ+;(/8CO[ckÃ뛌Pጉ+;D\dl/>OÃ뛌Qጉ*:D\dl 0>PÃ뛌Rጉ*:D\dl 0>PÃ뛌Sጉ)9D\dl!1>QÃ뛌TÃ뛌UÃ뛌VÃ뛌WÃ뛌Xጉ%0@P[h °Ã뛌 +8EU`u¨Yጉ&1AQ[i¡±Ã뛌*7EU_u§Zጉ&1AQ[i¡±Ã뛌*7EU_u§[ጉ'2BR[j¢²Ã뛌6EU^u¦\ጉ'2BRj¢²[Ã뛌6EUu¦]ጉ3CSk£³[Ã뛌u^ጉ3CSk£³[Ã뛌u_ጉ3CSk£³[Ã뛌u`#+3;CKS[ck{£«³Ã뛌ua#+3;CKS[ck{£«³Ã뛌ub#+3;CKS[ck{£«³Ã뛌uc#+3;CKS[ck{£«³Ã뛌ud#+3;CKS[ck{£«³Ã뛌ue#+3;CKS[ck{£«³Ã뛌uf#+3;CKS[ck{£«³Ã뛌ug#+3;CKS[ck{£«³Ã뛌uhጉ¬´#+3;CKS[ck{£Ã뛌Mu}iጉ­´#+3;CKS[ck{£Ã뛌Mu}jጉ´#+3;CKS[ck{£¯Ã뛌Mu}kጉ´#+3;CKR[ck{£±Ã뛌Mu}lጉT²#+3;CKQ[ck{£Ã뛌Mu}mጉ²#+3;CKR[ck{£Ã뛌Mu}©nጉ³#+3;CKS[ck{£§Ã뛌Mu}«oጉS³#+3;CK[ck{£§Ã뛌Mu}­pጉS³#+3CK[ck{£«Ã뛌uqጉS³#+3CK[ck{£«Ã뛌urጉ«#+3CKS[ck{£³Ã뛌usጉ«#+3CKS[ck{£³Ã뛌ut#+3CKS[ck{£«³Ã뛌uu#+3CKS[ck{£«³Ã뛌uv#+3CKS[ck{£«³Ã뛌uw#+3CKS[ck{£«³Ã뛌uxጉ»#+3;CKS[k{£³Ã뛌u}yጉ»#+3;CKS[k{£³Ã뛌u}zጉ»#+3;CKS[k{£³Ã뛌u}{ጉ»#+3;CKS[j{¢²Ã뛌u}|#+3;CKS[j{¢²»Ã뛌u}}ጉl¤´#+3;CKS[i{¡±»Ã뛌u}~ጉl¤´#+3;CKS[i{¡±»Ã뛌u}ጉk£³#+3;CKS[_h{ §°»Ã뛌u}ጉ$,4<DLT\k|£³¼_v~§¶Ã뛌ጉ$,4<DLT\j|¢²¼`v~¨¶Ã뛌ጉ$,4<DLT\j|¢²¼`v~¨¶Ã뛌ጉ$,4<DLT\i|¡±¼av~©¶뛌¿ﱪÄ뛌¿ﱪÄÀ뛌Ã뛌ﱪÃﱪZjrz£«¹Â뛌V_em¥­±µ½ﱪW\a¯뛌UZ^dimqu¤¬µÁﱪV]z°뛌T_dimqu¤¬²µ¹½ÁﱪX]krª³뛌T[_ey¤µ¹½ÁﱪX]³뛌T[_imqy¤¬°µ¹½ÁﱪV]³뛌T_hquy¤¬µÁﱪW\cirz«¹Â뛌UZmu¤­±µ½ﱪZ뛌V 𐀏GT]fmu}¡¥ﱪ:Zi{«ûጉ6í¡𐀏FTYeimu|¡¥ﱪ;I£ጉ5ì"¢𐀏GTYdiu|¥ﱪ;£üጉ5ì£²ö𐀏GTYdin¥ﱪ<rz£ªጉ4ì¤ò𐀏GT]dot|¢¥ﱪ<Zkጉ4ìõ¥ò÷𐀏GT]diot|¡¥ﱪ<ጉ4ì¦ጉìﱪKc{«𐀏ET]eiot}¡¥5:ò÷§ጉìﱪ:÷뛌6¨²øõጉì©õጉìªጉì"«²õጉì¬õጉì­ﱪüጉì®ጉì"¯ﱪüì°ﱪJZi{«𐀏ET]fmu}¡¥±ﱪ£𐀏DITYeimu|¡¥²ﱪK£𐀏HTYdiu|¥³ﱪJrz£ª𐀏FTYdin¥´ﱪIZk𐀏ET]dot|¢¥µﱪG𐀏DT]diot|¡¥¶ﱪKc{«𐀏DT]eiot}¡¥½ﱪ¾ﱪՐ¿ÀՐÁՐÂՐÃՐÄՐ ÅՐ"Æ#Ç$ÈﱪT[cz¢𐀏Nw%Éﱪx 𐀏PUZ^bv~&Ê𐀏PUZ^buz~¢'Ëﱪl𐀏PUZ^buz~¢(Ìﱪcl𐀏PUZ^fuz~¢)Íﱪ|¤Ĉ𐀏PUZ^v~*ĂÎﱪ[z¢ċ𐀏PVwՐĂ+ÿĈÏ,ýċÐﱪ·Ç×Ր$Č"-³ÃÓüĊÑȎՐ$Č!.²·ÂÇÒ×ûĉÒȎՐ$Č!/°¸ÀÈÐØúĉďÓﱪ~¼ÌÜՐ$Č!0¯¸¿ÈÏØùĉÔﱪ¼ÌÜ䕏Ր$Č"1¯¹¿ÉÏÙøĆĊÕ῾¸ÈØϻ䕏ﱪ}Ր$¶ÆÖČ2¯¼ÌÜ÷ĆÖ῾¹¿ÉÏÙϻ䕏ﱪ}Ր²·ÂÇÒ×3®¼ÌÜöĆ×῾³ÃÓ䕏ﱪ}Ր±ÁÑ4­¼ÌÜõĆØﱪâ῾­ϻ}5ªÝôÙﱪâ῾àȎ䕏{6©ÝóÚ῾àȎﱪ~䕏{7¨ÞòÛ῾¨ﱪ}åϻ䕏{8áñÜȎﱪ|å9¦âðÝȎﱪ|:¥äïÞȎϻ}ﱪ{;¥äîßﱪ{<¦ãíàጉ,<L\l|¬¼ÌÜìüČ&6FVfv¦¶ÆÖæöĆá&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČâ&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČã&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČäጉ)9IYiy©¹ÉÙéùĉ&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČåጉ,/<?LO\_lo|¬¯¼¿ÌÏÜßìïüÿČď&)69FIVYfivy¦©¶¹ÆÉÖÙæéöùĆĉæጉ.>N^n~®¾ÎÞîþĎ&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČç&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČè&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČé&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČê%,5<ELU\elu|¥¬µ¼ÅÌÕÜåìõüąČጉ/?O_o¯¿Ïßïÿďë%,5<ELU\elu|¥¬µ¼ÅÌÕÜåìõüąČì,<L\l|¬¼ÌÜìüČ뛌 %05@EPU`epu ¥°µÀÅÐÕàåðõĀąíጉ&6FVfv¦¶ÆÖæöĆ$,4<DLT\dlt|¤¬´¼ÄÌÔÜäìôüĄČ뛌!1AQaq¡±ÁÑáñāî$+4;DKT[dkt{¤«´»ÄËÔÛäëôûĄċïጉ$,4<DLT\dlt|¤¬´¼ÄÌÔÜäìôüĄČðጉ,<L\l|¬¼ÌÜìüČ&6FVfv¦¶ÆÖæöĆñ&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČò&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČó&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČôጉ)9IYiy©¹ÉÙéùĉ&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČõጉ,/<?LO\_lo|¬¯¼¿ÌÏÜßìïüÿČď&)69FIVYfivy¦©¶¹ÆÉÖÙæéöùĆĉöጉ.>N^n~®¾ÎÞîþĎ&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČ÷&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČø&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČù&,6<FLV\flv|¦¬¶¼ÆÌÖÜæìöüĆČú%,5<ELU\elu|¥¬µ¼ÅÌÕÜåìõüąČጉ/?O_o¯¿Ïßïÿďû%,5<ELU\elu|¥¬µ¼ÅÌÕÜåìõüąČü,<L\l|¬¼ÌÜìüČ뛌 %05@EPU`epu ¥°µÀÅÐÕàåðõĀąýጉ&6FVfv¦¶ÆÖæöĆ$,4<DLT\dlt|¤¬´¼ÄÌÔÜäìôüĄČ뛌!1AQaq¡±ÁÑáñāþ$+4;DKT[dkt{¤«´»ÄËÔÛäëôûĄċ"""
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