local base_path = "../tests/example_dataset/";
local max_seq_length = 7;
local prefix = 'example';
local metrics =  {
    mrr: [1, 3, 5],
    recall: [1, 3, 5],
    ndcg: [1, 3, 5]
};
{
    templates: {
        unified_output: {
            path: "../experiments/bert4rec"
        },
        mask_data_sources: {
            parser: {
                item_column_name: "item_id"
            },
            loader: {
                batch_size: 9,
                max_seq_length: max_seq_length,
            },
            path: base_path,
            file_prefix: prefix,
            mask_probability: 0.1,
            mask_seed: {
                hyper_opt: {
                    suggest: "int",
                    params: {
                       low: 0,
                       high: 21312313
                    }
                }
            },
            split_type: 'leave_one_out'
        }
    },
    module: {
        type: "bert4rec",
        metrics: {
            full: {
                metrics: metrics
            },
            sampled: {
                sample_probability_file: base_path + "example.popularity.item_id.txt",
                num_negative_samples: 2,
                metrics: metrics
            },
            fixed: {
                item_file: base_path + "example.relevant_items.item_id.txt",
                metrics: metrics
            }
        },
        model: {
            max_seq_length: max_seq_length,
            num_transformer_heads: {
                hyper_opt: {
                    suggest: "int",
                    params: {
                       low: 2,
                       high: 8,
                       step: 2
                    }
                }
            },
            num_transformer_layers: {
                hyper_opt: {
                    suggest: "int",
                    params: {
                       low: 2,
                       high: 8,
                       step: 2
                    }
                }
            },
            transformer_hidden_size: {
                hyper_opt: {
                   suggest: "int",
                   params: {
                      low: 2,
                      high: 8,
                      step: 2
                   },
                   depends_on: "module.model.num_transformer_heads",
                   dependency: "multiply"
                }
            },
            transformer_dropout: 0.1
        }
    },
    tokenizers: {
        item: {
            tokenizer: {
                special_tokens: {
                    pad_token: "<PAD>",
                    mask_token: "<MASK>",
                    unk_token: "<UNK>"
                },
                vocabulary: {
                    file: base_path + "example.vocabulary.item_id.txt"
                }
            }
        }
    },
    trainer: {
        logger: {
            type: "tensorboard",
        },
        checkpoint: {
            monitor: "recall@5/sampled(2)",
            save_top_k: 3,
            mode: 'max'
        }
    }
}
