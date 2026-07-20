"""
Edge-case tests for the functional recommender path (the one src/main.py uses):
    score_song(user_prefs, song) -> (score, reasons)
    recommend_songs(user_prefs, songs, k) -> [(song, score, explanation), ...]

These probe sparse profiles, out-of-range numerics, exact/case-sensitive
categorical matching, conflicting keys, and k boundaries.

Most tests are *characterization* tests: they lock in what the code does today.
Two tests are marked xfail because they express behavior that is arguably
correct but that the code does NOT currently satisfy (flagged inline as BUG).
"""

import pytest

from src.recommender import score_song, recommend_songs


def make_song(**overrides):
    """A well-formed pop/happy song dict; override any field per test."""
    song = {
        "id": 1,
        "title": "Sunrise City",
        "artist": "Neon Echo",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.82,
        "tempo_bpm": 118.0,
        "valence": 0.84,
        "danceability": 0.79,
        "acousticness": 0.18,
    }
    song.update(overrides)
    return song


# ---------------------------------------------------------------------------
# Empty / sparse profiles
# ---------------------------------------------------------------------------

def test_empty_profile_scores_zero_with_no_reasons():
    score, reasons = score_song({}, make_song())
    assert score == 0.0
    assert reasons == []


def test_empty_profile_produces_empty_explanation_string():
    # recommend_songs joins the (empty) reasons -> "". Guards against the
    # explanation line in main.py rendering as "Because: ".
    songs = [make_song(id=1, title="A"), make_song(id=2, title="B", genre="lofi")]
    results = recommend_songs({}, songs, k=2)
    assert len(results) == 2
    _, _, explanation = results[0]
    assert explanation == ""


def test_sparse_single_numeric_only_scores_that_feature():
    # Only energy specified: unspecified features neither help nor hurt.
    score, reasons = score_song({"energy": 0.82}, make_song(energy=0.82))
    assert score == 2.0  # closeness 1.0 * energy weight 2.0
    assert reasons == ["energy similarity (+2.0)"]


def test_sparse_single_genre_only():
    score, reasons = score_song({"genre": "pop"}, make_song(genre="pop"))
    assert score == 2.0
    assert reasons == ["genre match (+2.0)"]


# ---------------------------------------------------------------------------
# Categorical matching is exact and case-sensitive
# ---------------------------------------------------------------------------

def test_genre_match_is_case_sensitive():
    lower = score_song({"genre": "pop"}, make_song(genre="pop"))[0]
    upper = score_song({"genre": "Pop"}, make_song(genre="pop"))[0]
    assert lower == 2.0
    assert upper == 0.0  # "Pop" != "pop": no match


def test_genre_match_is_whitespace_sensitive():
    assert score_song({"genre": " pop "}, make_song(genre="pop"))[0] == 0.0


def test_unknown_genre_does_not_error_and_scores_zero():
    score, reasons = score_song({"genre": "polka"}, make_song(genre="pop"))
    assert score == 0.0
    assert reasons == []


# ---------------------------------------------------------------------------
# Conflicting / redundant keys
# ---------------------------------------------------------------------------

def test_likes_acoustic_overrides_explicit_acousticness():
    # Both keys map to the "acousticness" target; score_song applies
    # likes_acoustic last, so True (-> target 1.0) must win over acousticness 0.0.
    song = make_song(acousticness=0.9)
    score, _ = score_song({"likes_acoustic": True, "acousticness": 0.0}, song)
    # target 1.0 vs song 0.9 -> closeness 0.9 (not 0.1 from target 0.0)
    assert score == pytest.approx(0.9)


def test_likes_acoustic_false_targets_electronic():
    song = make_song(acousticness=0.0)
    score, _ = score_song({"likes_acoustic": False}, song)
    assert score == pytest.approx(1.0)  # target 0.0 vs song 0.0 -> perfect


# ---------------------------------------------------------------------------
# Tempo is normalized/clamped; the other numerics are NOT
# ---------------------------------------------------------------------------

def test_extreme_tempo_is_clamped():
    # Both target and song tempo clamp to 1.0 (>=220 BPM) -> perfect closeness.
    score, _ = score_song({"tempo_bpm": 100000}, make_song(tempo_bpm=100000))
    assert score == pytest.approx(1.0)


def test_zero_tempo_clamps_to_lower_bound():
    score, _ = score_song({"tempo_bpm": 0}, make_song(tempo_bpm=0))
    assert score == pytest.approx(1.0)  # both clamp to 0.0


