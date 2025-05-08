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

hotreload_polling_active = False

def set_polling_active(state):
    global hotreload_polling_active
    hotreload_polling_active = state

def get_polling_active():
    global hotreload_polling_active
    return hotreload_polling_active

timer = None
wait_time = 2.0

class HOTRELOAD_OT_start_polling_operator(bpy.types.Operator):
    bl_idname = "hotreload.start_polling"
    bl_label = "Start Hot Reload Polling"

    duration = None

    def check_for_changes(self):
        global last_mod_time

        hotreload_path = os.path.join(WATCHED_DIR, ".hotreload")
        if not os.path.exists(hotreload_path):
            return

        last_change_path = hotreload_path + "_last_change"
        if not os.path.exists(last_change_path):
            return
        last_change = None
        with open(last_change_path, "r") as f:
            last_change = json.load(f)
        if last_change is None:
            return
        current_mod_time = os.path.getmtime(last_change_path)

        if current_mod_time > last_mod_time:
            print("Detected change in", last_change_path)
            with open(hotreload_path, "r") as f:
                last_mod_time = current_mod_time

                data = json.load(f)
                watched_dirs = data.get("watched_dirs")
                for watched_dir_and_module_names in watched_dirs:
                    watched_dir_split = watched_dir_and_module_names.split("|")
                    if len(watched_dir_split) > 1:
                        watched_dir, module_names = watched_dir_split
                        changed_dir = last_change.get("changed_dir")
                        if (changed_dir == "." and watched_dir == ".") or os.path.abspath(watched_dir) == os.path.abspath(changed_dir):
                            for module_name in module_names.split(","):
                                self.reload_module(module_name)

    def reload_module(self, module_name):
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

            self.report({'INFO'}, f"Reloaded module: {module_name}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to reload module: {e}")

    def modal(self, context, event):
        global timer, wait_time
        elapsed = None
        if self.duration is not None:
            elapsed = datetime.now() - self.duration
        if timer is not None and event.type == 'TIMER' and elapsed and elapsed.total_seconds() >= wait_time:
            self.check_for_changes()
            self.duration = datetime.now()
        return {'PASS_THROUGH'}

    def execute(self, context):
        global last_mod_time, changed_files, timer
        if timer is not None:
            return {'CANCELLED'}

        set_polling_active(True)
        self.report({'INFO'}, f"Polling for changes in {WATCHED_DIR} every {wait_time} seconds")

        self.duration = datetime.now()
        last_mod_time = time.time()
        changed_files = []
        wm = bpy.context.window_manager
        timer = wm.event_timer_add(wait_time, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class HOTRELOAD_OT_stop_polling_operator(bpy.types.Operator):
    bl_idname = "hotreload.stop_polling"
    bl_label = "Stop Hot Reload Polling"

    def execute(self, context):
        global timer
        if timer is None:
            return {'CANCELLED'}

        set_polling_active(False)
        self.report({'INFO'}, f"Stopped polling")

        wm = context.window_manager
        wm.event_timer_remove(timer)
        timer = None
        return {'FINISHED'}