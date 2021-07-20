local base_path = "/ssd/ml-20m/";
local output_path = "/scratch/jane-doe-framework/experiments/ml-20m/gru";
local max_seq_length = 50;
local metrics =  {
    mrr: [1, 5, 10],
    recall: [3, 5, 10],
    ndcg: [3, 5, 10]
};

local file_prefix = 'ml-1m';

{
    templates: {
        unified_output: {
            path: output_path
        },
        next_sequence_step_data_sources: {
            loader: {
                batch_size: 128,
                num_workers: 4
            },
            path: base_path,
            file_prefix: file_prefix,
            next_step_type: "loo" // leave one out
        }
    },
    module: {
        type: "gru",
        metrics: {
            full: {
                metrics: metrics
            },
            sampled: {
                sample_probability_file: base_path + "popularity.txt",
                num_negative_samples: 100,
                metrics: metrics
            }
        },
        model: {
            cell_type: "gru",
            item_embedding_dim: 64,
            hidden_size: 64,
            num_layers: 2,
            dropout: 0.2
        }
    },
    features: {
        item: {
            column_name: "title",
            sequence_length: max_seq_length,
            tokenizer: {
                special_tokens: {
                    pad_token: "<PAD>",
                    mask_token: "<MASK>",
                    unk_token: "<UNK>"
                },
                vocabulary: {
                    delimiter: "\t",
                    file: base_path + "vocab_title.txt"
                }
            }
        }
    },
    trainer: {
        loggers: {
            tensorboard: {}
        },
        checkpoint: {
            monitor: "recall@10_sampled(100)",
            save_top_k: 3,
            mode: 'max'
        },
        max_epochs: 100,
        gpus: 1
    }
}