# Milipah

Milipah is a Python and PyQt6-based desktop application designed to streamline and accelerate the process of sorting thousands of photos into various subfolders. It's the perfect tool for photographers or anyone who needs to quickly organize a massive collection of photos.

##  Key Features

- **Blazing Fast Keyboard Sorting:**
  - Use keys `1` through `9` to instantly assign a photo to your desired subfolder.
  - Navigate between photos using the `Left` / `Right` arrow keys or `A` / `D`.
  - Press `S` to skip a photo.
  - Press `Z` to undo your previous action.
- **Comprehensive Format Support:** Supports a wide range of image formats, including RAW formats (powered by `rawpy`), JPEG, PNG, and more.
- **Session Management:** Your sorting progress is automatically saved. You can close the application at any time and resume your sorting session in the same folder later without losing any data.
- **Customizable Subfolders:** Add new subfolders on the fly directly within the app, complete with color-coded tags for quick visual identification.
- **Modern Interface:** Features a responsive filmstrip (thumbnail list) at the bottom and a main preview area that renders photos extremely fast.
- **Batch Move Operation:** Once you're done sorting, simply click "Move" to execute the physical file transfer of all photos into their assigned subfolders.

## Installation

### For Windows Users (Recommended)
You don't need to install Python. Simply download and run the installer:
1. Go to the [Releases](https://github.com/dikapradnyanta/milipah/releases) page.
2. Download the latest `Milipah-Setup.exe`.
3. Double-click the installer and follow the instructions to install the app on your computer.

### For Developers (Run from Source)
This application requires **Python 3.10 or newer**.

1. **Clone this repository or download the source code:**
   ```bash
   git clone https://github.com/dikapradnyanta/milipah.git
   cd milipah
   ```

2. **(Optional but recommended) Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # For Windows:
   venv\Scripts\activate
   # For macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   The application requires `PyQt6`, `rawpy`, `Pillow`, and `numpy`.
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Building the Windows Installer
If you are developing the app and want to build the `.exe` installer yourself:

1. Double-click `build_exe.bat` (or run it in the terminal) to install PyInstaller and generate the `dist\Milipah` executable directory.
2. Ensure you have [Inno Setup 6](https://jrsoftware.org/isinfo.php) installed.
3. Open the `milipah.iss` script with Inno Setup Compiler.
4. Click **Compile**.
5. The final installer will be generated inside the `installer\` directory as `Milipah-Setup.exe`.

## How to Use

1. Launch the application and select a **source folder** (the main folder containing the photos you want to sort).
2. Add your target subfolders (e.g., "Good", "Bad", "Print").
3. Start the sorting session.
4. In the main window, look at the displayed photo. Press keys `1` - `9` corresponding to the subfolder order on the left sidebar to assign the photo to that subfolder.
5. Use the Left/Right arrow keys if you need to review photos, or press `Z` if you made a mistake.
6. Once you're done, click the **Move** button on the right panel to execute the actual file moves to their target subfolders.
