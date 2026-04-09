"""
Prepare data for model training and prediction.
"""
from __future__ import annotations

from collections import Counter

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer

from bustag.model.persist import dump_model, load_model
from bustag.spider.db import RATE_TYPE, get_items
from bustag.util import MODEL_PATH, get_data_path

BINARIZER_PATH = MODEL_PATH + 'label_binarizer.pkl'


def load_data():
    """
    Load labeled items from the database.
    """
    items, _ = get_items(rate_type=RATE_TYPE.USER_RATE.value, rate_value=None, page=None)
    return items


def as_dict(item):
    tags_set = set()
    for tags in item.tags_dict.values():
        for tag in tags:
            tags_set.add(tag)
    return {
        'id': item.fanhao,
        'title': item.title,
        'fanhao': item.fanhao,
        'url': item.url,
        'add_date': item.add_date,
        'tags': sorted(tags_set),
        'cover_img_url': item.cover_img_url,
        'target': int(item.rate_value),
    }


def build_dataframe(items):
    dicts = [as_dict(item) for item in items]
    return pd.DataFrame(
        dicts,
        columns=['id', 'title', 'fanhao', 'url', 'add_date', 'tags', 'cover_img_url', 'target'],
    )


def process_data(df, *, fit=True):
    """
    Transform tags into model features.
    """
    feature_df = df[['tags']].copy()
    target = df['target'].astype(int).to_numpy() if 'target' in df.columns else None

    if fit:
        mlb = MultiLabelBinarizer()
        X = mlb.fit_transform(feature_df['tags'].values)
        dump_model(get_data_path(BINARIZER_PATH), mlb)
    else:
        mlb = load_model(get_data_path(BINARIZER_PATH))
        X = mlb.transform(feature_df['tags'].values)
    return X, target, mlb


def split_data(X, y):
    """
    Split train/test data while preserving class distribution when possible.
    """
    class_counts = Counter(y)
    stratify = y if len(class_counts) > 1 and min(class_counts.values()) >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )
    return X_train, X_test, y_train, y_test


def prepare_data():
    items = load_data()
    df = build_dataframe(items)
    if df.empty:
        raise ValueError('没有可用于训练的打标数据')

    X, y, mlb = process_data(df, fit=True)
    X_train, X_test, y_train, y_test = split_data(X, y)
    return {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'target_names': sorted(set(int(v) for v in y)),
        'class_counts': {int(k): int(v) for k, v in Counter(y).items()},
        'feature_count': len(mlb.classes_),
        'total': int(len(y)),
    }


def prepare_predict_data():
    unrated_items, _ = get_items(rate_type=None, rate_value=None, page=None)
    df = pd.DataFrame((as_dict(item) for item in unrated_items), columns=['id', 'tags'])
    if df.empty:
        return [], []
    df.set_index('id', inplace=True)
    X, _, _ = process_data(df, fit=False)
    return df.index.to_list(), X
