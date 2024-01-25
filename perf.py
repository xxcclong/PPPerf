import sys
import platform
import argparse
from influxdb import InfluxDBClient
import os
from datetime import datetime
import time
from pynput import mouse, keyboard

parser = argparse.ArgumentParser()
parser.add_argument("--ip", type=str, default="172.23.0.1")
parser.add_argument("--port", type=int, default=8086)
parser.add_argument("--database_name", type=str, default="hkz")
parser.add_argument("--username", type=str)
parser.add_argument("--passwd", type=str)
args = parser.parse_args()
print(args)

os_name = platform.system().lower()
if "windows" in os_name:
    import win32gui
    import win32process
    import psutil
    def get_app_name():
        fgWindow = win32gui.GetForegroundWindow()
        threadID, ProcessID = win32process.GetWindowThreadProcessId(fgWindow)
        procname = psutil.Process(ProcessID)
        name = procname.name().lower()
        return name
elif "darwin" in os_name:
    from AppKit import NSWorkspace
    def get_app_name():
        window = NSWorkspace.sharedWorkspace().activeApplication()
        if window is not None:
            name = window['NSApplicationName'].lower()
        else:
            name = "None"
        return name
else:
    assert False, f"unsupported OS {os_name}"

passwd = args.passwd

client = InfluxDBClient(host=args.ip, port=args.port, username=args.database_name, password=passwd, timeout=30000)
client.switch_database(args.database_name)

keycnt = 0
def on_press(key):
    global keycnt
    keycnt += 1

listener = keyboard.Listener(on_press=on_press)
listener.start()

clk_cnt = 0
move_cnt = 0
scroll_cnt = 0
move_time = time.time()
scroll_time = time.time()

def on_move(x, y):
    global move_time, move_cnt
    move_time2 = time.time()
    if move_time2 - move_time > 0.5:
        move_cnt += 1
        move_time = move_time2

def on_click(x, y, button, pressed):
    global clk_cnt
    clk_cnt += 1

def on_scroll(x, y, dx, dy):
    global scroll_time, scroll_cnt
    scroll_time2 = time.time()
    if scroll_time2 - scroll_time > 0.5:
        scroll_cnt += 1
        scroll_time = scroll_time2

listener2 = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll)
listener2.start()

d = {}
d["measurement"] = "keyboard"
d["tags"] = {"user": args.username}

def get_work_type():
    name = None
    try:
        name = get_app_name()
    except:
        return "uncategorized"
    if name is None:
        return "uncategorized"
    return str(name)  

print("start profiling")

while True:
    time.sleep(1)
    d["fields"] = {"times": keycnt, "mouse_times": move_cnt + scroll_cnt + clk_cnt}
    move_cnt = 0
    scroll_cnt = 0
    clk_cnt = 0
    keycnt = 0
    wtype = get_work_type()
    d["tags"]["app"] = wtype
    if not client.write_points([d]):
        print('Data writing error')
