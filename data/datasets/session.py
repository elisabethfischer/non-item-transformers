import datetime
import functools
import io
from typing import Dict, List, Any, Callable, Union
import csv
from torch.utils.data import Dataset

from data.base.reader import CsvDatasetReader
from data.datasets import ITEM_SEQ_ENTRY_NAME
from data.datasets.prepare import Processor
from data.mp import MultiProcessSupport
from tokenization.tokenizer import Tokenizer


def _parse_boolean(text: str
                   ) -> bool:
    return text == 'True'


def _parse_timestamp(text: str,
                     date_format: str
                     ) -> datetime.datetime:
    return datetime.datetime.strptime(text, date_format)


# TODO: move to provider utils?
def _build_converter(converter_info: Dict[str, Any]
                     ) -> Callable[[str], Any]:
    feature_type = converter_info['type']
    if feature_type == 'int':
        return int

    if feature_type == 'bool':
        return _parse_boolean

    if feature_type == 'timestamp':
        return functools.partial(_parse_timestamp, date_format=converter_info['format'])

    raise KeyError(f'{feature_type} not supported. Currently only bool, timestamp and int are supported.'
                   f'See documentation for more details')


class SessionParser:
    def parse(self, raw_session: str) -> Dict[str, Any]:
        raise NotImplementedError()


class ItemSessionParser(SessionParser):

    def __init__(self,
                 indexed_headers: Dict[str, int],
                 item_header_name: str,
                 additional_features: Dict[str, Any] = None,
                 item_separator: str = None,
                 delimiter: str = "\t"
                 ):
        super().__init__()
        self._indexed_headers = indexed_headers
        self._item_header_name = item_header_name

        if additional_features is None:
            additional_features = {}
        self._additional_features = additional_features

        self._item_separator = item_separator

        self._delimiter = delimiter

    def parse(self,
              raw_session: str
              ) -> Dict[str, Any]:
        reader = csv.reader(io.StringIO(raw_session),
                            delimiter=self._delimiter)

        entries = list(reader)
        items = [self._get_item(entry) for entry in entries]
        parsed_session = {
            ITEM_SEQ_ENTRY_NAME: items
        }

        for feature_key, info in self._additional_features.items():
            feature_sequence = info['sequence']

            # if feature changes over the sequence parse it over all entries, else extract it form the first entry
            if feature_sequence:
                feature = [self._get_feature(entry, feature_key, info) for entry in entries]
            else:
                feature = self._get_feature(entries[0], feature_key, info)
            parsed_session[feature_key] = feature

        return parsed_session

    def _get_feature(self,
                     entry: List[str],
                     feature_key: str,
                     info: Dict[str, Any]
                     ) -> Any:
        converter = _build_converter(info)
        feature_idx = self._indexed_headers[feature_key]
        return converter(entry[feature_idx])

    def _get_item(self,
                  entry: List[str]
                  ) -> Union[str, List[str]]:
        item_column_idx = self._indexed_headers[self._item_header_name]
        entry = entry[item_column_idx]
        if self._item_separator is None:
            return entry
        return entry.split(self._item_separator)


class ItemSessionDataset(Dataset, MultiProcessSupport):

    def __init__(self,
                 reader: CsvDatasetReader,
                 parser: SessionParser,
                 processors: List[Processor] = None
                 ):
        super().__init__()
        self._reader = reader
        self._parser = parser
        if processors is None:
            processors = []
        self._processors = processors

    def __len__(self):
        return len(self._reader)

    def __getitem__(self, idx):
        session = self._reader.get_session(idx)
        parsed_session = self._parser.parse(session)

        for processor in self._processors:
            parsed_session = processor.process(parsed_session)

        return parsed_session

    def _init_class_for_worker(self, worker_id: int, num_worker: int, seed: int):
        # nothing to do here
        pass
