import numpy as np
import cv2
import imutils
import pyautogui
import os
from enum import Enum
import time
from datetime import datetime
from typing import Tuple, List, Dict
from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops
from collections.abc import Callable
import pandas as pd
import json


class AnalyzerStatus(Enum):
    IDLE = 1
    RUNNING = 2

class TimeOutError(Exception):
    """Exception raised when an operation takes too long."""
    def __init__(self, message: str = 'The operation takes too long.') -> None:
        self.message = message
        super().__init__(self.message)

class DeviceRunningError(Exception):
    """Exception raised when an operation is attempted while the analyzer is running."""
    def __init__(self, message: str = 'The analyzer is currently running. Please wait until it is done.') -> None:
        self.message = message
        super().__init__(self.message)

class ButtonNotFoundError(Exception):
    """Exception raised when a press-button is requested but the button has not been found."""
    def __init__(self, message: str = 'The button was not found.') -> None:
        self.message = message
        super().__init__(self.message)

class UnkonwnButtonNameError(Exception):
    """Exception raised when an unknown button name is provided."""
    def __init__(self, message: str = 'The button name is unknown.') -> None:
        self.message = message
        super().__init__(self.message)

class LIBSAnalyzer:
    """Base driver class for the SciAps Z300 LIBS analyzer based on GUI automation."""

    def __init__(self, cache_folder_path: str, 
                 export_folder_path: str, 
                 measure_button_img_path: str = 'button_templates/measure_button.png',
                 sample_name_input_img_path: str = 'button_templates/sample_name_input.png', 
                 export_button_img_path: str = 'button_templates/export_button.png',
                 separate_spectrum_button_img_path: str = 'button_templates/separate_spectrum_button.png',
                 new_folder_button_img_path: str = 'button_templates/new_folder_button.png',
                 export_finish_button_img_path: str = 'button_templates/export_finish_button.png',
                 delete_button_img_path: str = 'button_templates/delete_button.png',
                 sync_button_img_path: str = 'button_templates/sync_button.png',
                 time_out: float = 15.0,
                 sleep_func: Callable[[float], None] = time.sleep) -> None:
        """
        Initialize the LIBSAnalyzer.

        Args:
            cache_folder_path (str): Path to the folder where the analyzer stores measurement cache files.
            export_folder_path (str): Path to the folder where to store the exported data.
            measure_button_img_path (str, optional): Path to the image of the measurement button. Defaults to 'measure_button.png'.
            sample_name_input_img_path (str, optional): Path to the image of the sample name input field. Defaults to 'sample_name_input.png'.
            export_button_img_path (str, optional): Path to the image of the export button. Defaults to 'export_button.png'.
            separate_spectrum_button_img_path (str, optional): Path to the image of the separate spectrum button. Defaults to 'separate_spectrum_button.png'.
            new_folder_button_img_path (str, optional): Path to the image of the new folder button. Defaults to 'new_folder_button.png'.
            export_finish_button_img_path (str, optional): Path to the image of the export finish button. Defaults to 'export_finish_button.png'.
            delete_button_img_path (str, optional): Path to the image of the delete button. Defaults to 'delete_button.png'.
            time_out (float, optional): Time out for operations. Defaults to 20.0.
            sleep_func (Callable, optional): Sleep function. Defaults to time.sleep.
        """
        self.cache_folder_path = cache_folder_path
        self.export_folder_path = export_folder_path
        self.time_out = time_out
        self.sleep_func = sleep_func
        
        # load or create a dictionary for button positions
        if os.path.exists('button_positions.json'):
            with open('button_positions.json', 'r') as f:
                loaded_buttons = json.load(f)
            # Convert any list positions back to tuples for 'pos'
            for button in loaded_buttons:
                pos = loaded_buttons[button].get('pos', None)
                if isinstance(pos, list):
                    loaded_buttons[button]['pos'] = tuple(pos)
            self.buttons = loaded_buttons
            if 'measure' in self.buttons:
                self.buttons['measure']['img_path'] = measure_button_img_path
            if 'sample_name' in self.buttons:
                self.buttons['sample_name']['img_path'] = sample_name_input_img_path
            if 'export' in self.buttons:
                self.buttons['export']['img_path'] = export_button_img_path
            if 'separate_spectrum' in self.buttons:
                self.buttons['separate_spectrum']['img_path'] = separate_spectrum_button_img_path
            if 'new_folder' in self.buttons:
                self.buttons['new_folder']['img_path'] = new_folder_button_img_path
            if 'export_finish' in self.buttons:
                self.buttons['export_finish']['img_path'] = export_finish_button_img_path
            if 'delete' in self.buttons:
                self.buttons['delete']['img_path'] = delete_button_img_path
            if 'sync' in self.buttons:
                self.buttons['sync']['img_path'] = sync_button_img_path
        else:
            self.buttons = {
                'measure': {
                    'pos': None,
                    'found': False,
                    'img_path': measure_button_img_path
                },
                'sample_name': {
                    'pos': None,
                    'found': False,
                    'img_path': sample_name_input_img_path
                },
                'export': {
                    'pos': None,
                    'found': False,
                    'img_path': export_button_img_path
                },
                'separate_spectrum': {
                    'pos': None,
                    'found': False,
                    'img_path': separate_spectrum_button_img_path
                },
                'new_folder': {
                    'pos': None,
                    'found': False,
                    'img_path': new_folder_button_img_path
                },
                'export_finish': {
                    'pos': None,
                    'found': False,
                    'img_path': export_finish_button_img_path
                },
                'delete': {
                    'pos': None,
                    'found': False,
                    'img_path': delete_button_img_path
                },
                'sync': {
                    'pos': None,
                    'found': False,
                    'img_path': sync_button_img_path
                }
            }
        self.status = AnalyzerStatus.IDLE
        self.sample_name = ''

    def measure(self) -> None:
        """
        Perform a measurement operation.

        Raises:
            DeviceRunningError: If the analyzer is currently running.
        """
        if self.status is not AnalyzerStatus.IDLE:
            raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested measurement operation cannot be performed.')
        else:
            self.status = AnalyzerStatus.RUNNING
            print('------------------------measurement started------------------------')
            try:
                pyautogui.press('enter')
                self.sleep_func(0.5)
                n = len(os.listdir(self.cache_folder_path))
                self.press_a_button('measure')
                print('measure button pressed')
            except Exception as e:
                print(e)
                raise
            else:
                # check the number of files and folders in the cache folder
                # if the number of files and folders increased, then the measurement is done
                print(f'waiting for measurement to finish - {n}')
                curr_t = time.time()
                while len(os.listdir(self.cache_folder_path)) == n:
                    self.sleep_func(0.2)
                    elapsed = time.time() - curr_t
                    print(f'elapsed time: {elapsed}')
                    if elapsed > self.time_out:
                        raise TimeOutError()
                print('------------------------measurement done------------------------')     
            finally:
                self.status = AnalyzerStatus.IDLE
                print('device status back to idle')
        
    def export(self) -> None:
        """
        Perform an export operation.

        Raises:
            DeviceRunningError: If the analyzer is currently running.
        """
        if self.status is not AnalyzerStatus.IDLE:
            raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested export operation cannot be performed.')
        else:
            self.status = AnalyzerStatus.RUNNING
            self.sample_name = self._name_after_time()
            print('------------------------export started------------------------')
            try:
                n = len(os.listdir(self.export_folder_path))
                # follow the steps below
                # 0. type in sample name
                self.press_a_button('sample_name')
                self.sleep_func(0.1)
                pyautogui.typewrite(self.sample_name)
                self.sleep_func(0.1)
                # 1. press button already done
                self.press_a_button('export')
                print('export button pressed')
                self.sleep_func(1.0)
                # 2. type in directory and hit enter
                pyautogui.typewrite(self.export_folder_path)
                self.sleep_func(0.1)
                pyautogui.press('enter')
                print('export folder path typed')
                self.sleep_func(1.0)
                # 3 choose save separate files
                # choose save in a new folder
                # hit export confirmation button
                self.press_a_button('separate_spectrum')
                self.sleep_func(0.1)
                self.press_a_button('new_folder')
                self.sleep_func(0.1)
                self.press_a_button('export_finish')
                print('export confirmation button pressed')
                self.sleep_func(0.5)
                self.press_a_button('delete')
                self.sleep_func(0.1)
                pyautogui.press('enter')
                print('cache file deteted')
                self.sleep_func(0.5)
                self.press_a_button('sync')
                self.sleep_func(0.5)
                pyautogui.press('enter')
                print('sync with LIBS analyzer')
                
            except Exception as e:
                print(e)
                raise
            else:
                print(f'waiting for export to finish - {n}')
                curr_t = time.time()
                while len(os.listdir(self.export_folder_path)) == n:
                    self.sleep_func(0.2)
                    elapsed = time.time() - curr_t
                    print(f'elapsed time: {elapsed}')
                    if elapsed > self.time_out:
                        raise TimeOutError()
                print('------------------------export done------------------------') 
            finally:
                self.status = AnalyzerStatus.IDLE
                print('device status back to idle')
    
    def analyze(self) -> List[float]:
        """
        Perform an analysis operation.

        Returns:
            List[float]: The analysis results.

        Raises:
            DeviceRunningError: If the analyzer is currently running.
        """
        if self.status is not AnalyzerStatus.IDLE:
            raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested analysis operation cannot be performed.')
        else:
            self.status = AnalyzerStatus.RUNNING
            print('------------------------analyzation started------------------------')
            try:
                spec_path = ''
                for f in os.listdir(self.export_folder_path + '/' + self.sample_name):
                    if f.endswith('1.csv'):
                        print(f)
                        spec_path = self.export_folder_path + '/' + self.sample_name + '/' + f
                        print(spec_path)
                        break
                
                res = self.find_all_peaks(spec_path)
            except Exception as e:
                print(e)
                raise
            else:
                print('------------------------analyzation done------------------------')
                return res
            finally:
                self.status = AnalyzerStatus.IDLE
                print('device status back to idle')

    def press_a_button(self, button_name: str) -> None:
        """
        Press the button with the given name.

        Args:
            button_name (str): The name of the button to press.

        Raises:
            UnkonwnButtonNameError: If the button name is unknown.
            ButtonNotFoundError: If the button is not found.
        """
        if button_name not in self.buttons:
            raise UnkonwnButtonNameError(f'The button name {button_name} is unknown.')
        elif not self.buttons[button_name]['found']:
            raise ButtonNotFoundError(f'The button {button_name} was not found.')
        else:
            pyautogui.click(self.buttons[button_name]['pos'])

    def _name_after_time(self) -> str:
        """
        Generate a sample name based on the current data and time. 

        Returns:
            str: generated sample name.
        """
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second
        
        return f'{year}_{month:02}_{day:02}_{hour:02}_{minute:02}_{second:02}'

    def find_all_buttons(self) -> None:
        """
        Find all buttons on the screen.
        """
        for button in self.buttons:
            
            self.buttons[button]['pos'] = self.locate_button_multi_scale(self.buttons[button]['img_path'])
            self.buttons[button]['found'] = True
            print(f'{button} found in {self.buttons[button]['pos']}')
        
        self._save_buttons_to_json()

    def _save_buttons_to_json(self) -> None:
        """
        Save self.buttons to a JSON file named button_positions.json in the root directory.
        """

        # Convert any non-serializable objects (e.g., tuples) to serializable types
        def convert(obj):
            if isinstance(obj, tuple):
                return list(obj)
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj

        buttons_serializable = convert(self.buttons)
        with open('button_positions.json', 'w') as f:
            json.dump(buttons_serializable, f, indent=4)

    def locate_button_multi_scale(self, button_template_path: str) -> Tuple[int, int]:
        """
        Locate the button on the screen using multi-scale template matching.

        Args:
            button_template_path (str): Path to the image file of the button template.

        Returns:
            Tuple[int, int]: The (x, y) coordinates of the center of the button.
        """
        screenshot = np.array(pyautogui.screenshot())
        gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

        template = cv2.imread(button_template_path, cv2.IMREAD_GRAYSCALE) # return shape(height * width, y * x)
        template = cv2.Canny(template, 50, 200)
        (template_height, template_width) = template.shape[:2]

        found = None
        # loop over the scales of the image
        for scale in np.linspace(0.2, 2.0, 10)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(gray, width = int(gray.shape[1] * scale))
            r = gray.shape[1] / float(resized.shape[1])
            # if the resized image is smaller than the template, then break
            # from the loop
            if resized.shape[0] < template_height or resized.shape[1] < template_width:
                break
            
            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = cv2.Canny(resized, 50, 200)
            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
            (_, max_val, _, max_loc) = cv2.minMaxLoc(result)
            # # check to see if the iteration should be visualized
            # if args.get("visualize", False):
            #     # draw a bounding box around the detected region
            #     clone = np.dstack([edged, edged, edged])
            #     cv2.rectangle(clone, (max_loc[0], max_loc[1]),
            #         (max_loc[0] + template_width, max_loc[1] + template_height), (0, 0, 255), 2)
            #     cv2.imshow("Visualize", clone)
            #     cv2.waitKey(0)
            # if we have found a new maximum correlation value, then update
            # the bookkeeping variable
            if found is None or max_val > found[0]:
                found = (max_val, max_loc, r)
        # unpack the bookkeeping variable and compute the (x, y) coordinates
        # of the bounding box based on the resized ratio
        (_, max_loc, r) = found
        (start_x, start_y) = (int(max_loc[0] * r), int(max_loc[1] * r))
        (end_x, end_y) = (int((max_loc[0] + template_width) * r), int((max_loc[1] + template_height) * r))
        
        # draw a bounding box around the detected result and display the image
        # cv2.rectangle(screenshot, (start_x, start_y), (end_x, end_y), (0, 0, 255), 2)
        # cv2.imshow("Image", screenshot)
        # cv2.waitKey(0)
        return (start_x + end_x) // 2, (start_y + end_y) // 2

    def find_all_peaks(self, csv_file_path: str) -> List[float]:
        """
        Find all peaks in the given CSV file.

        Args:
            csv_file_path (str): Path to the CSV file.

        Returns:
            List[float]: A list of detected peaks.
        """
        # todo: naive implementation for now
        df = pd.read_csv(csv_file_path, header=0)
        x = df['wavelength'].to_numpy(dtype=float)
        y = df['intensity'].to_numpy(dtype=float)

        ranges = [(669.0, 673.0)]
        areas = {}
        for start, stop in ranges:
            
            start_idx = np.where(x >= start)[0][0]
            stop_idx = np.where(x <= stop)[0][-1]

            area = np.trapezoid(y[start_idx:stop_idx+1], x[start_idx:stop_idx+1]) - (y[start_idx] + y[stop_idx]) * (x[stop_idx] - x[start_idx]) / 2
            areas[f'{start} - {stop}'] = area

        return areas
    
    
