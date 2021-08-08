# Autoloader
import sys
import os
from pathlib import Path

path = Path(__file__).resolve()
sys.path.append(str(path.parents[2]))
root_path = str(path.parents[1])

# Import system
import numpy as np
import cv2
import time
import pytesseract
import pyautogui
import win32gui
import PIL.ImageOps
import re
from src.tools.search import Search
from src.errors.screen_errors import ScreenError
from PIL import Image
from PIL import ImageGrab
from skimage.metrics import structural_similarity

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class Screen:
    def __init__(self, mode=None):
        self.base_local_path = os.path.dirname(os.path.realpath(__file__))
        self.screen_size = None
        self.get_screen_size()
        self.game_scale = None
        self.get_game_scale()
        self.game_active_screen = None
        self.get_game_active_screen()
        self.game_active_screen_width = (
            self.game_active_screen[2] - self.game_active_screen[0]
        )
        self.game_active_screen_height = (
            self.game_active_screen[3] - self.game_active_screen[1]
        )
        self.y_range = None
        self.x_range_black = None
        self.x_range_white = None
        self.get_map_cell_translations()
        self.bottom_region = None
        self.get_bottom_region()
        self.fight_buttom_region = None
        self.get_fight_buttom_region()
        self.chat_input = None
        self.coordinates_region = None
        self.pos_ocr_regex = re.compile(r"(-?\d{1,2})")
        self.get_coordinates_region()
        self.search = Search()

    def get_coordinates_region(self):
        self.coordinates_region = (
            round(12 * self.game_scale),
            round(46.666 * self.game_scale),
            round(161.333 * self.game_scale),
            round(74.666 * self.game_scale),
        )

    def pos_ocr(self, image):
        image = PIL.ImageOps.invert(image)
        config = "--psm 13 --oem 3"
        text = pytesseract.image_to_string(image, config=config)
        coords = tuple([int(i) for i in self.pos_ocr_regex.findall(text)])
        return coords

    def get_screen_size(self):
        self.screen_size = ImageGrab.grab("").size

    def get_game_scale(self):
        width_const = self.screen_size[0] / 1280
        height_const = self.screen_size[1] / 1024
        self.game_scale = min(width_const, height_const)

    def get_game_active_screen(self):
        action_screen_proportion = 0.709
        width = (self.screen_size[0] - 86) * self.game_scale
        X = (self.screen_size[0] - width) / 2
        high = action_screen_proportion * width
        self.game_active_screen = (round(X), 0, round(X + width), round(0 + high))

    def get_bottom_region(self):
        self.bottom_region = (
            0,
            round(0.65 * self.screen_size[1]),
            self.screen_size[0],
            self.screen_size[1],
        )

    def get_fight_buttom_region(self):
        self.fight_buttom_region = (
            0.75419 * (self.game_active_screen_width) + self.game_active_screen[0],
            self.game_active_screen[3],
            self.game_active_screen[2],
            self.screen_size[1],
        )

    def map_to_screen(self, cell_number: int):
        ycoord = cell_number // 14
        xcoord = cell_number - (ycoord * 14)
        translation_x = self.game_active_screen[0]
        translation_y = self.game_active_screen[1]
        if ycoord % 2 == 0:
            return (
                round(self.x_range_black[xcoord] + translation_x),
                round(self.y_range[ycoord] + translation_y),
            )
        return (
            round(self.x_range_white[xcoord] + translation_x),
            round(self.y_range[ycoord] + translation_y),
        )

    def get_map_cell_translations(self):
        step_x = self.get_action_screen_x_step()
        step_y = self.get_action_screen_y_step()
        y_start = step_y * 0.5
        self.y_range = list(
            np.arange(y_start, self.game_active_screen_height - step_y, step_y)
        )
        self.x_range_black = list(
            np.arange(step_x * 0.5, self.game_active_screen_width, step_x)
        )
        self.x_range_white = list(
            np.arange(step_x, self.game_active_screen_width, step_x)
        )

    def get_action_screen_y_step(self):
        return (self.game_active_screen_height) / 41

    def get_action_screen_x_step(self):
        return (self.game_active_screen_width) / 14.5

    def get_foreground_screen_id(self):
        return win32gui.GetForegroundWindow()

    def get_screen_image(self):
        return ImageGrab.grab()

    def get_active_screen_image(self):
        return ImageGrab.grab(self.game_active_screen)

    def image_ssim(self, img1, img2):
        img1 = np.array(img1)
        img2 = np.array(img2)
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        return structural_similarity(gray1, gray2)

    #        :::::::: ::::::::::: :::    ::: :::::::::: :::::::::   ::::::::
    #      :+:    :+:    :+:     :+:    :+: :+:        :+:    :+: :+:    :+:
    #     +:+    +:+    +:+     +:+    +:+ +:+        +:+    +:+ +:+
    #    +#+    +:+    +#+     +#++:++#++ +#++:++#   +#++:++#:  +#++:++#++
    #   +#+    +#+    +#+     +#+    +#+ +#+        +#+    +#+        +#+
    #  #+#    #+#    #+#     #+#    #+# #+#        #+#    #+# #+#    #+#
    #  ########     ###     ###    ### ########## ###    ###  ########

    def find_zaap_search_position(self):
        result = self.search.search_color(
            RGB=(0, 255, 255), region=(self.game_active_screen)
        )
        print(result)
        if len(result) < 1:
            raise ScreenError("Fail to find zaap on screen")
        result_width = (
            max(result, key=lambda x: x[0])[0] - min(result, key=lambda x: x[0])[0]
        )
        result_heigh = (
            max(result, key=lambda x: x[1])[1] - min(result, key=lambda x: x[1])[1]
        )
        xcoord = min(result, key=lambda x: x[0])[0] + 2.5 * result_width
        ycoord = min(result, key=lambda x: x[1])[1] + result_heigh / 2
        return (xcoord, ycoord)

    def has_zaap_marker(self):
        return self.is_color_on_region(RGB=(255, 0, 255), region=(self.game_active_screen))

    @staticmethod
    def bring_character_to_front(character_window_number: int):
        win32gui.SetForegroundWindow(character_window_number)

    def get_chat_content(self, chat_position, ocr_config_number=1):
        ocr_configs = {1: "--psm 6 --oem 3", 2: "--psm 7 --oem 3"}
        chat_image = ImageGrab.grab(chat_position)
        ocr_config = ocr_configs[ocr_config_number]
        text = pytesseract.image_to_string(chat_image, config=ocr_config)
        return text

    def is_color_on_region(self, RGB: tuple, region:tuple):
        result = self.search.search_color(
            RGB=RGB, region=region
        )
        if result != []:
            return True
        return False

    def get_line_text_on_region(self, region: tuple):
        img = ImageGrab.grab(region)
        config = "--psm 7 --oem 3"
        text = pytesseract.image_to_string(img, config=config)
        return text

if __name__ == "__main__":
    screen = Screen()
    time.sleep(1)
    a = screen.get_battle_map_info()
    print(a.keys())
    for i in a['holes']:
        pyautogui.moveTo(screen.map_to_screen(i))
        time.sleep(0.01)

