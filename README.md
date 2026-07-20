# 🎵 Music Recommender Simulation

## Project Summary

The project compares music using an algorithm and will recomennd song based on that as well as provide a ranking for you.

## How The System Works

The recommender gives every song a **score** that says how well it matches what a
listener likes, then ranks all songs by that score and returns the best ones. A
song earns points for matching the listener's genre and mood, and more points the
closer its audio features are to the listener's target. Here is that idea broken down.

### What each `Song` uses

Each song carries two kinds of information:

- **Numeric audio features** (from `data/songs.csv`), which drive the closeness math:
  - **energy** – calm vs. intense (0–1)
  - **valence** – how positive/happy the song feels (0–1)
  - **danceability** – how easy it is to move to (0–1)
  - **acousticness** – acoustic vs. electronic (0–1)
  - **tempo_bpm** – speed in beats per minute
- **Category labels** – `genre` and `mood`, which are matched exactly for bonus
  points. (`title` and `artist` are only for display.)

### What the `UserProfile` stores

The profile is a "target song" the listener would ideally like, in the **same shape**
as a song: a favorite genre, a favorite mood, and a target value for each numeric
feature (energy, valence, danceability, acousticness, tempo). A `likes_acoustic`
flag sets the acoustic target to fully acoustic or fully electronic.

### How the `Recommender` scores each song

Scoring is **points-based** — the more points, the better the match. For each song:

