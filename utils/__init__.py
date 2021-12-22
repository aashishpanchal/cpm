import sys, os
from cpm.utils.config import __base_path__, __cpm_ascii_file__

def cpm_ascii() -> str:
    cpm: str = ''
    with open(os.path.join(__base_path__, __cpm_ascii_file__), 'r') as f:
        for line in f:
            cpm += ''.join(line)
    return cpm