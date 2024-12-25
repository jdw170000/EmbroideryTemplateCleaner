import PyInstaller.__main__

import pathlib
import shutil

if pathlib.Path('./build').exists():
    shutil.rmtree('./build/')
if pathlib.Path('./dist').exists():
    shutil.rmtree('./dist')

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--name', 'empty_folder_cleaner',
    '--icon', 'icon.ico'
])