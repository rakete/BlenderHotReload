# Blender Hot Reload Addon

A Blender addon for automatically reloading other addons when changes are made to their files. It exists because I wanted something that isn't specifically made for one IDE, but instead can be used with anything from vim to Intellij IDEA. 

It is implemented with a smaller runner.go program that starts blender with a WATCHED_DIR environment variable, which is then used inside blender by the BlenderHotReload python addon.

The runner.go program recursively watches all files under the directory where it was started for changes, and everytime something changes it notifies the BlenderHotReload addon about it. The addon will then reload the addon that was configured to be reloaded on a change. 

## Installation

### ~~From GitHub Release~~

~~1. Download the latest release from [GitHub](https://github.com/rakete/BlenderHotReload/releases)~~  
~~2. Open Blender and go to `Edit > Preferences > Addons`~~  
~~3. Click "Install" button in top right corner~~  
~~4. Select the downloaded zip file~~  
~~5. Enable the addon in the list~~

### Manually until I write a GitHub workflow

1. Clone the repository
2. go install
3. Manually copy entire repository in `Blender\\scripts\\addons` directory
4. Setup .hotreload (see below)
4. Run BlenderHotReload.exe
5. Enable plugin in Blender
6. Start polling operator by clicking "Hot Reload" in upper right corner

## Usage

You need two parts, the BlenderHotReload addon needs to be installed in blender, and BlenderHotReload runner needs to be installed so that you can run it from a terminal (put the installation directory in your $PATH).

You need to copy the `.hotreload.example` file to `.hotreload` in your addon directory. And change it so that you have `blender_path` and `watched_dirs` customized for your setup. 

Once you start the runner from your addon source directory it will start a blender instance and watch the source directory for changes.

Inside Blender you can click "Hot Reload" in the upper right corner to enable the hot reload polling. As long as that is active blender will automatically reload modules where any file inside the watched dirs is changed. You can stop the polling with the little X button besides the "Hot Reload" button.

Any change that the runner detects is written to the `.hotreload` file as `last_change` field. When the `.hotreload` changes, the polling operator will reload the addons that have been configured in the `watched_dirs` config option.

## Configuration

The addon uses a `.hotreload` config file to customize its behavior.

### Example Config File

```json
{
    "ignored_patterns": [
        ".vscode",
        "__pycache__"
    ],
    "blender_path": "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe",
    "watched_dirs": [
        ".|Module1,Module2",
        "C:\\Users\\Blender\\AppData\\Roaming\\Blender Foundation\\Blender\\scripts\\addons\\OtherAddon|Module3,Module4"
    ]
}
```

### Config Options

- `ignored_patterns`: Patterns of files/directories to ignore
- `blender_path`: Full path to Blender executable
- `watched_dirs`: Directories to watch for changes (format: "path|comma_seperated_module_names", you need to include "." as first element, which will be the working directory where BlenderHotReload.exe is started, the module names are the names of the modules that will be reloaded when something changes in path)