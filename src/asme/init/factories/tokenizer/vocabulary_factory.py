from pathlib import Path
from typing import List

from asme.init.config import Config
from asme.init.context import Context
from asme.init.factories.util import require_config_keys
from asme.init.object_factory import ObjectFactory, CanBuildResult
from asme.tokenization.vocabulary import CSVVocabularyReaderWriter


class VocabularyFactory(ObjectFactory):
    """
    Builds a vocabulary.
    """
    KEY = "vocabulary"
    REQUIRED_KEYS = ["file"]

    def can_build(self,
                  config: Config,
                  context: Context
                  ) -> CanBuildResult:
        return require_config_keys(config, self.REQUIRED_KEYS)

    def build(self, config: Config, context: Context):
        delimiter = config.get_or_default("delimiter", "\t")
        vocab_file = config.get_or_raise("file", f"<file> could not be found in vocabulary config section.")

        vocab_reader = CSVVocabularyReaderWriter(delimiter)

        with Path(vocab_file).open("r") as file:
            return vocab_reader.read(file)

    def is_required(self, context: Context) -> bool:
        return True

    def config_path(self) -> List[str]:
        return [self.KEY]

    def config_key(self) -> str:
        return self.KEY
