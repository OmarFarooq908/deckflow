from datetime import UTC, datetime

from deckflow.scheduler.fsrs import card_to_json, new_fsrs_card, review_card


def test_good_rating_advances_due_date() -> None:
    card = new_fsrs_card(card_id=1)
    fsrs_json = card_to_json(card)
    now = datetime.now(UTC)

    updated, _ret = review_card(fsrs_json, rating=3, review_datetime=now)
    assert updated.due >= now


def test_again_rating_still_schedules() -> None:
    card = new_fsrs_card(card_id=2)
    fsrs_json = card_to_json(card)
    now = datetime.now(UTC)

    updated, _ret = review_card(fsrs_json, rating=1, review_datetime=now)
    assert updated.due >= now
