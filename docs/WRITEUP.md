# MARS: What I Built, What Went Wrong, and What I Learned

MARS is an anime recommender with a [live demo](../README.md). This page tells the story of the
project: what I set out to do, how it is built, which results held up, and the mistakes I made
along the way and how each one was caught. All numbers come from the reports linked inline.

## The problem and the data

I wanted a recommender that does two jobs. Given a title someone liked, it finds others with the
same feel. Given a person's rating history, it finds titles for them. Each card also had to say in
plain words why it was picked.

The ratings came from a Kaggle MyAnimeList snapshot: 7,813,730 interactions from 73,515 users over
11,200 titles. Metadata and synopses for the wider catalog of about 13,000 titles came from the
Jikan API ([data sources](DATA_SOURCES.md)). Two properties of this data mattered more than I
expected. 19% of the ratings are a "watched, not rated" code that my cleaning step had turned
into 0. The snapshot also has no interaction dates.

## Approach

The pipeline has three stages ([scoring pipeline guide](scoring_pipeline_integration_guide.md)).
Stage 0 gathers candidates from synopsis-embedding neighbors, metadata overlap and a popularity
backfill. Stage 1 cuts that to a shortlist with semantic admission gates and type filters.
Stage 2 reranks the shortlist with a collaborative-filtering score plus genre overlap and
synopsis similarity. A post-processing step then caps franchise entries and blends in the
personal profile.

I split it this way because the two kinds of signal fail in opposite ways. Collaborative
filtering knows taste but knows nothing about titles newer than the rating snapshot. Content
similarity knows every title but ranks poorly. Content decides what is eligible, and
collaborative filtering joins it in deciding the order. The hybrid exists for the same reason. On its own,
TF-IDF content similarity spreads its top-10 lists across 0.1711 of the catalog, the widest of
any model, yet its NDCG@10 of 0.0211 is below popularity's 0.0347.

## Results

![Accuracy vs. coverage: NDCG@10 against Coverage@10 for ten model variants, with 95% bootstrap intervals](../reports/figures/ablation_accuracy_vs_coverage.png)

I scored every variant on one cohort: 1,000 validation users, seed 42, ranking the full catalog,
with collaborative models fit on the train split only ([ablation](../reports/phase4_ablation.md)).
The served blend reaches NDCG@10 0.0658, CI [0.0535, 0.0795]. It beats popularity by a paired
CI of [+0.0175, +0.0454], but it is tied with item-kNN alone ([-0.0036, +0.0091]), because it is
95% item-kNN. Matrix factorization on its own is tied with popularity. An implicit-feedback ALS
that I evaluated but have not yet served scores 0.1890, about three times anything else. A
LightGBM LambdaRank reranker over the blend's top 200 candidates reached 0.0931 averaged over three
seeds, every paired CI above zero ([learned reranker](../reports/learned_reranker.md)). It ships
behind a flag that is off by default.

## What went wrong and how it was caught

Most of what I learned came from finding out that earlier numbers were wrong.

**The headline lift compared the baseline with itself.** The README once claimed
`+43% NDCG / +61% MAP` for the hybrid. That was popularity on a 500-user cohort measured against
popularity on a 300-user cohort. The ablation script filtered on model names that did not exist
in the metrics file, so every collaborative row was silently dropped, and the lift used whichever
row came first as the baseline. A review that read the table the way a stranger would caught it:
ten rows, all labeled `popularity`. I rebuilt the table so every number comes from one cohort and
one run, made the scripts refuse a mixed-cohort frame, and added a test that recomputes every
number in the README from the ablation CSV ([decision log](decisions.md), 2026-09-16).

**An exclusion bug hid the best model.** Item-kNN had been published at NDCG@10 0.0017 and written
off as a weak model. Its "exclude already seen" step used the model's own fitted matrix, and that
matrix contained the held-out item, so the right answer was removed before scoring. A controlled
reproduction showed the item was masked for 300/300 users. Scored against train-split artifacts,
kNN became the strongest single model at 0.0632
([evaluation report](../reports/phase4_evaluation.md) §8). The same diagnosis later turned up two
smaller cousins of this bug. MF scored users with no history in item-index order, which acted
as an accidental popularity fallback. kNN's mask also let 0-rated titles through. The lesson I
wrote down was that an exclusion set must come from the evaluation split, never from the model.

**The weights were tuned under the broken protocol, on the reporting users.** The shipped blend,
mf 0.931 / knn 0.066 / pop 0.003, came from an Optuna sweep run while kNN could not score. It drew
its users with the same seed from the same population as the reporting cohort. Re-tuned on users
disjoint from that cohort, the weights flipped to mf 0.048 / knn 0.952, and NDCG@10 went from
0.0324 to 0.0658. Then I found that the app did not load a kNN component at all, so the new
weights could not be served by editing constants. I recorded that as a stop instead of shipping an
unmeasured ranking, then built per-request kNN scoring from seed titles or profile ratings before
switching the app over.

