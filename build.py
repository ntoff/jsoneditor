# build.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'json_editor.py',
    '--name=ParametersEditor',  # Name of the executable
    '--onefile',             # Create a single executable file
    '--windowed',            # Hide the console window
])