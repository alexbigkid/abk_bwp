
import os
import random

BWP_FILES = 2

def get_text_overlay_font_name() -> str:
    font_path = os.path.dirname(__file__)
    font_list_all = sorted(next(os.walk(font_path))[BWP_FILES])
    font_list = [font for font in font_list_all if font.endswith("tf")]
    if len(font_list) > 0:
        random_num = random.randint(0,len(font_list)-1)
        return os.path.join(font_path, font_list[random_num])
    return ""
