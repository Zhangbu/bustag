import pytest

pytest.importorskip('sklearn')

from bustag.model.prepare import build_dataframe, load_data, prepare_predict_data, process_data


def test_load_data():
    items = load_data()
    print(len(items))
    item = items[0]
    print(item.fanhao, item.tags_dict)
    assert len(items) > 0


def test_process_data():
    df = build_dataframe(load_data())
    X, y, mlb = process_data(df)
    print(X.shape)
    print(y.shape)
    assert X.shape[0] == len(y)
    assert len(mlb.classes_) >= 0


def test_prepare_predict_data():
    ids, X = prepare_predict_data()
    if len(ids) == 0:
        print('No unrated items found')
        return
    print(X.shape)
    print(X[0])
    print(ids)
