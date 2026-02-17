import sys, json, datetime

current_prog = ""

if sys.platform == "darwin":
    from AppKit import NSWorkspace, NSApplication
    NSApplication.sharedApplication()         
    _workspace = NSWorkspace.sharedWorkspace()

def check_current_program():
    if sys.platform == "darwin":
        info = _workspace.activeApplication()       
        return info.get("NSApplicationName")
    else:
        # to be implemented for linux
        pass

def get_last_timestamp(filepath: str):
    try:
        with open(filepath, 'r') as f:
           lines = f.readlines()
           if not lines:
               return None
           last_entry = json.loads(lines[-1])
           time_str = last_entry['timestamp']
           return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
    except (FileNotFoundError, IndexError, ValueError):
        return None
