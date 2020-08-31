from argparse import ArgumentParser

from registry import registry


def build_module(module_id: str):
    builder = registry.get_module_builder(module_id)

    # build argument parser and let the model be build from it
    parser = ArgumentParser()
    parser = builder.add_arguments_to_parser(parser)
    args = parser.parse_args()

    dict_args = vars(args)

    return builder.build_module(dict_args)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument('module_id')

    args = parser.parse_args()
    module = args.module_id

    module = build_module(module)


if __name__ == '__main__':
    main()
