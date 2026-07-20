# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Music Matcher 1.0 

---

## 2. Intended Use  

Music Matcher takes a listener's taste — the genre and mood they like plus how
energetic, happy, danceable, acoustic, and fast they want their music — and
recommends songs from a small catalog that best match that taste. It is a learning
project meant to show how a recommender turns data into ranked suggestions, not a
production app for real listeners.

## 3. How the Model Works  

Think of it like a matchmaker giving every song a score for how well it fits you.

- **What each song brings:** every song has two category labels — a **genre**
  (pop, lofi, rock, etc.) and a **mood** (happy, chill, intense, etc.) — plus five
  number "dials" between 0 and 1: **energy** (calm vs. intense), **valence** (how
  happy it sounds), **danceability**, **acousticness** (acoustic vs. electronic),
  and **tempo** (speed, measured in beats per minute).
- **What you tell it:** you describe your ideal song using those same fields. You
  don't have to fill in all of them — you can just say "I like pop and high energy"
  and leave the rest blank.
- **Turning that into a score:** the song earns **2 points** if its genre matches
  yours and **1.5 points** if its mood matches. Then, for each number dial you
  cared about, it measures how close the song's value is to yours — a perfect match
  is worth full points and the score shrinks the further apart you are. Energy
  counts double because it usually matters most to how a song feels. All the points
  add up, and the songs with the highest totals are recommended. Each point also
  comes with a plain reason like "genre match" or "energy similarity" so you can see
  *why* a song was suggested.
- **What I changed from the starter:** the starter left the scoring functions empty,
  so I built the points system above. I also fixed two problems: if someone entered a
  value outside the normal 0–1 range (like an energy of 5), the score used to go
  negative and rank badly — now those values are safely capped. And if someone typed
  a word where a number belonged (like energy = "high"), the program used to crash;
  now it gives a clear error message instead.

---

## 4. Data  

- **Size:** the catalog has **18 songs**, stored in `data/songs.csv`.
- **Genres represented:** pop, indie pop, lofi, rock, ambient, jazz, and synthwave.
  They are uneven — **lofi has the most songs (5)** and pop has 3, while the rest
  have only 2 each.
- **Moods represented:** happy, chill, intense, relaxed, focused, and moody — with
  chill and intense being the most common.
- **Changes I made:** I did not add or remove any songs; I used the provided catalog
  as-is so the results stay comparable.
- **What's missing:** a huge amount of real musical taste. There's no hip-hop, R&B,
  classical, country, metal, or non-English/world music. There are no lyrics,
  no artist popularity, no release year, and no sense of what songs people actually
  listen to together. The catalog is also tiny, so tastes on the edges (very
  experimental or very mainstream) aren't represented.

---

## 5. Strengths  

- **Works well for clearly-defined tastes.** A listener who says "pop, happy, high
  energy" gets an obvious, sensible top pick (Sunrise City) with pop dance tracks
  right behind it — the results match intuition.
- **Captures the calm-vs-energetic axis reliably.** Because energy is weighted
  heavily, asking for low energy consistently surfaces the lofi/ambient songs and
  high energy surfaces the pop/rock songs, which feels correct.
- **Explains itself.** Every recommendation lists its reasons, so it's easy to trust
  and to sanity-check — you can see exactly which parts of your taste it matched.
- **Behaves predictably.** Ties break alphabetically by title, so the same profile
  always returns the same ranking, which made it easy to test.

---

## 6. Limitations and Bias 

- **Features it ignores:** lyrics, language, artist, popularity, era, and how songs
  are actually listened to together. It only sees the seven fields in the CSV.
- **Exact-match blindness (the biggest one):** genre and mood must match *word for
  word*. So "pop" earns zero genre credit for an "indie pop" song even though they're
  almost identical, and calm moods like "chill," "relaxed," and "focused" are treated
  as totally unrelated. Recommendation quality ends up depending on how songs were
  labeled rather than how they actually sound.
- **Underrepresented groups:** most genres have only two songs, and whole categories
  (hip-hop, classical, etc.) are absent, so listeners with those tastes can't be
  served at all.
- **Energy is a hidden stand-in for genre.** In this data, high-energy songs are
  mostly pop/rock and low-energy ones are mostly lofi/ambient, so weighting energy
  heavily quietly pushes people toward certain genres even if they never asked.
- **Overfitting to one preference:** because genre (+2.0) and mood (+1.5) together
  can outweigh the actual audio similarity, a single label match can dominate the
  ranking and drown out songs that are a better all-around fit.
- **Subtle favoritism:** when scores tie, songs whose titles come first
  alphabetically always win — an arbitrary edge unrelated to musical fit.

---

## 7. Evaluation  

- **Profiles I tested:** I ran a range of edge-case profiles through the full catalog
  and saved the top-5 results in the README — an empty profile, single-feature
  profiles (energy-only, genre-only), a case-mismatched genre ("Pop" vs "pop"),
  out-of-range values (energy 5.0 and −3.0), conflicting keys, and a fully-specified
  profile.
- **What I looked for:** whether the top pick made intuitive sense, whether the
  reasons matched the scores, and whether unusual input broke anything or produced
  nonsense rankings.
- **What surprised me:** how much the exact-match rule hurts — a capital "P" in "Pop"
  silently drops every genre point and returns an all-zero, alphabetical list. I was
  also surprised that out-of-range values used to produce *negative* scores, which is
  what led me to add the capping fix.
- **Simple tests I ran:** I wrote an automated test file (`tests/test_edge_cases.py`,
  26 tests) that locks in each behavior — empty profiles, clamping, exact matching,
  key conflicts, and the friendly error for non-numeric input — so future changes
  can't quietly break them.

---

## 8. Future Work  

- **Smarter category matching:** give partial credit for related genres and moods
  (so "indie pop" counts partly as "pop"), using a taste taxonomy or learned
  similarity instead of exact string equality.
- **More and richer data:** a larger catalog with more genres, plus features like
  artist, year, and listening history, so recommendations aren't hostage to labels.
- **Better explanations:** rank the reasons by how much they contributed, and phrase
  them in everyday language ("very similar energy" instead of "energy similarity").
- **More diverse results:** avoid returning five near-identical songs by mixing in
  some variety among the top picks.
- **Handling complex tastes:** let users express multiple favorite genres/moods or
  weight what matters most to them, instead of one target value per field.

---

## 9. Personal Reflection  

Building this showed me that a recommender is really just a scoring rule applied over
and over — there's no magic, just points for matches and closeness, then sorting. The
most interesting discovery was how much the *labels* drive everything: a tiny
mismatch like "Pop" vs "pop" quietly wipes out a big chunk of the score, which made me
realize how fragile these systems can be. It changed how I think about the music apps
I use every day — behind the "For You" playlist is a set of choices about what
features count and how much, and those choices can unintentionally favor some tastes
over others.
