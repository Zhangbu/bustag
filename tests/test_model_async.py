import bustag.app.index as app_index


def test_train_model_task_result_shape(monkeypatch):
    def fake_train(model_name='logistic_regression'):
        return object(), {'f1': 0.88, 'accuracy': 0.9}, {'model_name': model_name, 'model_label': 'Fake'}

    monkeypatch.setattr(app_index.clf, 'train', fake_train)
    result = app_index._train_model_task('knn')

    assert result['model_name'] == 'knn'
    assert result['model_scores']['accuracy'] == 0.9
    assert result['model_metadata']['model_label'] == 'Fake'
