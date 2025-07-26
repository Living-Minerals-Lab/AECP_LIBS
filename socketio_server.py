from calendar import TUESDAY
from typing import override
import os
import socketio
import pyautogui
import cv2
import numpy as np
import imutils
import eventlet
from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops
from enum import Enum
import time
import threading
from libs_analyzer import LIBSAnalyzer, AnalyzerStatus, DeviceRunningError, TimeOutError, ButtonNotFoundError, UnkonwnButtonNameError

class Z300SocketIOServer(LIBSAnalyzer):
    """
    A socket.io server class for the SciAps Z300 LIBS gun based on GUI automation.
    """
    def __init__(self, 
                 cache_folder_path, 
                 export_folder_path, 
                 measure_button_img_path,
                 sample_name_input_img_path,
                 export_button_img_path,
                 separate_spectrum_button_img_path,
                 new_folder_button_img_path,
                 export_finish_button_img_path,
                 delete_button_img_path,
                 sync_button_img_path,
                 time_out):
        
        self.sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
        self.app = socketio.WSGIApp(self.sio)

        super().__init__(cache_folder_path, export_folder_path, measure_button_img_path, sample_name_input_img_path,
                         export_button_img_path, separate_spectrum_button_img_path, new_folder_button_img_path, 
                         export_finish_button_img_path, delete_button_img_path, sync_button_img_path, time_out, sleep_func=self.sio.sleep)
        
        # self.libs_analyzer = LIBSAnalyzer(cache_folder_path='C:/Users/LIBS_VM/sciaps/cache', export_folder_path='Y:/')
        
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        # self.sio.on('pull_trigger', self.on_pull_trigger)
        # self.sio.on('set_desktop_id', self.on_set_desktop_id)
        self.sio.on('measure', self.on_measure)
        self.sio.on('export', self.on_export)
        self.sio.on('analyze', self.on_analyze)
        self.sio.on('find_buttons', self.on_find_buttons)
        self.sio.on('change_export_path', self.on_change_export_path)

    # @override
    # def measure(self):
    #     """
    #     Perform a measurement operation.

    #     Raises:
    #         DeviceRunningError: If the analyzer is currently running.
    #     """
    #     if self.status is not AnalyzerStatus.IDLE:
    #         raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested measurement operation cannot be performed.')
    #     else:
    #         self.status = AnalyzerStatus.RUNNING
    #         print('------------------------measurement started------------------------')
    #         try:
    #             n = len(os.listdir(self.cache_folder_path))
    #             self.press_a_button('measure')
    #             print('measure button pressed')  
    #         except Exception as e:
    #             print(e)
    #             raise
    #         else:
    #             # check the number of files and folders in the cache folder
    #             # if the number of files and folders increased, then the measurement is done
    #             print(f'waiting for measurement to finish - {n}')
    #             curr_t = time.time()
    #             while len(os.listdir(self.cache_folder_path)) == n:
    #                 self.sio.sleep(0.2)
    #                 elapsed = time.time() - curr_t
    #                 print(f'elapsed time: {elapsed}')
    #                 if elapsed > self.time_out:
    #                     raise TimeOutError()
    #             print('------------------------measurement done------------------------')    
    #         finally:
    #             self.status = AnalyzerStatus.IDLE
    #             print('device back to idle')
    
    # @override
    # def export(self) -> None:
    #     """
    #     Perform an export operation.

    #     Raises:
    #         DeviceRunningError: If the analyzer is currently running.
    #     """
    #     if self.status is not AnalyzerStatus.IDLE:
    #         raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested export operation cannot be performed.')
    #     else:
    #         self.status = AnalyzerStatus.RUNNING
    #         self.sample_name = self._name_after_time()
    #         try:
    #             n = len(os.listdir(self.export_folder_path))
    #             # follow the steps below
    #             # 0. type in sample name
    #             self.press_a_button('sample_name')
    #             pyautogui.typewrite(self.sample_name)
    #             # 1. press button already done
    #             self.press_a_button('export')
    #             print('export button pressed')
    #             self.sio.sleep(2.0)
    #             # 2. type in directory and hit enter
    #             pyautogui.typewrite(self.export_folder_path)
    #             pyautogui.press('enter')
    #             print('export folder path typed')
    #             self.sio.sleep(2.0)
    #             # 3 choose save separate files
    #             # choose save in a new folder
    #             # hit export confirmation button
    #             self.press_a_button('separate_spectrum')
    #             self.press_a_button('new_folder')
    #             self.press_a_button('export_finish')
    #             print('export confirmation button pressed')
    #         except Exception as e:
    #             print(e)
    #             raise
    #         else:
    #             print(f'waiting for export to finish - {n}')
    #             curr_t = time.time()
    #             while len(os.listdir(self.export_folder_path)) == n:
    #                 self.sio.sleep(0.2)
    #                 elapsed = time.time() - curr_t
    #                 print(f'elapsed time: {elapsed}')
    #                 if elapsed > self.time_out:
    #                     raise TimeOutError()
    #             print('export done') 
    #         finally:
    #             self.status = AnalyzerStatus.IDLE
    #             print('device back to idle')

    def on_connect(self, sid, environ, auth):
        print('connect ', sid)

    def on_disconnect(self, sid):
        print('disconnect ', sid)

    def on_measure(self, sid, data):
        if self.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                self.measure()
            except Exception as e:
                print(e)
                return str(e)
            else:
                return 'success'
    
    def on_export(self, sid, data):
        if self.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                self.export()
            except Exception as e:
                print(e)
                return str(e)
            else:
                return 'success'
    
    def on_analyze(self, sid, data):
        if self.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                res = self.analyze()
            except Exception as e:
                return str(e), {'not_found': 0.0}
            else:
                return 'success', res 

    def on_find_buttons(self, sid, data):
        self.find_all_buttons()
        return [self.buttons[button]['pos'] for button in self.buttons]
    # def on_set_desktop_id(self, sid, data):
    #     self.desktop_id = data
    #     print(f'Virtual desktop id for Profile Builder has been set to {self.desktop_id}.')

    def on_change_export_path(self, sid, new_path: str):
        if self.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                self.set_export_folder_path(new_path)
            except Exception as e:
                print(e)
                return str(e)
            else:
                return 'success'

    def update_status(self):
        while True:
            self.sio.sleep(0.5)
            self.sio.emit('status', self.status.name)
        

if __name__ == '__main__':
    z300_web_server = Z300SocketIOServer(cache_folder_path='C:/Users/Whittaker/sciaps/cache/Z300-0915', 
                                         export_folder_path='C:/Users/Whittaker/Documents/20250623Scanning',
                                         measure_button_img_path='button_templates/measure_button.png',
                                         sample_name_input_img_path='button_templates/sample_name_input.png',
                                         export_button_img_path='button_templates/export_button.png',
                                         separate_spectrum_button_img_path='button_templates/separate_spectrum_button.png',
                                         new_folder_button_img_path='button_templates/new_folder_button.png',
                                         export_finish_button_img_path='button_templates/export_finish_button.png',
                                         delete_button_img_path='button_templates/delete_button.png',
                                         sync_button_img_path='button_templates/sync_button.png',
                                         time_out=15.0)
    z300_web_server.sio.start_background_task(z300_web_server.update_status)
    eventlet.wsgi.server(eventlet.listen(('', 1234)), z300_web_server.app)


