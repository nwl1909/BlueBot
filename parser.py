import json
import re
from pathlib import Path


with open("apps.json", encoding="utf8") as f:

    APPS = json.load(f)
