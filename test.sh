#!/bin/sh

# if ls Contributors.txt > /dev/null
# then
#     echo "Passed Contributors.txt test"
# else
#     echo "Failed the Contributors.txt test"
#     exit 1
# fi

import glob
files = glob.glob("CONTRIBUTORS.TXT")
assert(files)