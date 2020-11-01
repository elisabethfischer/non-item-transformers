from typing import Any, Dict

from dependency_injector import containers, providers

from models.bert4rec.bert4rec_model import BERT4RecModel
from models.caser.caser_model import CaserModel
from models.gru.gru_model import GRUSeqItemRecommenderModel
from models.narm.narm_model import NarmModel
from models.sasrec.sas_rec_model import SASRecModel
from modules import BERT4RecModule, CaserModule, SASRecModule
from modules.gru_module import GRUModule
from modules.narm_module import NarmModule
from runner.util.provider_utils import build_tokenizer_provider, build_session_loader_provider_factory, \
    build_nextitem_loader_provider_factory, build_posneg_loader_provider_factory, build_standard_trainer, \
    build_metrics_provider


def build_default_config() -> providers.Configuration:
    config = providers.Configuration()
    # init some default values
    config.from_dict({
        'trainer': {
            'limit_train_batches': 1.0,
            'limit_val_batches': 1.0,
            'gradient_clip_val': 0.0,
            'default_root_dir': '/tmp/checkpoints'
        },
        'datasets': {
            'train': _build_default_dataset_config(shuffle=True),
            'validation': _build_default_dataset_config(shuffle=False),
            'test': _build_default_dataset_config(shuffle=False)
        }


    })
    return config


def _build_default_dataset_config(shuffle: bool) -> Dict[str, Any]:
    return {
        'dataset': {
            'additional_features': {}
        },
        'loader': {
            'num_workers': 1,
            'shuffle': shuffle
        }
    }


# XXX: find a better way to allow
def _kwargs_adapter(clazz, kwargs):
    return clazz(**kwargs)


class BERT4RecContainer(containers.DeclarativeContainer):

    config = build_default_config()

    # tokenizer
    tokenizer = build_tokenizer_provider(config)

    # model
    model = providers.Singleton(_kwargs_adapter, BERT4RecModel, config.model)

    module_config = config.module

    metrics = build_metrics_provider(module_config.metrics)

    module = providers.Singleton(
        BERT4RecModule,
        model=model,
        mask_probability=module_config.mask_probability,
        learning_rate=module_config.learning_rate,
        beta_1=module_config.beta_1,
        beta_2=module_config.beta_2,
        weight_decay=module_config.weight_decay,
        num_warmup_steps=module_config.num_warmup_steps,
        tokenizer=tokenizer,
        batch_first=module_config.batch_first,
        metrics=metrics
    )

    train_dataset_config = config.datasets.train
    validation_dataset_config = config.datasets.validation
    test_dataset_config = config.datasets.test

    # loaders
    train_loader = build_session_loader_provider_factory(train_dataset_config, tokenizer)
    validation_loader = build_nextitem_loader_provider_factory(validation_dataset_config, tokenizer)
    test_loader = build_nextitem_loader_provider_factory(test_dataset_config, tokenizer)

    # trainer
    trainer = build_standard_trainer(config)


class CaserContainer(containers.DeclarativeContainer):

    config = build_default_config()

    # tokenizer
    tokenizer = build_tokenizer_provider(config)

    # model
    model = providers.Singleton(_kwargs_adapter, CaserModel, config.model)

    module_config = config.module

    metrics = build_metrics_provider(module_config.metrics)

    module = providers.Singleton(
        CaserModule,
        model=model,
        tokenizer=tokenizer,
        learning_rate=module_config.learning_rate,
        weight_decay=module_config.weight_decay,
        metrics=metrics
    )

    train_dataset_config = config.datasets.train
    validation_dataset_config = config.datasets.validation
    test_dataset_config = config.datasets.test

    # loaders
    train_loader = build_posneg_loader_provider_factory(train_dataset_config, tokenizer)
    validation_loader = build_nextitem_loader_provider_factory(validation_dataset_config, tokenizer)
    test_loader = build_nextitem_loader_provider_factory(test_dataset_config, tokenizer)

    # trainer
    trainer = build_standard_trainer(config)


class SASRecContainer(containers.DeclarativeContainer):

    config = build_default_config()

    # tokenizer
    tokenizer = build_tokenizer_provider(config)

    model_config = config.model

    # model
    model = providers.Singleton(_kwargs_adapter, SASRecModel, config.model)

    module_config = config.module

    metrics = build_metrics_provider(module_config.metrics)

    module = providers.Singleton(
        SASRecModule,
        model=model,
        learning_rate=module_config.learning_rate,
        beta_1=module_config.beta_1,
        beta_2=module_config.beta_2,
        teokinizer=tokenizer,
        batch_first=module_config.batch_first,
        metrics=metrics
    )

    train_dataset_config = config.datasets.train
    validation_dataset_config = config.datasets.validation
    test_dataset_config = config.datasets.test

    # loaders
    train_loader = build_posneg_loader_provider_factory(train_dataset_config, tokenizer)
    validation_loader = build_nextitem_loader_provider_factory(validation_dataset_config, tokenizer)
    test_loader = build_nextitem_loader_provider_factory(test_dataset_config, tokenizer)

    trainer = build_standard_trainer(config)


class NarmContainer(containers.DeclarativeContainer):

    config = build_default_config()

    # tokenizer
    tokenizer = build_tokenizer_provider(config)

    # model
    model = providers.Singleton(_kwargs_adapter, NarmModel, config.model)

    module_config = config.module
    metrics = build_metrics_provider(module_config.metrics)

    module = providers.Singleton(
        NarmModule,
        model,
        module_config.batch_size,
        module_config.learning_rate,
        module_config.beta_1,
        module_config.beta_2,
        tokenizer,
        module_config.batch_first,
        metrics
    )

    train_dataset_config = config.datasets.train
    validation_dataset_config = config.datasets.validation
    test_dataset_config = config.datasets.test

    # loaders
    train_loader = build_nextitem_loader_provider_factory(train_dataset_config, tokenizer)
    validation_loader = build_nextitem_loader_provider_factory(validation_dataset_config, tokenizer)
    test_loader = build_nextitem_loader_provider_factory(test_dataset_config, tokenizer)

    trainer = build_standard_trainer(config)


class GRUContainer(containers.DeclarativeContainer):

    config = build_default_config()

    # tokenizer
    tokenizer = build_tokenizer_provider(config)

    model_config = config.model

    # model
    model = providers.Singleton(
        GRUSeqItemRecommenderModel,
        model_config.num_items,
        model_config.item_embedding_dim,
        model_config.hidden_size,
        model_config.num_layers,
        model_config.dropout,
    )

    module_config = config.module
    metrics = build_metrics_provider(module_config.metrics)

    module = providers.Singleton(
        GRUModule,
        model,
        module_config.learning_rate,
        module_config.beta_1,
        module_config.beta_2,
        tokenizer,
        metrics
    )

    train_dataset_config = config.datasets.train
    validation_dataset_config = config.datasets.validation
    test_dataset_config = config.datasets.test

    # loaders
    train_loader = build_nextitem_loader_provider_factory(train_dataset_config, tokenizer)
    validation_loader = build_nextitem_loader_provider_factory(validation_dataset_config, tokenizer)
    test_loader = build_nextitem_loader_provider_factory(test_dataset_config, tokenizer)

    trainer = build_standard_trainer(config)
