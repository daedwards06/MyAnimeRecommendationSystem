=========================================================================================================== FAILURES ===========================================================================================================
_______________________________________________________________________________________________________ test_app_import ________________________________________________________________________________________________________

    def test_app_import():
        # Enable lightweight mode to bypass heavy artifact loading in tests.
        os.environ["APP_IMPORT_LIGHT"] = "1"
>       __import__("app.main")

tests\test_app_import.py:9:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
app\main.py:135: in <module>
    recs = recommender.get_top_n_for_user(user_index, n=top_n, weights=weights)
src\app\recommender.py:122: in get_top_n_for_user
    top_idx = np.argpartition(scores, -n)[-n:]
.venv\Lib\site-packages\numpy\core\fromnumeric.py:858: in argpartition
    return _wrapfunc(a, 'argpartition', kth, axis=axis, kind=kind, order=order)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

obj = array([0.01928998], dtype=float32), method = 'argpartition', args = (-10,), kwds = {'axis': -1, 'kind': 'introselect', 'order': None}, bound = <built-in method argpartition of numpy.ndarray object at 0x0000020A8D160B70>

    def _wrapfunc(obj, method, *args, **kwds):
        bound = getattr(obj, method, None)
        if bound is None:
            return _wrapit(obj, method, *args, **kwds)

        try:
>           return bound(*args, **kwds)
E           ValueError: kth(=-9) out of bounds (1)

.venv\Lib\site-packages\numpy\core\fromnumeric.py:59: ValueError
----------------------------------------------------------------------------------------------------- Captured stderr call -----------------------------------------------------------------------------------------------------
2025-11-22 14:01:36.700 WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
2025-11-22 14:01:36.706 WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
2025-11-22 14:01:36.710 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:36.711 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.236
  Warning: to view this Streamlit app on a browser, run it with the following
  command:

    streamlit run C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\.venv\Scripts\pytest [ARGUMENTS]
2025-11-22 14:01:38.237 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.238 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.238 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.238 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.238 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.239 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.239 Session state does not function when running a script without `streamlit run`
2025-11-22 14:01:38.239 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.240 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.240 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.240 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.240 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.241 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.241 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.241 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.241 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.242 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.242 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.242 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.242 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.242 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.243 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.243 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.244 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.244 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.244 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.245 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.253 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.253 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.253 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-11-22 14:01:38.253 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
======================================================================================================= warnings summary =======================================================================================================
tests/test_splits.py::test_build_validation_basic
  C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\src\eval\splits.py:28: DeprecationWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
    .apply(lambda g: g.sample(1, random_state=rng.randint(0, 1_000_000)))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================================================================================== short test summary info ====================================================================================================
FAILED tests/test_app_import.py::test_app_import - ValueError: kth(=-9) out of bounds (1)
1 failed, 17 passed, 1 warning in 23.13s
