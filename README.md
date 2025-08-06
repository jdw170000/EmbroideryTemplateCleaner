# Embroidery Template Cleaner

This is a simple utility application built using Python and Tkinter to help clean up embroidery template directories. It recursively deletes files with specified extensions, streamlining the directory structure.

Embroidery template packages often contain duplicate files in numerous file formats because different embroidery machines support different formats. While template vendors need to include all the formats for broad compatibility, individual users typically only require a few specific ones. This utility allows users to easily remove unwanted template formats, reducing clutter and disk space usage.

## How to Use

1.  **Download:** Obtain the executable for your operating system from the [Releases](https://github.com/jdw170000/EmbroideryTemplateCleaner/releases) section.
2.  **Run:** Execute the application.
3.  **Select Directory:** Click the "Browse" button to choose the directory containing embroidery files you want to clean.
4.  **Select Extensions:** Check the boxes next to the file extensions you want to delete.
5.  **Delete:** Click the "Delete Selected File Extensions" button to start the deletion process.

*Use with caution. Deleting files is an irreversible action. Make sure the directory selected is the correct one.*

## Building From Source

If you prefer to build the application from the source code:

1.  **Prerequisites:**
    *   Python 3.12 or later installed
    *   `PyInstaller` installed: `pip install pyinstaller`
2.  **Clone:** Clone the repository:
    ```bash
    git clone git@github.com:jdw170000/EmbroideryTemplateCleaner.git
    ```
3.  **Build:** Use the PyInstaller build script to create the executable:
    ```bash
    python build.py
    ```
4.  **Executable:** The executable will be located in the `dist` directory.