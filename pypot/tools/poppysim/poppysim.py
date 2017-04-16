#!/usr/bin/env python
# coding: utf-8
"""
Crée un poppy dans vrep et lance un shell interactif IPython
"""

from IPython.config.loader import Config as ipConfig
from IPython.terminal.embed import InteractiveShellEmbed
from poppy.creatures import PoppyHumanoid

if __name__ == '__main__':
    cfg = ipConfig()
    cfg.TerminalInteractiveShell.confirm_exit = False
    shell = InteractiveShellEmbed(config=cfg, user_ns={ 'poppy' : PoppyHumanoid(simulator='vrep') })
    shell()
