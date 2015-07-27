# Building docs #
To build docs, run `make` in this directory. `make help` lists all targets.

## Requirements ##
Sphinx and Latex is needed to build doc.

**Spinx:**
```sh
pip install sphinx sphinxjp.themes.basicstrap
```

**Latex Ubuntu:**
```sh
sudo apt-get install -qq texlive texlive-latex-extra dvipng
```

**Latex Mac:**

Install the full [MacTex](http://www.tug.org/mactex/) installation or install the smaller [BasicTex](http://www.tug.org/mactex/morepackages.html) and add *ucs* and *dvipng* packages:
```sh
sudo tlmgr install ucs dvipng
```
