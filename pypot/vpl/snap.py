from .download import download_vpl_interactively

# Snap 5.4.5 application download to local data directory in userspace
VPL_APP_URL = "https://codeload.github.com/jmoenig/Snap/zip/v5.4.5"
VPL_APP_NAME = "Snap-5.4.5"
VPL_EXTRACT_ZIP_ROOT = True 

def download_snap_interactively():
    """
    Download the Snap 5.4.5 Programming langage web app and returns its path.
    If it couldn't be downloaded, return None
    """
    return download_vpl_interactively(VPL_APP_NAME, VPL_APP_URL, VPL_EXTRACT_ZIP_ROOT)
