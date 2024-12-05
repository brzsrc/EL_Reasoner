"""
Created by: Eduardo Lira
Date: Nov 14 2023
Name: utils.py

Description:
   some useful (but not critical) utilities
"""

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def bold(s: str) -> str:
    return color.BOLD + s + color.END

def underline(s: str) -> str:
    return color.UNDERLINE + s + color.END

def colorText(c: color, s: str) -> str:
    return c + s + color.END

