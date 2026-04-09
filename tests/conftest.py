import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('TESTING', '1')
os.environ.setdefault('BUSTAG_ADMIN_PASSWORD', 'test-admin-password')

from bustag.util import init as init_app_config

init_app_config(force=True)


@pytest.fixture(scope="session", autouse=True)
def start():
    print("\n **** start test ****")
