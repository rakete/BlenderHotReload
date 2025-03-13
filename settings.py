import bpy
import os
import subprocess
import shutil

class HOTRELOAD_OT_check_go_and_install(bpy.types.Operator):
    bl_idname = "hotreload.check_go_and_install"
    bl_label = "Install BlenderHotReload"
    bl_description = "Check if Go is installed and install BlenderHotReload.exe"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # Always allow this operator to be called
        return True

    def go_exists_in_path(self):
        go_cmd = "go.exe" if os.name == "nt" else "go"
        return shutil.which(go_cmd) is not None

    def get_addon_directory(self):
        return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    def execute(self, context):
        if not self.go_exists_in_path():
            self.report({'ERROR'}, "Go is not found in PATH. Please install Go from https://golang.org/dl/")
            return {'CANCELLED'}

        # Go exists in path, proceed with installation
        addon_dir = self.get_addon_directory()

        try:
            # Run go install in the cmd directory
            self.report({'INFO'}, "Installing BlenderHotReload.exe with 'go install'...")

            # Change to the go directory
            original_dir = os.getcwd()
            os.chdir(addon_dir)

            # Run go install which will place the executable in GOPATH/bin
            process = subprocess.Popen(
                ["go", "install", "."],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()

            # Change back to original directory
            os.chdir(original_dir)

            if process.returncode != 0:
                self.report({'ERROR'}, f"Failed to install: {stderr}")
                return {'CANCELLED'}

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error during installation: {str(e)}")
            return {'CANCELLED'}