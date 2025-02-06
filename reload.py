import bpy
import os
import time
import sys
from datetime import datetime
import json

# Define the directory to watch
WATCHED_DIR = os.getenv("HOTRELOAD_WATCHED_DIR", "")

# Store the last modification time and changed files
last_mod_time = datetime.now().timestamp()


def check_for_changes():
    global last_mod_time

    hotreload_path = os.path.join(WATCHED_DIR, ".hotreload")
    if os.path.exists(hotreload_path):
        current_mod_time = os.path.getmtime(hotreload_path)

        if current_mod_time > last_mod_time:
            print("Detected change in", hotreload_path)
            with open(hotreload_path, "r") as f:
                last_mod_time = current_mod_time
                data = json.load(f)
                last_change = data.get("last_change")
                watched_dirs = data.get("watched_dirs")
                for watched_dir_and_module_names in watched_dirs:
                    watched_dir_split = watched_dir_and_module_names.split("|")
                    if len(watched_dir_split) > 1:
                        watched_dir, module_names = watched_dir_split
                        changed_dir = last_change.get("changed_dir")
                        if (changed_dir == "." and watched_dir == ".") or os.path.abspath(watched_dir) == os.path.abspath(changed_dir):
                            for module_name in module_names.split(","):
                                reload_module(module_name)

def reload_module(module_name):
    try:
        # Disable the addon
        print("Disabling", module_name)
        bpy.ops.preferences.addon_disable(module=module_name)

        # Delete the module from sys.modules
        for name in list(sys.modules.keys()):
            if name == module_name or name.startswith(module_name + "."):
                print(f"Deleting module: {name}")
                del sys.modules[name]

        # Enable the addon
        print("Enabling", module_name)
        bpy.ops.preferences.addon_enable(module=module_name)

        print(f"Reloaded module: {module_name}")
    except Exception as e:
        print(f"Failed to reload module: {e}")

timer = None
wait_time = 2.0

class StartPollingOperator(bpy.types.Operator):
    bl_idname = "wm.start_polling"
    bl_label = "Start Hot Reload Polling"

    duration = None

    def modal(self, context, event):
        global timer, wait_time
        elapsed = None
        if self.duration is not None:
            elapsed = datetime.now() - self.duration
        if timer is not None and event.type == 'TIMER' and elapsed and elapsed.total_seconds() >= wait_time:
            check_for_changes()
            self.duration = datetime.now()
        return {'PASS_THROUGH'}

    def execute(self, context):
        print("Starting polling")

        global last_mod_time, changed_files, timer
        if timer is not None:
            return {'CANCELLED'}

        self.duration = datetime.now()
        last_mod_time = time.time()
        changed_files = []
        wm = context.window_manager
        timer = wm.event_timer_add(wait_time, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class StopPollingOperator(bpy.types.Operator):
    bl_idname = "wm.stop_polling"
    bl_label = "Stop Hot Reload Polling"

    def execute(self, context):
        print("Stopping polling")

        global timer
        if timer is None:
            return {'CANCELLED'}

        wm = context.window_manager
        wm.event_timer_remove(timer)
        timer = None
        return {'FINISHED'}