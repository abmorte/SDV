import numpy as np
import pandas as pd
import pytest

from sdv.demo import load_demo
from sdv.tabular.copulagan import CopulaGAN


def test_copulagan():
    users = load_demo(metadata=False)['users']

    model = CopulaGAN(
        primary_key='user_id',
        epochs=1,
        field_distributions={
            'age': 'beta'
        },
        default_distribution='bounded'
    )
    model.fit(users)

    sampled = model.sample()

    # test shape is right
    assert sampled.shape == users.shape

    # test user_id has been generated as an ID field
    assert list(sampled['user_id']) == list(range(0, len(users)))

    assert model.get_metadata().to_dict() == {
        'fields': {
            'user_id': {
                'type': 'id',
                'subtype': 'integer',
                'transformer': 'integer',
            },
            'country': {
                'type': 'categorical',
                'transformer': 'label_encoding',
            },
            'gender': {
                'type': 'categorical',
                'transformer': 'label_encoding',
            },
            'age': {
                'type': 'numerical',
                'subtype': 'integer',
                'transformer': 'integer',
            }
        },
        'primary_key': 'user_id',
        'constraints': [],
        'sequence_index': None,
        'context_columns': [],
        'entity_columns': [],
        'model_kwargs': {},
        'name': None
    }


def test_recreate():
    data = load_demo(metadata=False)['users']

    # If distribution is non parametric, get_parameters fails
    model = CopulaGAN(epochs=1)
    model.fit(data)
    sampled = model.sample()

    assert sampled.shape == data.shape
    assert (sampled.dtypes == data.dtypes).all()
    assert (sampled.notnull().sum(axis=1) != 0).all()

    # Metadata
    model_meta = CopulaGAN(epochs=1, table_metadata=model.get_metadata())
    model_meta.fit(data)
    sampled = model_meta.sample()

    assert sampled.shape == data.shape
    assert (sampled.dtypes == data.dtypes).all()
    assert (sampled.notnull().sum(axis=1) != 0).all()

    # Metadata dict
    model_meta_dict = CopulaGAN(epochs=1, table_metadata=model.get_metadata().to_dict())
    model_meta_dict.fit(data)
    sampled = model_meta_dict.sample()

    assert sampled.shape == data.shape
    assert (sampled.dtypes == data.dtypes).all()
    assert (sampled.notnull().sum(axis=1) != 0).all()


@pytest.mark.xfail(reason="Waiting improvements to CTGAN conditional sampling")
def test_conditional_sampling_one_category():
    data = pd.DataFrame({
        "column1": [1.0, 0.5, 2.5] * 10,
        "column2": ["a", "b", "c"] * 10
    })

    model = CopulaGAN(epochs=1)
    model.fit(data)
    conditions = {
        "column2": "b"
    }
    sampled = model.sample(30, conditions=conditions)

    assert sampled.shape == data.shape
    assert set(sampled["column2"].unique()) == set(["b"])


@pytest.mark.xfail(reason="Waiting improvements to CTGAN conditional sampling")
def test_conditional_sampling_multiple_categories():
    data = pd.DataFrame({
        "column1": [1.0, 0.5, 2.5] * 10,
        "column2": ["a", "b", "c"] * 10
    })

    model = CopulaGAN(epochs=1)
    model.fit(data)
    conditions = pd.DataFrame({
        "column2": ["b", "b", "b", "c", "c"]
    })
    sampled = model.sample(conditions=conditions)

    assert sampled.shape[0] == len(conditions["column2"])
    assert (sampled["column2"] == np.array(["b", "b", "b", "c", "c"])).all()


def test_conditional_sampling_two_conditions_fails():
    data = pd.DataFrame({
        "column1": [1.0, 0.5, 2.5] * 10,
        "column2": ["a", "b", "c"] * 10,
        "column3": ["d", "e", "f"] * 10
    })

    model = CopulaGAN(epochs=1)
    model.fit(data)
    conditions = {
        "column2": "b",
        "column3": "f"
    }
    with pytest.raises(NotImplementedError):
        model.sample(30, conditions=conditions)
