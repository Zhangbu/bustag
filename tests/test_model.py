import pytest

pytest.importorskip('sklearn')

from bustag.model import classifier as clf


def test_create_model_default():
    model = clf.create_model()
    assert model is not None


def test_create_model_invalid():
    with pytest.raises(ValueError):
        clf.create_model('unknown-model')


def test_list_models():
    model_names = {model['name'] for model in clf.list_models()}
    assert 'logistic_regression' in model_names
    assert 'knn' in model_names


def test_evaluate_handles_single_class_predictions():
    scores = clf.evaluate([1, 1, 1], [1, 1, 1], [1])
    assert scores['f1'] == 1.0
    assert scores['tp'] == 3
    assert scores['tn'] == 0


def test_train_model(monkeypatch):
    dataset = {
        'X_train': [[0, 1], [1, 0], [1, 1], [0, 0], [1, 0], [0, 1]],
        'X_test': [[1, 1], [0, 0]],
        'y_train': [1, 0, 1, 0, 0, 1],
        'y_test': [1, 0],
        'target_names': [0, 1],
        'class_counts': {0: 3, 1: 3},
        'feature_count': 2,
        'total': 200,
    }

    monkeypatch.setattr(clf, 'prepare_data', lambda: dataset)
    captured = {}

    def fake_dump_model(path, models):
        captured['path'] = path
        captured['models'] = models

    monkeypatch.setattr(clf, 'dump_model', fake_dump_model)
    model, scores, metadata = clf.train()
    assert model is not None
    assert scores['accuracy'] >= 0
    assert metadata['model_name'] == clf.DEFAULT_MODEL_NAME
    assert 'models' in captured


def test_recommend(monkeypatch):
    monkeypatch.setattr(clf, 'prepare_predict_data', lambda: (['A', 'B'], [[0, 1], [1, 0]]))
    monkeypatch.setattr(clf, 'predict', lambda X: [1, 0])

    saved = []

    class DummyRate:
        def __init__(self, rate_type, rate_value, item_id):
            self.rate_type = rate_type
            self.rate_value = rate_value
            self.item_id = item_id

        def save(self):
            saved.append((self.item_id, self.rate_value))

    monkeypatch.setattr(clf, 'ItemRate', DummyRate)
    total, count = clf.recommend()
    assert total == 2
    assert count == 1
    assert saved == [('A', 1), ('B', 0)]
