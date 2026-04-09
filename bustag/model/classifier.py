"""
Model training and recommendation helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.naive_bayes import BernoulliNB
from sklearn.neighbors import KNeighborsClassifier

from bustag.model.persist import dump_model, load_model
from bustag.model.prepare import prepare_data, prepare_predict_data
from bustag.spider.db import ItemRate, RATE_TYPE
from bustag.util import MODEL_PATH, get_data_path, logger

MODEL_FILE = MODEL_PATH + 'model.pkl'
MIN_TRAIN_NUM = 200
DEFAULT_MODEL_NAME = 'logistic_regression'
CV_FOLDS = 5


@dataclass(frozen=True)
class ModelSpec:
    name: str
    label: str
    factory: Any


MODEL_SPECS: dict[str, ModelSpec] = {
    'logistic_regression': ModelSpec(
        name='logistic_regression',
        label='Logistic Regression',
        factory=lambda: LogisticRegression(
            class_weight='balanced',
            max_iter=2000,
            random_state=42,
        ),
    ),
    'knn': ModelSpec(
        name='knn',
        label='KNN',
        factory=lambda: KNeighborsClassifier(n_neighbors=11),
    ),
    'bernoulli_nb': ModelSpec(
        name='bernoulli_nb',
        label='Bernoulli Naive Bayes',
        factory=lambda: BernoulliNB(),
    ),
}


def load():
    model_data = load_model(get_data_path(MODEL_FILE))
    if isinstance(model_data, tuple) and len(model_data) == 2:
        model, scores = model_data
        metadata = {
            'model_name': getattr(model, '__class__', type(model)).__name__,
            'model_label': getattr(model, '__class__', type(model)).__name__,
        }
        return model, scores, metadata
    return model_data['model'], model_data['scores'], model_data['metadata']


def list_models() -> list[dict[str, str]]:
    return [{'name': spec.name, 'label': spec.label} for spec in MODEL_SPECS.values()]


def create_model(model_name: str = DEFAULT_MODEL_NAME):
    spec = MODEL_SPECS.get(model_name)
    if spec is None:
        supported = ', '.join(MODEL_SPECS)
        raise ValueError(f'不支持的模型: {model_name}. 可选值: {supported}')
    return spec.factory()


def predict(X_test):
    model, _, _ = load()
    y_pred = model.predict(X_test)
    return y_pred


def train(model_name: str = DEFAULT_MODEL_NAME):
    dataset = prepare_data()
    X_train = dataset['X_train']
    X_test = dataset['X_test']
    y_train = dataset['y_train']
    y_test = dataset['y_test']
    target_names = dataset['target_names']
    total = dataset['total']
    class_counts = dataset['class_counts']

    if total < MIN_TRAIN_NUM:
        raise ValueError(f'训练数据不足, 无法训练模型. 需要{MIN_TRAIN_NUM}, 当前{total}')
    if len(class_counts) < 2:
        raise ValueError('训练数据只有一个类别, 至少需要喜欢和不喜欢两类数据')

    model = create_model(model_name)
    cv_scores = _cross_validate(model_name, X_train, y_train)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    scores = evaluate(y_test, y_pred, target_names, cv_scores=cv_scores)
    metadata = {
        'model_name': model_name,
        'model_label': MODEL_SPECS[model_name].label,
        'train_size': int(len(y_train)),
        'test_size': int(len(y_test)),
        'total_samples': int(total),
        'class_counts': class_counts,
        'target_names': target_names,
    }
    model_data = {
        'model': model,
        'scores': scores,
        'metadata': metadata,
    }
    dump_model(get_data_path(MODEL_FILE), model_data)
    logger.info(f'new model trained: {MODEL_SPECS[model_name].label}')
    return model, scores, metadata


def _cross_validate(model_name: str, X_train, y_train) -> dict[str, float]:
    min_class_size = int(np.min(np.bincount(y_train)))
    folds = min(CV_FOLDS, min_class_size)
    if folds < 2:
        return {}
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    result = cross_validate(
        create_model(model_name),
        X_train,
        y_train,
        cv=cv,
        scoring=('precision', 'recall', 'f1', 'accuracy'),
        error_score='raise',
    )
    return {
        'cv_precision': _round_metric(float(np.mean(result['test_precision']))),
        'cv_recall': _round_metric(float(np.mean(result['test_recall']))),
        'cv_f1': _round_metric(float(np.mean(result['test_f1']))),
        'cv_accuracy': _round_metric(float(np.mean(result['test_accuracy']))),
    }


def evaluate(y_test, y_pred, target_names, cv_scores=None):
    labels = sorted(target_names)
    confusion_mtx = confusion_matrix(y_test, y_pred, labels=labels)
    tn, fp, fn, tp = _extract_confusion_parts(confusion_mtx, labels)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f'tp: {tp}, fp: {fp}')
    logger.info(f'fn: {fn}, tn: {tn}')
    logger.info(f'precision_score: {precision}')
    logger.info(f'recall_score: {recall}')
    logger.info(f'f1_score: {f1}')
    logger.info(f'accuracy_score: {accuracy}')

    model_scores = {
        'precision': _round_metric(precision),
        'recall': _round_metric(recall),
        'f1': _round_metric(f1),
        'accuracy': _round_metric(accuracy),
        'tp': int(tp),
        'fp': int(fp),
        'fn': int(fn),
        'tn': int(tn),
    }
    if cv_scores:
        model_scores.update(cv_scores)
    return model_scores


def _extract_confusion_parts(confusion_mtx, labels):
    if confusion_mtx.shape == (2, 2):
        tn, fp, fn, tp = confusion_mtx.ravel()
        return int(tn), int(fp), int(fn), int(tp)

    matrix_sum = int(confusion_mtx.sum())
    if len(labels) == 1:
        label = labels[0]
        if label == 1:
            tp = matrix_sum
            return 0, 0, 0, tp
        tn = matrix_sum
        return tn, 0, 0, 0
    return 0, 0, 0, 0


def _round_metric(value: float) -> float:
    return float(f'{value:.2f}')


def recommend():
    """
    Use the trained model to recommend items.
    """
    ids, X = prepare_predict_data()
    if len(X) == 0:
        logger.warning('no data for recommend')
        return
    count = 0
    total = len(ids)
    y_pred = predict(X)
    for item_id, predicted in zip(ids, y_pred):
        if predicted == 1:
            count += 1
        item_rate = ItemRate(
            rate_type=RATE_TYPE.SYSTEM_RATE,
            rate_value=int(predicted),
            item_id=item_id,
        )
        item_rate.save()
    logger.warning(f'predicted {total} items, recommended {count}')
    return total, count
