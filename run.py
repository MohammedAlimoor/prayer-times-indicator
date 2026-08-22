#!/usr/bin/env python3
"""مشغّل مباشر من مجلد المشروع بدون تثبيت."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prayertimes.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
