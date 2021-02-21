from typing import List, Any

from init.config import Config
from init.context import Context

from init.factories.dependencies_factory import DependenciesFactory
from init.factories.list_elements_factory import NamedListElementsFactory
from init.factories.vocabulary_factory import VocabularyFactory
from init.object_factory import ObjectFactory, CanBuildResult, CanBuildResultType
from tokenization.tokenizer import Tokenizer


class TokenizerFactory(ObjectFactory):
    """
    Builds a single tokenizer entry inside the tokenizers section.
    """
    # (AD) this is special since we can have multiple tokenizers with individual keys/names.
    KEY = "tokenizer"
    SPECIAL_TOKENS_KEY = "special_tokens"

    def __init__(self, dependencies=DependenciesFactory([VocabularyFactory()])):
        super(TokenizerFactory, self).__init__()
        self._dependencies = dependencies

    def can_build(self, config: Config, context: Context) -> CanBuildResult:

        dependencies_result = self._dependencies.can_build(config, context)
        if dependencies_result.type != CanBuildResultType.CAN_BUILD:
            return dependencies_result

        if not config.has_path([self.SPECIAL_TOKENS_KEY]):
            return CanBuildResult(CanBuildResultType.MISSING_CONFIGURATION, f"missing key <{self.SPECIAL_TOKENS_KEY}>")

        return CanBuildResult(CanBuildResultType.CAN_BUILD)

    def build(self, config: Config, context: Context):
        dependencies = self._dependencies.build(config, context)
        special_tokens = self._get_special_tokens(config)

        return Tokenizer(dependencies["vocabulary"], **special_tokens)

    def is_required(self, context: Context) -> bool:
        return True

    def config_path(self) -> List[str]:
        return [self.KEY]

    def config_key(self) -> str:
        return self.KEY

    def _get_special_tokens(self, config: Config):
        special_tokens_config = config.get_or_default([self.SPECIAL_TOKENS_KEY], {})
        return special_tokens_config


class TokenizersFactory(ObjectFactory):
    """
    Builds all tokenizers within the `tokenizers` section.
    """

    KEY = "tokenizers"

    def __init__(self, tokenizer_elements_factory: NamedListElementsFactory = NamedListElementsFactory(TokenizerFactory())):
        super(TokenizersFactory, self).__init__()
        self.tokenizer_elements_factory = tokenizer_elements_factory

    def can_build(self, config: Config, context: Context) -> CanBuildResult:
        return self.tokenizer_elements_factory.can_build(config, context)

    def build(self, config: Config, context: Context) -> Any:
        return self.tokenizer_elements_factory.build(config, context)

    def is_required(self, context: Context) -> bool:
        return True

    def config_path(self) -> List[str]:
        return [self.KEY]

    def config_key(self) -> str:
        return self.KEY