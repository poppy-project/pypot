import sys
import tempfile
from wget import download
from urllib.error import URLError
from zipfile import ZipFile
from pathlib import Path

def get_pypot_datadir(app_name="pypot"):
    """
    Returns pypot's directory for peristent data.
    Attempt creation if create==True.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """
    home = Path.home()

    if sys.platform == "win32":
        data_dir = home / "AppData/Roaming"
    elif sys.platform == "linux":
        data_dir = home / ".local/share"
    elif sys.platform == "darwin":
        data_dir = home / "Library/Application Support"
    else:
        raise ValueError("Can't find the user data directory of your platform '{}'".format(sys.platform))

    #app_name = app_name if version is None else app_name + "-" + str(version)
    pypot_dir = data_dir / app_name
    return pypot_dir


def download_vpl_interactively(vpl_app_name, vpl_app_url, extract=False):
    """
    Download the specified Visual Programming langage web app and returns its path.
    If it couldn't be downloaded, return None
    """
    pypot_datadir = get_pypot_datadir()
    vpl_dir = pypot_datadir / vpl_app_name
    actual_vpl_dir = vpl_dir / vpl_app_name if extract else vpl_dir
    
    if vpl_dir.is_dir():
        return actual_vpl_dir
    else:
        while True:
            response = input("This is the first time you are launching {}, it needs to be downloaded first. Proceed? [Y/n] ".format(vpl_app_name))
            if response.lower() in ["y", ""]:
                try:
                    vpl_dir.mkdir(parents=True)
                except FileExistsError:
                    pass
                print("Downloading...")
                try:
                    downloaded_app = download(vpl_app_url, tempfile.gettempdir())
                except URLError as e:
                    print("Cannot download the {} app from {}: {}".format(vpl_app_name, vpl_app_url, str(e)), file=sys.stderr)
                else:
                    try:
                        with ZipFile(downloaded_app, 'r') as archive:
                            archive.extractall(vpl_dir)
                    except FileNotFoundError:
                        print("Couldn't extract {} from zipfile".format(vpl_app_name))
                    else:
                        return actual_vpl_dir
            else:
                print("Download aborted by user", file=sys.stderr)
                return None
