from src.models.hybrid import weighted_blend


def test_weighted_blend_topk_and_order():
    scores = {
        'mf': {1: 0.9, 2: 0.1},
        'knn': {2: 0.8, 3: 0.5},
        'pop': {3: 0.7, 4: 0.6},
    }
    weights = {'mf': 0.5, 'knn': 0.3, 'pop': 0.2}
    recs = weighted_blend(scores, weights, top_k=2)
    assert len(recs) == 2
    assert recs[0] in {1,2,3}
