.. _config datamodule:
Datamodule
======================================

This config part specifies the dataset parameters.

Example
~~~~~~~~
.. code:: json
    datamodule: {
        dataset: <dataset>,
        <template OR data_sources>: {
            ...
        },
        force_regeneration: "False",
        preprocessing: {
            output_directory: <dataset_path>,
            min_sequence_length: <min_seq_length>,
            ...
        },
        ...
    },

* *dataset*: the name of the dataset (e.g. `ml-1m`)

* *template* / *data_sources*: you can use either the :ref:`template <datamodule template>` to preprocess standardized data sets quickly or :ref:`datamodule datasources` for unique datasets or preprocessing steps. Further explanation for both options are listed below.

* *force_regeneration*: `True` or `False`, depending on whether the dataset should be generated if it already exists. This part is optional.

* *preprocessing*: this part is optional and only available for some datasets already provided by us. The corresponding parameters differ depending on the dataset (which has to be stated above):
    `ml-1m` and `ml-20m`: requires `output_directory`, `min_item_feedback`, `min_sequence_length`, and `extraction_directory` (optional).
    `amazon`: requires `prefix` (either `beauty` or `games`), `output_directory`, `min_item_feedback`, `min_sequence_length`, and `input_directory`.
    `dota`: requires `output_directory`, `raw_csv_file_path`, `split_directory`, `min_sequence_length`, `window_size` (optional), and `session_end_offset` (optional).
    `steam` and `youchoose`: requires `output_directory`, `input_dir`, `min_item_feedback`, `min_sequence_length`.

Please note that some data sets have to be downloaded in advance. You can download the youchoose data set (`buys` or `clicks`) `here<https://www.kaggle.com/chadgostopp/recsys-challenge-2015/download>`__ .


.. _datamodule template:
Template
~~~~~~~~~
The datamodule template offers a way to preprocess common data sets quickly.

.. code:: json
    datamodule: {
        ...
        template: {
            name: "masked",
            split: "leave_one_out",
            path: dataset_path,
            file_prefix: dataset,
            num_workers: 0,
            ...
        },
        ...
    },

template:
    name: masked, next, par_positive_negative, positive_negative, sliding_window
    split: leave_one_out or ratio
    path: path where the dataset is saved (similar to the output_directory from above)
    file_prefix: prefix of the generated files, we recommend using the name of the dataset
    num_workers: number of workers


.. _datamodule datasources:
Data Sources
~~~~~~~~~~~~~~
The data_sources config offers a variety of options to preprocess a given data set.

.. code:: json
    datamodule: {
        ...
        data_sources: {
            split: "leave_one_out",
            path: raw_dataset_path,
            file_prefix: dataset,
            train: {
                type: "session",
                processors: [
                    {
                        "type": "cloze",
                        "mask_probability": 0.2,
                        "only_last_item_mask_prob": 0.1
                    }
                ]
            },
            validation: {
                type: "session",
                processors: [
                    {
                        "type": "target_extractor"
                    },
                    {
                        "type": "last_item_mask"
                    }
                ]
            },
            test: {
                type: "session",
                processors: [
                    {
                        "type": "target_extractor"
                    },
                    {
                        "type": "last_item_mask"
                    }
                ]
            }
        },
    ...
    },

Common Constructs
-----------------

Here we list common data sources configurations.

Positional Datasource
~~~~~~~~~~~~~~~~~~~~~

TODO

Positive Negative Datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This datasource returns the session excluding the last item as sequence
(key: ``TODO``) together with the successor for each sequence step
(positive example; key: ``TODO``), and a negative sampled item from the
item space, that does not occur in the session or is the successor.

.. code-block:: json

    ...
    {
        type: 'session',
        csv_file: '../tests/example_dataset/train.csv',
        csv_file_index: '../tests/example_dataset/train.idx',
        parser: {
            'item_column_name': 'column_name'
        },
        processors: [
            {
                type: 'tokenizer'
            },
            {
                type: 'pos_neg',
                'seed': 42
            }
        ]
    }
    ...

Templates for Specific Models
-----------------------------

Positive Negative DataSources Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This template adds data sources for

-  train (Positive Negative Datasource)
-  test (Positional Datasource)
-  validation (Positional Datasource)

The template is for models that use the complete sequence and train to
predict the successor for each sequence step and compare the scores for
the successor with a negative sample.

It can be triggered by adding the following element instead of
``data_sources``:

.. code-block:: json

    ...
    pos_neg_data_sources: {
        parser: {
            item_column_name: "column_name"
        },
        batch_size: BATCH_SIZE,
        max_seq_length: SEQ_LENGTH,
        path: "/path",
        train_file_prefix: "train"
        validation_file_prefix: "train",
        test_file_prefix: "train",
        seed: 42
    },
    ...

By default, the template configures the framework to

The following config parameters are available:

-  ``parser``: configs the parser for the csv file, see parser
   configuration
-  ``batch_size``: the batch size to use, if you want to override this
   for training, validation or test your model, add a
   ``{train,validation,test}_batch_size`` element to the element
-  ``seed``: the seed used to generate negative samples

Mask Datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    ...
    mask_data_sources: {
        loader: {
            batch_size: 9,
            num_workers: 0
        },
        path: base_path,
        file_prefix: prefix,
        mask_probability: 0.1,
        mask_seed: 123456,
        split_type: 'leave_one_out'
    }
    ...

src/asme/init/factories/data_sources/datasets/processor/processors.py
        'cloze': ClozeProcessorFactory(),
        'pos_neg': PositiveNegativeSamplerProcessorFactory(),
        'par_pos_neg': ParameterizedPositiveNegativeSamplerProcessorFactory(),
        'last_item_mask': LastItemMaskProcessorFactory(),
        'position_token': PositionTokenProcessorFactory(),
        'tokenizer': TokenizerProcessorFactory(),
        'target_extractor': TargetExtractorProcessorFactory(),
        'fixed_sequence_length_processor': CutToFixedSequenceLengthProcessorFactory()
