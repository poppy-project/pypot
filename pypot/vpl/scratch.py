from .download import download_vpl_interactively

# Scratch latest release download to local data directory in userspace
VPL_APP_URL = "https://github.com/poppy-project/scratch-poppy/releases/latest/download/scratch-application.zip"
VPL_APP_NAME = "scratch-application"
VPL_EXTRACT_ZIP_ROOT = True 

def download_scratch_interactively():
    """
    Download the Scratch v1.0-beta Programming language web app and returns its path.
    If it couldn't be downloaded, return None
    """
    return download_vpl_interactively(VPL_APP_NAME, VPL_APP_URL, VPL_EXTRACT_ZIP_ROOT)
