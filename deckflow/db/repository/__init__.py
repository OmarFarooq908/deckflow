from deckflow.db.repository.analytics import AnalyticsMixin
from deckflow.db.repository.base import BaseRepository
from deckflow.db.repository.cards import CardsMixin
from deckflow.db.repository.collections import CollectionsMixin
from deckflow.db.repository.concepts import ConceptsMixin
from deckflow.db.repository.reviews import ReviewsMixin
from deckflow.db.repository.scheduling_config import SchedulingConfigMixin


class Repository(
    BaseRepository,
    CollectionsMixin,
    ConceptsMixin,
    CardsMixin,
    ReviewsMixin,
    AnalyticsMixin,
    SchedulingConfigMixin,
):
    pass


__all__ = ["Repository"]
