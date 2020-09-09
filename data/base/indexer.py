import csv
from io import StringIO
from pathlib import Path
from typing import List, Text, BinaryIO, Dict
import sys
from argparse import ArgumentParser
from dataclasses import dataclass

INT_BYTE_SIZE = 8

@dataclass
class SessionBoundary:
    start: int
    end: int


class CsvSessionIndexer:
    INT_BYTE_SIZE = 8

    def __init__(self, delimiter: Text):
        self._delimiter = delimiter

    def create(self, data_file_path: Path, index_file_path: Path, session_key: List[Text]):
        headers = self._extract_headers(data_file_path)

        if not self._all_session_keys_part_of_header(session_key, headers):
            raise Exception(f"not all session keys [{session_key}] could be found in headers [{headers}]")

        with data_file_path.open(mode="rb") as data_file:
            self._skip_headers(data_file)
            with index_file_path.open("wb") as index_file:
                session_key_columns = self._get_session_key_column_indices(headers, session_key)
                num_sessions = 0

                while not self._at_end_of_file(data_file):
                    session_boundary = self._extract_next_session(data_file, session_key_columns)
                    self._add_session_to_index(index_file, session_boundary)
                    num_sessions += 1

                self._write_metadata(index_file, num_sessions)

    def _extract_next_session(self,
                              data_file: BinaryIO,
                              session_key_columns: Dict[Text, int]) -> SessionBoundary:
        first_session_line = self._peek_at_next_line_parsed(data_file)
        session_key_values = self._get_session_key_values(first_session_line, session_key_columns)
        start = data_file.tell()

        while not self._at_end_of_file(data_file) and not self._session_keys_change(session_key_values, session_key_columns, data_file):
            self._take_next_line(data_file)

        end = data_file.tell()
        return SessionBoundary(start, end)

    def _session_keys_change(self, current_session_key_values: Dict[Text, Text], session_key_columns, data_file):
        next_line = self._peek_at_next_line_parsed(data_file)
        next_session_key_values = self._get_session_key_values(next_line, session_key_columns)

        return current_session_key_values != next_session_key_values

    def _get_session_key_values(self, parsed_line: List[Text], session_key_columns: Dict[Text, int]) -> Dict[Text, Text]:
        return {session_key: parsed_line[session_key_column] for session_key, session_key_column in session_key_columns.items()}

    def _take_next_line(self, data_file: BinaryIO):
        return data_file.readline()

    def _peek_at_next_line_parsed(self, data_file: BinaryIO):
        backup_cursor_pos = data_file.tell()
        next_row = self._take_next_line_parsed(data_file)
        data_file.seek(backup_cursor_pos)
        return next_row

    def _take_next_line_parsed(self, data_file: BinaryIO):
        next_line = self._take_next_line(data_file)
        with StringIO(next_line.decode(encoding="utf-8")) as next_line_input:
            reader = csv.reader(next_line_input, delimiter=self._delimiter)
            return next(reader)

    def _at_end_of_file(self, data_file):
        p = data_file.tell()
        eof = data_file.read(4)
        data_file.seek(p)

        return len(eof) == 0

    def _skip_headers(self, data_file: BinaryIO):
        data_file.readline()

    def _extract_headers(self, data_file_path: Path) -> List[Text]:
        with data_file_path.open("r") as file:
            reader = csv.reader(file, delimiter=self._delimiter)
            headers = next(reader)
            return [header.strip() for header in headers]

    def _get_session_key_column_indices(self, headers: List[Text], session_key: List[Text]):
        column_name_to_indices = {name: idx for idx, name in enumerate(headers)}
        return {key: column_name_to_indices[key] for key in session_key}

    def _all_session_keys_part_of_header(self, session_keys: List[Text], headers: List[Text]) -> bool:
        for session_key in session_keys:
            if not self._part_of(session_key, headers):
                return False
        return True

    def _part_of(self, candidate: Text, list: List[Text]) -> bool:
        for element in list:
            if element == candidate:
                return True
        return False

    def _add_session_to_index(self, index_file: BinaryIO, session_boundary: SessionBoundary):
        self._write_value(index_file, session_boundary.start)
        self._write_value(index_file, session_boundary.end)

    def _write_value(self, index_file: BinaryIO, pos: int):
        index_file.write(pos.to_bytes(self.INT_BYTE_SIZE, byteorder=sys.byteorder, signed=False))

    def _write_metadata(self, index_file: BinaryIO, num_session: int):
        self._write_value(index_file, num_session)



