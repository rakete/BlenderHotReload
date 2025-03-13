bl_info = {
    "name": "BlenderHotReload Addon",
    "blender": (4, 3, 0),
    "category": "Development",
    "version": (1, 0, 0),
    "author": "Andreas Raster",
    "description": "A Blender addon for hot reloading other addons.",
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
}

import bpy
import importlib

from .reload import (
    get_polling_active,
    set_polling_active,
    HOTRELOAD_OT_start_polling_operator,
    HOTRELOAD_OT_stop_polling_operator,
    WATCHED_DIR,
)
from .settings import HOTRELOAD_OT_check_go_and_install

class HotReloadAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

def draw_hotreload_buttons(self, context):
    layout = self.layout
    row = layout.row(align=True)

    is_polling = get_polling_active()

    c1 = row.column(align=True)
    c1.operator("hotreload.start_polling", text="Hot Reload", icon='FILE_REFRESH', depress=is_polling)
    c2 = row.column(align=True)
    c2.operator("hotreload.stop_polling", text="", icon='CANCEL')
    c2.enabled = is_polling

def register():
    if not WATCHED_DIR:
        print("HotReload: No directory or module specified. Exiting.")
        return

    bpy.utils.register_class(HotReloadAddonPreferences)
    bpy.utils.register_class(HOTRELOAD_OT_start_polling_operator)
    bpy.utils.register_class(HOTRELOAD_OT_stop_polling_operator)

    bpy.utils.register_class(HOTRELOAD_OT_check_go_and_install)

    bpy.types.VIEW3D_HT_header.append(draw_hotreload_buttons)

    # If you want to add it to other headers as well:
    # bpy.types.TOPBAR_HT_upper_bar.append(draw_hotreload_button)  # Top-most header
    # bpy.types.TEXT_HT_header.append(draw_hotreload_button)  # Text editor header
    # bpy.types.NODE_HT_header.append(draw_hotreload_button)  # Node editor header


def unregister():
    if not WATCHED_DIR:
        return

    bpy.ops.hotreload.stop_polling()

    bpy.types.VIEW3D_HT_header.remove(draw_hotreload_buttons)

    bpy.utils.unregister_class(HOTRELOAD_OT_start_polling_operator)
    bpy.utils.unregister_class(HOTRELOAD_OT_stop_polling_operator)

    bpy.utils.unregister_class(HOTRELOAD_OT_check_go_and_install)

    bpy.utils.unregister_class(HotReloadAddonPreferences)

if __name__ == "__main__":
    register()
