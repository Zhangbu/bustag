from pathlib import Path

import pytest

pytest.importorskip('sklearn')

from bustag.model.persist import load_model
from bustag.util import get_data_path


def test_load_model():
    path = Path(get_data_path('model/label_binarizer.pkl'))
    if not path.exists():
        pytest.skip('label_binarizer.pkl not found')
    mlb = load_model(str(path))
    assert len(mlb.classes_) > 0
    print(mlb.classes_[:10])
    print(f'total tags: {len(mlb.classes_)}')
