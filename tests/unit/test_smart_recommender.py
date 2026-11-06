"""Real training and recommendation paths; no fictional analysis/model methods."""
import random
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from src.core.models import SSQNumber, DLTNumber
from src.core.smart_recommender import SmartRecommender


@pytest.fixture
def recommender():
    instance = SmartRecommender()
    # A real small regressor keeps boundary tests quick and deterministic.
    instance.models = {'ridge': Ridge()}
    return instance


@pytest.fixture
def history():
    return pd.DataFrame({
        'draw_date': pd.date_range('2024-01-01', periods=30),
        'red_numbers': [sorted({(i + k) % 33 + 1 for k in [0, 1, 2, 10, 20, 30]}) for i in range(30)],
        'blue_number': [(i % 16) + 1 for i in range(30)],
    }, index=range(30, 60))


@pytest.mark.parametrize('as_array', [False, True])
def test_train_models_accepts_numeric_frames_and_arrays(recommender, as_array):
    X = pd.DataFrame({'first': np.arange(20), 'second': np.arange(20) % 3})
    y = pd.Series(np.arange(20) * 0.5)
    scores = recommender.train_models(X.to_numpy() if as_array else X, y.to_numpy() if as_array else y)
    assert set(scores) == {'ridge'}
    assert np.isfinite(list(scores['ridge'].values())).all()
    prediction = recommender.models['ridge'].predict(recommender.scaler.transform(X.tail(1).to_numpy() if as_array else X.tail(1)))
    assert prediction.shape == (1,)


@pytest.mark.parametrize('lottery_type', ['ssq', 'dlt'])
def test_generate_recommendations_with_real_features(recommender, history, lottery_type):
    if lottery_type == 'dlt':
        history = history.drop(columns=['red_numbers', 'blue_number']).assign(
            front_numbers=[list(range(i % 20 + 1, i % 20 + 6)) for i in range(30)],
            back_numbers=[[i % 11 + 1, i % 11 + 2] for i in range(30)])
    state = random.getstate()
    random.seed(42)
    try:
        recommendations = recommender.generate_recommendations(history, num_recommendations=3)
    finally:
        random.setstate(state)
    assert len(recommendations) == 3
    for rec in recommendations:
        number = SSQNumber(**rec['numbers']) if lottery_type == 'ssq' else DLTNumber(**rec['numbers'])
        assert number.validate()
        assert np.isfinite(rec['score'])


def test_candidates_use_latest_draw_and_history_is_sorted(recommender, history, monkeypatch):
    captured = []
    generate = recommender._generate_candidates
    def capture(features, count):
        captured.append(features.copy())
        return generate(features, count)
    monkeypatch.setattr(recommender, '_generate_candidates', capture)
    recommender.generate_recommendations(history.iloc[::-1], num_recommendations=1)
    assert captured[0].index.tolist() == [59]


def test_unknown_history_type_is_rejected(recommender):
    with pytest.raises(ValueError):
        recommender.generate_recommendations(pd.DataFrame({'a': [1, 2, 3]}))


def test_insufficient_history_is_rejected(recommender, history):
    with pytest.raises(ValueError):
        recommender.generate_recommendations(history.iloc[:2])


def test_diversity_removes_repeated_candidates(recommender):
    first = {'numbers': {'red': [1, 2, 3, 4, 5, 6], 'blue': 1}, 'score': 2}
    second = {'numbers': {'red': [20, 21, 22, 23, 24, 25], 'blue': 2}, 'score': 1}
    assert recommender._optimize_diversity([first, first, second]) == [first, second]


def test_training_aligns_a_reordered_series_target(recommender):
    data = pd.DataFrame({'signal': np.arange(20)}, index=range(20, 40))
    target = pd.Series(np.arange(20) * 0.5, index=data.index).iloc[::-1]
    recommender.train_models(data, target)
    prediction = recommender.models['ridge'].predict(recommender.scaler.transform(data.tail(1)))[0]
    assert prediction == pytest.approx(9.5, abs=0.5)