# ---------------------------------------------------------------------------
# Full profile / perfect match ceiling
# ---------------------------------------------------------------------------

def test_full_profile_perfect_match_lists_all_reasons():
    song = make_song(
        genre="pop", mood="happy", energy=1.0, valence=1.0,
        danceability=1.0, acousticness=1.0, tempo_bpm=100000,
    )
    prefs = {
        "genre": "pop", "mood": "happy", "energy": 1.0, "valence": 1.0,
        "danceability": 1.0, "likes_acoustic": True, "tempo_bpm": 100000,
    }
    score, reasons = score_song(prefs, song)
    # 2.0 + 1.5 + energy 2.0 + valence 1 + dance 1 + acoustic 1 + tempo 1
    assert score == pytest.approx(9.5)
    assert len(reasons) == 7


# ---------------------------------------------------------------------------
# recommend_songs: k boundaries and ranking
# ---------------------------------------------------------------------------

def test_recommend_k_zero_returns_empty():
    songs = [make_song(id=i, title=f"S{i}") for i in range(3)]
    assert recommend_songs({"genre": "pop"}, songs, k=0) == []


def test_recommend_k_larger_than_catalog_returns_all():
    songs = [make_song(id=i, title=f"S{i}") for i in range(3)]
    assert len(recommend_songs({"genre": "pop"}, songs, k=99)) == 3


def test_recommend_ranks_best_match_first():
    good = make_song(id=1, title="Match", genre="pop", mood="happy")
    bad = make_song(id=2, title="NoMatch", genre="rock", mood="intense")
    prefs = {"genre": "pop", "mood": "happy"}
    ranked = recommend_songs(prefs, [bad, good], k=2)
    assert ranked[0][0]["title"] == "Match"


def test_recommend_ties_break_on_title_deterministically():
    # Identical scores (empty profile) -> order must be by title, stable.
    songs = [make_song(id=1, title="Zebra"), make_song(id=2, title="Apple")]
    ranked = recommend_songs({}, songs, k=2)
    assert [s["title"] for s, _, _ in ranked] == ["Apple", "Zebra"]


# ---------------------------------------------------------------------------
# Out-of-range numerics are clamped to 0-1 (no negative scores)
# ---------------------------------------------------------------------------

def test_out_of_range_high_energy_is_clamped_not_negative():
    # energy=5.0 clamps to 1.0; vs song 0.82 -> closeness 0.82 * weight 2.0 = 1.64
    score, _ = score_song({"energy": 5.0}, make_song(energy=0.82))
    assert score == pytest.approx(1.64)
    assert score >= 0.0


def test_out_of_range_negative_energy_is_clamped():
    # energy=-3.0 clamps to 0.0; vs song 0.82 -> closeness 1-0.82 = 0.18 * 2 = 0.36
    score, _ = score_song({"energy": -3.0}, make_song(energy=0.82))
    assert score == pytest.approx(0.36)
    assert score >= 0.0


def test_out_of_range_value_never_drives_total_score_below_zero():
    # Even with every numeric wildly out of range, clamping keeps score >= 0.
    prefs = {"energy": 99, "valence": -99, "danceability": 99, "acousticness": -99}
    score, _ = score_song(prefs, make_song())
    assert score >= 0.0


# ---------------------------------------------------------------------------
# Non-numeric preferences are rejected with a clear, named error
# ---------------------------------------------------------------------------

def test_non_numeric_preference_raises_clear_error():
    with pytest.raises(ValueError, match="Preference 'energy' must be a number"):
        score_song({"energy": "high"}, make_song())


def test_non_numeric_error_names_the_offending_value():
    with pytest.raises(ValueError, match="'high'"):
        score_song({"energy": "high"}, make_song())


def test_non_numeric_tempo_is_also_rejected():
    with pytest.raises(ValueError, match="Preference 'tempo_bpm' must be a number"):
        score_song({"tempo_bpm": "fast"}, make_song())


def test_none_preference_is_rejected():
    with pytest.raises(ValueError, match="Preference 'valence' must be a number"):
        score_song({"valence": None}, make_song())


def test_numeric_strings_still_accepted():
    # A numeric string like "0.82" is a legitimate value and must still work.
    score, _ = score_song({"energy": "0.82"}, make_song(energy=0.82))
    assert score == pytest.approx(2.0)
