"""Install, update and manage DINC.

    python DINC.py            open the menu
    python DINC.py install    first time setup
    python DINC.py update     pull new code and images, and run migrations
    python DINC.py --help     everything else

The code lives in the dinc/ folder. This file only starts it.
"""

import sys

if sys.version_info < (3, 9):
    sys.exit("DINC.py needs Python 3.9 or newer.")

from dinc.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