1. **Genre match** → **+2.0** points if the song's genre equals the listener's favorite.
2. **Mood match** → **+1.5** points if the moods match.
3. **Numeric closeness** → for each feature, `closeness = 1 − |target − song_value|`
   (values on a 0–1 scale; tempo is first rescaled from BPM so it can't dominate).
   Each closeness is multiplied by a weight and added. **Energy is weighted 2.0**;
   valence, danceability, acousticness, and tempo are weighted 1.0.

Every point awarded also records a plain-language **reason** (e.g. `genre match (+2.0)`,
`energy similarity (+1.96)`) so the recommendation can explain itself.

```
score = 2.0·(genre matches) + 1.5·(mood matches) + Σ weightₓ·(1 − |targetₓ − songₓ|)
```

### How songs are chosen to recommend

1. Use the scorer as a **judge** on **every** song in the catalog.
2. **Sort** by score, highest first, breaking ties on title so results are deterministic.
3. Return the **top K** as the ranked recommendation list, each with its reasons.

### In one picture

```
song data ─────────────► genre/mood labels + numeric features
                                      │
user profile ───────────► target genre/mood + target features
                                      │
                                      ▼
             score each song: +2.0 genre, +1.5 mood,
             + weighted closeness on each numeric feature
                                      │
                                      ▼
              sort by score (desc), break ties on title
                                      │
                                      ▼
                     top K ranked recommendations + reasons
```

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# User profile: genre=pop, mood=happy, energy=0.8

Top recommendations:

Sunrise City - Score: 5.46
Because: genre match (+2.0), mood match (+1.5), energy similarity (+1.96)

Gym Hero - Score: 3.74
Because: genre match (+2.0), energy similarity (+1.74)

Power Set - Score: 3.72
Because: genre match (+2.0), energy similarity (+1.72)

Rooftop Lights - Score: 3.42
Because: mood match (+1.5), energy similarity (+1.92)

Morning Bloom - Score: 3.38
Because: mood match (+1.5), energy similarity (+1.88)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Edge-Case Profiles (Top 5 Results)

These profiles were run against the full `data/songs.csv` catalog to probe how the
recommender behaves on unusual input. They correspond to the tests in
`tests/test_edge_cases.py`.

### Empty profile — no preferences
`{}`

```
Coffee Shop Stories    Score:  0.00
Deep Space Drift       Score:  0.00
Focus Flow             Score:  0.00
Gym Hero               Score:  0.00
Iron Sprint            Score:  0.00
```
Every song scores 0.0, so ranking falls back entirely to the alphabetical title
tie-break. Explanations are empty because no points were awarded.

### Sparse — energy only
`{"energy": 0.8}`

```
Sunrise City           Score:  1.96   energy similarity (+1.96)
Rooftop Lights         Score:  1.92   energy similarity (+1.92)
Night Drive Loop       Score:  1.90   energy similarity (+1.9)
Morning Bloom          Score:  1.88   energy similarity (+1.88)
Neon Highway           Score:  1.84   energy similarity (+1.84)
```
Unspecified features neither help nor hurt — only energy closeness matters.

### Genre only — pop
`{"genre": "pop"}`

```
Gym Hero               Score:  2.00   genre match (+2.0)
Power Set              Score:  2.00   genre match (+2.0)
Sunrise City           Score:  2.00   genre match (+2.0)
Coffee Shop Stories    Score:  0.00
Deep Space Drift       Score:  0.00
```
The three pop songs tie at +2.0 and sort by title; everything else scores 0.0.

### Case mismatch — "Pop" (capital P)
`{"genre": "Pop"}`

```
Coffee Shop Stories    Score:  0.00
Deep Space Drift       Score:  0.00
Focus Flow             Score:  0.00
Gym Hero               Score:  0.00
Iron Sprint            Score:  0.00
```
Matching is **case-sensitive**: "Pop" != "pop", so no genre bonus is awarded.

### Out-of-range energy (5.0) — clamped
`{"energy": 5.0}`

```
Power Set              Score:  1.88   energy similarity (+1.88)
Gym Hero               Score:  1.86   energy similarity (+1.86)
Storm Runner           Score:  1.82   energy similarity (+1.82)
Iron Sprint            Score:  1.78   energy similarity (+1.78)
Sunrise City           Score:  1.64   energy similarity (+1.64)
```
`5.0` is clamped to `1.0`, so it favors the highest-energy songs instead of
producing a negative score. (Before the clamp fix this scored `-6.36`.)

### Negative energy (-3.0) — clamped
`{"energy": -3.0}`

```
Deep Space Drift       Score:  1.48   energy similarity (+1.48)
Spacewalk Thoughts     Score:  1.44   energy similarity (+1.44)
Quiet Window           Score:  1.34   energy similarity (+1.34)
Paper Planes           Score:  1.32   energy similarity (+1.32)
Library Rain           Score:  1.30   energy similarity (+1.3)
```
`-3.0` is clamped to `0.0`, correctly surfacing the calmest, lowest-energy songs.

### Conflicting keys — `likes_acoustic` vs `acousticness`
`{"likes_acoustic": True, "acousticness": 0.0}`

```
Deep Space Drift       Score:  0.94   acousticness similarity (+0.94)
Spacewalk Thoughts     Score:  0.92   acousticness similarity (+0.92)
Paper Planes           Score:  0.90   acousticness similarity (+0.9)
Coffee Shop Stories    Score:  0.89   acousticness similarity (+0.89)
Quiet Window           Score:  0.88   acousticness similarity (+0.88)
```
`likes_acoustic` is applied last and **wins** (target 1.0), so the most acoustic
songs rank first — the conflicting `acousticness: 0.0` is overridden.

### Full profile — pop / happy / high-energy
`{"genre": "pop", "mood": "happy", "energy": 0.9, "valence": 0.9, "danceability": 0.85, "likes_acoustic": False, "tempo_bpm": 125}`

```
Sunrise City           Score:  9.00   genre match (+2.0), mood match (+1.5), energy similarity (+1.84), valence similarity (+0.94), danceability similarity (+0.94), acousticness similarity (+0.82), tempo similarity (+0.96)
Gym Hero               Score:  7.69   genre match (+2.0), energy similarity (+1.94), valence similarity (+0.87), danceability similarity (+0.97), acousticness similarity (+0.95), tempo similarity (+0.96)
Power Set              Score:  7.65   genre match (+2.0), energy similarity (+1.92), valence similarity (+0.89), danceability similarity (+0.95), acousticness similarity (+0.94), tempo similarity (+0.95)
Rooftop Lights         Score:  6.74   mood match (+1.5), energy similarity (+1.72), valence similarity (+0.91), danceability similarity (+0.97), acousticness similarity (+0.65), tempo similarity (+0.99)
Morning Bloom          Score:  6.65   mood match (+1.5), energy similarity (+1.68), valence similarity (+0.93), danceability similarity (+0.95), acousticness similarity (+0.62), tempo similarity (+0.97)
```
With all signals specified, the pop + happy + high-energy song (`Sunrise City`)
clearly wins, and every reason is listed.

### Bonus: non-numeric input is rejected
`{"energy": "high"}` raises a clear error instead of crashing:
`ValueError: Preference 'energy' must be a number, got 'high'.`

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

I learned the various data types used to compare and match songs. I gained a better understanding of the metrics and how other music streaming platforms could better implement them for a better user experience. I better understand the extended logic as well.



