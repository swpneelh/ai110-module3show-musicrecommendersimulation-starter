"""Music recommender: loads songs, scores them against a listener's taste, and ranks the best matches."""

import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.

    The profile is a "target song" the user would ideally like. It carries one
    target value for each of the five features the recommender scores on, so it
    has the same numeric shape as a Song and can be compared by distance.

    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Target values for the remaining recommendation features (0-1 scale, tempo
    # in BPM). Defaults describe a middle-of-the-road song so existing callers
    # that only set the fields above still get a valid, usable profile.
    target_valence: float = 0.5
    target_danceability: float = 0.5
    target_acousticness: float = 0.5
    target_tempo_bpm: float = 100.0

# ---------------------------------------------------------------------------
# Scoring core (shared by the OOP and functional paths so they never diverge)
# ---------------------------------------------------------------------------
#
# The Algorithm Recipe (points-based, higher = better):
#   * genre match .............. +2.0 points
#   * mood match ............... +1.5 points
#   * numerical features ....... closeness * weight, where
#         closeness = 1 - |target - song_value|   (both on a 0-1 scale)
#     Energy is weighted most heavily; the rest add supporting signal.
#
# Every awarded point also records a human-readable reason such as
# "genre match (+2.0)" so the user understands why a song was recommended.

GENRE_POINTS = 2.0
MOOD_POINTS = 1.5

# Weight per numerical feature. Higher weight = more influence on the score.
NUMERIC_WEIGHTS = {
    "energy": 2.0,
    "valence": 1.0,
    "danceability": 1.0,
    "acousticness": 1.0,
    "tempo": 1.0,
}

# Tempo is in BPM, so it is rescaled to 0-1 before the closeness formula runs;
# otherwise its raw range would dwarf the already-0-1 features.
TEMPO_MIN_BPM = 40.0
TEMPO_MAX_BPM = 220.0


def _clamp01(value: float) -> float:
    """Clamp any value to the 0-1 range the closeness formula assumes."""
    return max(0.0, min(1.0, value))


def _numeric_pref(feature: str, value) -> float:
    """
    Convert a user's numeric preference to float, or raise a clear error.

    A bare float() would surface a cryptic "could not convert string to float"
    for input like {"energy": "high"}; this names the offending feature and
    value so the caller can fix their profile.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Preference '{feature}' must be a number, got {value!r}."
        ) from None


def _normalize_tempo(bpm: float) -> float:
    """Rescale a BPM value to 0-1 and clamp it to that range."""
    scaled = (bpm - TEMPO_MIN_BPM) / (TEMPO_MAX_BPM - TEMPO_MIN_BPM)
    return _clamp01(scaled)


def _song_numeric(energy: float, valence: float, danceability: float,
                  acousticness: float, tempo_bpm: float) -> Dict[str, float]:
    """A song's numerical features on a common 0-1 scale (tempo normalized)."""
    return {
        "energy": energy,
        "valence": valence,
        "danceability": danceability,
        "acousticness": acousticness,
        "tempo": _normalize_tempo(tempo_bpm),
    }


def _score_core(
    target_numeric: Dict[str, float],
    song_numeric: Dict[str, float],
    *,
    target_genre: Optional[str],
    song_genre: str,
    target_mood: Optional[str],
    song_mood: str,
) -> Tuple[float, List[str]]:
    """
    Score one song against a target using the points recipe above.

    `target_numeric` holds only the numerical features that should count (so a
    sparse user preference like "energy only" scores just energy). Returns
    (score, reasons); a higher score is a better recommendation.
    """
    score = 0.0
    reasons: List[str] = []

    if target_genre and target_genre == song_genre:
        score += GENRE_POINTS
        reasons.append(f"genre match (+{GENRE_POINTS})")
    if target_mood and target_mood == song_mood:
        score += MOOD_POINTS
        reasons.append(f"mood match (+{MOOD_POINTS})")

    for feature, weight in NUMERIC_WEIGHTS.items():
        if feature in target_numeric and feature in song_numeric:
            # Clamp both sides to 0-1 so an out-of-range value can't push
            # closeness negative (and thus the score below zero).
            target_value = _clamp01(target_numeric[feature])
            song_value = _clamp01(song_numeric[feature])
            closeness = 1.0 - abs(target_value - song_value)
            points = round(closeness * weight, 2)
            score += points
            reasons.append(f"{feature} similarity (+{points})")

    return round(score, 2), reasons


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        target_numeric = {
            "energy": user.target_energy,
            "valence": user.target_valence,
            "danceability": user.target_danceability,
            # likes_acoustic turns the boolean taste into a numeric target:
            # True -> aim for fully acoustic (1.0), False -> fully electronic (0.0).
            "acousticness": 1.0 if user.likes_acoustic else 0.0,
            "tempo": _normalize_tempo(user.target_tempo_bpm),
        }
        song_numeric = _song_numeric(
            song.energy, song.valence, song.danceability,
            song.acousticness, song.tempo_bpm,
        )
        return _score_core(
            target_numeric, song_numeric,
            target_genre=user.favorite_genre, song_genre=song.genre,
            target_mood=user.favorite_mood, song_mood=song.mood,
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # Score every song, then rank highest-first. Ties break on title so the
        # ordering is stable (deterministic) across runs.
        scored = [(self._score(user, song)[0], song) for song in self.songs]
        scored.sort(key=lambda pair: (-pair[0], pair[1].title))
        return [song for _, song in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = self._score(user, song)
        return f"Recommended because it is a " + ", ".join(reasons) + "."

_NUMERIC_FIELDS = ("energy", "valence", "danceability", "acousticness", "tempo_bpm")


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dictionaries.

    Numeric columns are converted to float and `id` to int; everything else
    stays a string. Required by src/main.py.
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["id"] = int(row["id"])
            for field in _NUMERIC_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song (dict) against a user-preferences dict.

    `user_prefs` may be sparse (e.g. only genre/mood/energy). A numerical feature
    is scored only when the user actually specified it, so unspecified features
    neither help nor hurt. Returns (score, reasons). Required by src/main.py.
    """
    # Pull out only the numerical preferences the user provided.
    target_numeric: Dict[str, float] = {}
    for feature in ("energy", "valence", "danceability", "acousticness"):
        if feature in user_prefs:
            target_numeric[feature] = _numeric_pref(feature, user_prefs[feature])
    if "likes_acoustic" in user_prefs:
        target_numeric["acousticness"] = 1.0 if user_prefs["likes_acoustic"] else 0.0
    if "tempo_bpm" in user_prefs:
        target_numeric["tempo"] = _normalize_tempo(
            _numeric_pref("tempo_bpm", user_prefs["tempo_bpm"])
        )

    song_numeric = _song_numeric(
        song["energy"], song["valence"], song["danceability"],
        song["acousticness"], song["tempo_bpm"],
    )

    return _score_core(
        target_numeric, song_numeric,
        target_genre=user_prefs.get("genre"), song_genre=song["genre"],
        target_mood=user_prefs.get("mood"), song_mood=song["mood"],
    )


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, ranks them highest-first, and returns the top k as
    (song_dict, score, explanation) tuples. Required by src/main.py.

    `score_song` acts as the judge for each song; sorted() then orders them.
    """
    # Judge every song: build (song, score, reasons) for the whole catalog.
    scored = [(song, *score_song(user_prefs, song)) for song in songs]

    # sorted() returns a NEW ranked list (leaving `songs` untouched). The key
    # sorts by score descending (via -score) and breaks ties on title so the
    # order is deterministic.
    ranked = sorted(scored, key=lambda item: (-item[1], item[0]["title"]))

    return [(song, score, ", ".join(reasons)) for song, score, reasons in ranked[:k]]
