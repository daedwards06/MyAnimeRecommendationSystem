from src.eval.explain import blend_explanations


def test_blend_explanations_contains_shares_and_total():
    sources = {
        'mf': {1: 2.0, 2: 0.5},
        'knn': {1: 1.0},
        'pop': {1: 0.1, 2: 0.1},
    }
    weights = {'mf': 0.6, 'knn': 0.3, 'pop': 0.1}
    out = blend_explanations([1,2], sources, weights)
    assert 1 in out
    assert 'total' in out[1]
    # shares sum to 1 if total > 0
    ttl = out[1]['total']
    if ttl != 0:
        share_sum = sum(v for k, v in out[1].items() if k.endswith('_share'))
        assert abs(share_sum - 1.0) < 1e-6
