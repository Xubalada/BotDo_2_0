# Autoloader
import sys
import os
from pathlib import Path
path = Path(__file__).resolve()
sys.path.append(str(path.parents[1]))
root_path = str(path.parents[1])

# Import system
from bs4 import BeautifulSoup
from src.state.state import State
import traceback
from src.errors.screen_errors import ScreenError
from src.screen_controllers.screen import Screen
from database.sqlite import Database
from src.screen_controllers.chat import Chat
from src.character.login import Login
from src.character.moving import Moving
from src.errors.character_errors import CharacterCriticalError, RetryError, JobError
import requests
import time
import re
import keyboard
import pyautogui

debug = True

class Character:

    def __init__(
        self,
        state: State,
        screen: Screen,
        account: dict,
        database: Database
    ):
        self.shared_state = state
        self.screen = screen
        self.database = database
        self.name = None
        self.login = None
        self.password = None
        self.window_id = None
        self.level = None
        self.class_name = None
        self.current_hp = None
        self.current_pos = None
        self.last_pos = None
        self.my_zaaps = dict()
        self.primary_status = dict()
        self.res_status = dict()
        self.secundary_status = dict()
        self.damage_status = dict()
        self.skills = dict()
        self.queue = list()
        self.load_metadata(account)
        self.moving = Moving(self.screen, self.database, self.get_pos)
        self.chat = Chat(screen=self.screen, character_name=self.name)
        self.chat_comands_map = Character.get_chat_comands_map()
        self.add_init_functions_on_queue()

    def run_function(self):
        if len(self.queue) > 0:
            job = self.queue.pop(0)
            if job.__name__ != 'login_dofus':
                Screen.bring_character_to_front(self.window_id)
            time.sleep(0.5)
            if job:
                try:
                    Character.run_function_with_retry(job)
                except JobError as e:
                    raise JobError(f'Max atemp of 3 for {self.name} job = {job.__name__}')
        self.shared_state.set_state(key='turn_of', value='free')

    @staticmethod
    def get_chat_comands_map():
        return {
            'hp': {
                'string': '%hp%',
                'regex': r'(\d+)',
                'type': 'int'
            },
            'pos': {
                'string': '%pos%',
                'regex': r'(-?\d{1,2})',
                'type': 'tuple'
            }
        }

    @staticmethod
    def run_function_with_retry(job: callable, retry_counter: int = 0):
        retry_counter += 1
        if retry_counter > 3:
            raise JobError('Max atemp of 3')
        try:
            job()
        except RetryError as e:
            print(f'[JOB] {job.__name__} fail {retry_counter}/3', e)
            print('###' * 10)

    def queue_len(self):
        return len(self.queue)

    def go_to(self, position: tuple):
        self.moving.register_path_to_move(start=self.current_pos, destiny=position)
        self.move()

    def colect(self, items: list):
        print('COLECT!!!!')

    def add_init_functions_on_queue(self):
        self.queue.append(self.login_dofus)
        self.queue.append(self.check_hp_pos)
        if not debug:
            self.queue.append(self.get_zaaps)

    def get_check_string(self, property_name: str):
        return self.chat_comands_map.get(property_name).get('string')

    def get_check_regex(self, property_name: str):
        return self.chat_comands_map.get(property_name).get('regex')

    def get_check_type(self, property_name: str):
        return self.chat_comands_map.get(property_name).get('type')

    def cast_str_by_type(self, string: str, type: str):
        if type == 'int':
            return int(string)
        if type == 'tuple':
            return eval(f'({string})')
        return None

    def check_list(self, str_list: list):
        chat_list = list()
        for str_item in str_list:
            chat_list.append(self.get_check_string(str_item))
        results = self.chat.chat_io(string_array=chat_list)
        to_return = dict()
        count = 0
        for str_item in str_list:
            regex = self.get_check_regex(str_item)
            cast_type = self.get_check_type(str_item)
            regex_return = re.findall(regex, results[count])
            print(results, regex, count)
            to_return[str_item] = self.cast_str_by_type(','.join(regex_return), cast_type)
            count += 1
        return to_return

    def get_pos(self):
        result = self.check_list(str_list=['pos'])
        self.current_pos = result['pos']
        return self.current_pos


    #    :::      :::::::: ::::::::::: ::::::::::: ::::::::  ::::    :::  ::::::::
    #   :+: :+:   :+:    :+:    :+:         :+:    :+:    :+: :+:+:   :+: :+:    :+:
    #  +:+   +:+  +:+           +:+         +:+    +:+    +:+ :+:+:+  +:+ +:+
    # +#++:++#++: +#+           +#+         +#+    +#+    +:+ +#+ +:+ +#+ +#++:++#++
    # +#+     +#+ +#+           +#+         +#+    +#+    +#+ +#+  +#+#+#        +#+
    # #+#     #+# #+#    #+#    #+#         #+#    #+#    #+# #+#   #+#+# #+#    #+#
    # ###     ###  ########     ###     ########### ########  ###    ####  ########


    def check_hp_pos(self):
        str_list = ['hp', 'pos']
        result = self.check_list(str_list=str_list)
        self.current_pos = result['pos']
        self.current_hp = result['hp']

    def login_dofus(self):
        login = Login()
        self.window_id = login.run(
            account={
                'login': self.login,
                'password': self.password,
                'name': self.name
            },
            screen_size=self.screen.screen_size
        )
        print(f'Character {self.name} has recived {self.window_id} windows_id')
        time.sleep(12)

    def open_close_heavenbag(self):
        keyboard.press_and_release('h')
        time.sleep(4)

    def get_zaaps(self):
        zaaps = self.database.get_zaaps()
        self.open_close_heavenbag()
        bag_type = self.screen.get_my_bag_type()
        if bag_type == 'kerub':
            xconst = 0.158004158004158
            yconst = 0.45601173020527859
        else:
            yconst = 0.332844574780058651
            xconst = 0.36382536382536382
        xcoord = self.screen.game_active_screen[0] + xconst * (self.screen.game_active_screen[2] - self.screen.game_active_screen[0])
        ycoord = self.screen.game_active_screen[3] * yconst
        pyautogui.click((xcoord, ycoord))
        time.sleep(4)
        try:
            search_input_pos = self.screen.find_zaap_search_position()
        except ScreenError as e:
            traceback.print_tb(e.__traceback__)
            raise CharacterCriticalError('You are not premium account!!! 💸')
        pyautogui.click(search_input_pos)
        for zaap in zaaps:
            zaap_name = zaap[0]
            time.sleep(1)
            keyboard.write(zaap_name)
            if self.screen.has_zaap_marker():
                self.my_zaaps.update({zaap[0]: (zaap[1], zaap[2])})
            keyboard.press('control')
            time.sleep(0.1)
            keyboard.press_and_release('a')
            keyboard.release('control')
            time.sleep(0.1)
            keyboard.press_and_release('delete')
        time.sleep(0.1)
        keyboard.press_and_release('esc')
        time.sleep(0.5)
        self.open_close_heavenbag()

    def move(self):
        has_more_movements = self.moving.execute_movement()
        if has_more_movements:
            self.queue.append(self.move)

    # :::        ::::::::      :::     :::::::::   ::::::::
    # :+:       :+:    :+:   :+: :+:   :+:    :+: :+:    :+:
    # +:+       +:+    +:+  +:+   +:+  +:+    +:+ +:+
    # +#+       +#+    +:+ +#++:++#++: +#+    +:+ +#++:++#++
    # +#+       +#+    +#+ +#+     +#+ +#+    +#+        +#+
    # #+#       #+#    #+# #+#     #+# #+#    #+# #+#    #+#
    # ########## ########  ###     ### #########   ########


    def load_metadata(self, account: dict):
        self.load_damages(account.get('damage'))
        self.class_name = account.get('class')
        self.level = account.get('level')
        self.name = account.get('name')
        self.login = account.get('login')
        self.password = account.get('password')
        self.load_primary_status(account.get('primaryCharacteristics'))
        self.load_resistances(account.get('resistences'))
        self.load_secundary_status(account.get('secundaryCharacteristics'))

    def load_damages(self, damage: dict):
        dict_damages = {
            "Air (fixed)": "air_fixed",
            "Critical damage": "critical damage",
            "Damage": "damage",
            "Earth (fixed)": "earth_fixed",
            "Fire (fixed)": "fire_fixed",
            "Neutral (fixed)": "neutral_fixed",
            "Pushback": "pushback",
            "Reflect": "reflect",
            "Traps (Power)": "traps_power",
            "Traps (fixed)": "traps_fixed",
            "Water (fixed)": "water_fixed",
        }
        if damage:
            for item in damage:
                self.damage_status[dict_damages.get(item)] = damage.get(item)

    def load_resistances(self, resistances):
        dict_resistances = {
                "Air (%)": "air",
                "Air (fixed)": "air_fixed",
                "Critical Hits (fixed)": "critical_hits_fixed",
                "Earth (%)": "earth",
                "Earth (fixed)": "earth_fixed",
                "Fire (%)": "fire",
                "Fire (fixed)": "fire_fixed",
                "Neutral (%)": "neutral",
                "Neutral (fixed)": "neutral_fixed",
                "Pushback (fixed)": "pushback_fixed",
                "Water (%)": "water",
                "Water (fixed)": "water_fixed"
        }
        if resistances:
            for item in resistances:
                self.res_status[dict_resistances.get(item)] = resistances.get(item)

    def load_primary_status(self, primary_status: dict):
        if primary_status:
            for item in primary_status:
                self.primary_status[item.lower()] = primary_status.get(item)

    def load_secundary_status(self, secundary_status: dict):
        dict_secundary_status = {
            "AP Parry": "ap_parry",
            "AP Reduction": "ap_reduction",
            "Dodge": "dodge",
            "Heals": "heals",
            "Initiative": "initiative",
            "Lock": "lock",
            "MP Parry": "mp_parry",
            "MP Reduction": "mp_reduction",
            "Prospecting": "prospecting",
            "Summons": "summons"
        }
        if secundary_status:
            for item in secundary_status:
                self.secundary_status[dict_secundary_status.get(item)] = secundary_status.get(item)
