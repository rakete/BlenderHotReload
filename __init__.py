bl_info = {
    "name": "BlenderHotReload Addon",
    "blender": (2, 80, 0),
    "category": "Development",
    "version": (1, 0, 0),
    "author": "Andrreas Raster",
    "description": "A Blender addon for hot reloading other addons.",
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
}

import bpy
import importlib

from BlenderHotReload.reload import StartPollingOperator, StopPollingOperator, WATCHED_DIR

def register():
    if not WATCHED_DIR:
        print("HotReload: No directory or module specified. Exiting.")
        return

    bpy.utils.register_class(StartPollingOperator)
    bpy.utils.register_class(StopPollingOperator)

def unregister():
    if not WATCHED_DIR:
        return

    bpy.ops.wm.stop_polling()

    bpy.utils.unregister_class(StartPollingOperator)
    bpy.utils.unregister_class(StopPollingOperator)

if __name__ == "__main__":
    register()