**A small test told me a leak was harmless, and it was wrong.** Early on, the evaluation scored
models fit on all interactions against holdouts drawn from those same interactions. On a 120K-row
slice, refitting without the held-out rows changed MF by a mean of −0.0018, so I concluded the
leak did not matter. At full scale the leak was worth 0.0230 NDCG@10, with an interval clear of
zero ([MF diagnostic](../reports/mf_diagnostic.md) §2). I had already switched to train-split
artifacts on principle, which is the only reason the published numbers were clean.

## What did not work

**Rating-trained matrix factorization for top-N.** FunkSVD scores 0.0282, tied with popularity
at a paired −0.0065 [−0.0172, +0.0049]. It predicts ratings, and the data taught it that a fifth
of what people watch is worth 0, so it ranks a watched-but-unrated holdout at a median 9,463 of
11,200. Dropping those rows made it worse (−0.0178), because the zeros are its only trace of what
people choose to watch. Implicit ALS on watched versus not watched fixed this, and it is also
ahead on liked holdouts alone.

**Neural embeddings for content.** I expected MiniLM synopsis embeddings to beat TF-IDF. They
scored 0.0101 against TF-IDF's 0.0211, with lower coverage. In the learned reranker, TF-IDF
similarity carries the largest gain share (0.168) and neural similarity 0.029. I also could not
measure cold start properly. None of the 1,000 cohort users had a held-out title with no rating
history, so the cold-start run reported 0.0 with no support behind it.

**Synthetic timestamps.** With no dates in the snapshot, the "temporal" split ordered interactions
by row index. It reported NDCG@10 0.4383 and coverage 0.0018, an order of magnitude above every
like-for-like number, which points to ordering artifacts rather than better ranking. I kept it as
a heuristic check and dropped it as an accuracy claim.

## Product decisions

**Explanations.** Cards first showed a debug line such as `CF 0.0% | Content 94.9% |
Popularity 5.1%`. To a visitor, "CF 0.0%" reads as "the model did nothing", and the line was also
mislabeled: the share called "Content" belonged to the item-kNN key. I replaced it with a sentence
built from whichever signals dominate, for example the genres a title shares with the seed, a
very similar story, or that fans of the seed also rate it highly. I split true content signals
out from kNN and moved the corrected breakdown under "More details".

**Honest match labels.** A "98% Match" badge was assigned to rank 1 by construction, even though
the scores are uncalibrated. Cards now say `Top match` through `Worth a look` by quartile within
the run, with the rank alongside.

**Discovery by default.** For a Steins;Gate seed under "similar vibes", the top result was a
Steins;Gate special. Discovery is now the default, with franchise entries hidden from the
displayed list unless "Include sequels & spin-offs" is checked.

**Demo profiles.** Personalization was the most distinctive feature, and no reviewer would export
their MyAnimeList history to see it. I built two fictional, read-only taste profiles that load
with one click ([personalization guide](user_guide_personalization.md)). I also measured the
deployed app, at a median 10.9 s to the first card, and added a scheduled browser visit that
keeps it from sleeping ([deployment](DEPLOYMENT.md)).

## What I would do next

The segment analysis ([notebook 03](../notebooks/03_segment_and_error_analysis.ipynb)) set the
order:

1. **Fix first-stage recall.** For 70.9% of the users the blend missed, the held-out title was not
   in its top 200, and the reranker can only reorder what it is given (37% candidate recall).
   Implicit ALS leads in every activity quartile, so I would swap it in for candidate generation,
   after the liked-only check the MF diagnostic asks for, then retrain the reranker on the new
   candidates.
2. **Make the cold-start fallback explicit.** The blend beats item-kNN only for the least active
   quarter of users (+0.0170). The whole edge comes from users kNN cannot score, where the MF and
   popularity terms rank alone. Nobody designed that fallback. I would route those users to a
   declared one and say so in the UI.
3. **Give all-0 raters a watched signal.** 4.9% of the cohort rated every title 0, so
   rating-weighted kNN builds them no profile.
4. **Measure the tail before claiming it.** No model hits anything below the eighth popularity
   decile, so higher coverage is not yet evidence of long-tail discovery.
5. **Evaluate the full pipeline end to end.** The ablation scores the CF blend alone. The Stage 1
   gates were set by hand against golden-query reports, and the Stage 2 coefficient was matched
   to the old score scale rather than tuned. Both deserve the same offline measurement.
