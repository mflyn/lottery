#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

from src.gui.main_window import LotteryToolsGUI

if __name__ == '__main__':
    app = LotteryToolsGUI()
    app.run()