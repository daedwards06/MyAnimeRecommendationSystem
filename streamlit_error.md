[     UTC     ] Logs for myanimerecommendationsystem-x6rqm6vqjmbr2ij8i8yk3b.streamlit.app/

────────────────────────────────────────────────────────────────────────────────────────

[02:11:17] 🚀 Starting up repository: 'myanimerecommendationsystem', branch: 'main', main module: 'app/main.py'

[02:11:17] 🐙 Cloning repository...

[02:11:38] 🐙 Cloning into '/mount/src/myanimerecommendationsystem'...
Updating files: 100% (39506/39506), done.

[02:11:38] 🐙 Cloned repository!

[02:11:38] 🐙 Pulling code changes from Github...

[02:11:48] 📦 Processing dependencies...


──────────────────────────────────────── uv ───────────────────────────────────────────


Using uv pip install.

Using Python 3.13.12 environment at /home/adminuser/venv

Resolved 52 packages in 544ms

  × Failed to download and build `pyarrow==17.0.0`

  ╰─▶ Build backend failed to determine requirements with `build_wheel()`

      (exit status: 1)


      [stderr]

      Traceback (most recent call last):

        File "<string>", line 14, in <module>

          requires = get_requires_for_build({})

        File

      "/home/adminuser/.cache/uv/builds-v0/.tmpAk4vrs/lib/python3.13/site-packages/setuptools/build_meta.py",

      line 333, in get_requires_for_build_wheel

          return self._get_build_requires(config_settings, requirements=[])

                 ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        File

      "/home/adminuser/.cache/uv/builds-v0/.tmpAk4vrs/lib/python3.13/site-packages/setuptools/build_meta.py",

      line 301, in _get_build_requires

          self.run_setup()

          ~~~~~~~~~~~~~~^^

        File

      "/home/adminuser/.cache/uv/builds-v0/.tmpAk4vrs/lib/python3.13/site-packages/setuptools/build_meta.py",

      line 317, in run_setup

          exec(code, locals())

          ~~~~^^^^^^^^^^^^^^^^

        File "<string>", line 34, in <module>

      ModuleNotFoundError: No module named 'pkg_resources'


Checking if Streamlit is installed

Installing rich for an improved exception logging

Using uv pip install.

Using Python 3.13.12 environment at /home/adminuser/venv

Resolved 4 packages in 39ms

Prepared 1 package in 51ms

Installed 4 packages in 19ms

 + markdown-it-py==4.0.0[2026-02-17 02:11:53.450486] 

 + mdurl==0.1.2

 + pygments==2.19.2

 + rich==14.3.2


────────────────────────────────────────────────────────────────────────────────────────



──────────────────────────────────────── pip ───────────────────────────────────────────


Using standard pip install.

Collecting streamlit==1.38.0 (from -r /mount/src/myanimerecommendationsystem/requirements.txt (line 8))

  Downloading streamlit-1.38.0-py2.py3-none-any.whl.metadata (8.5 kB)

Collecting pandas==2.2.2 (from -r /mount/src/myanimerecommendationsystem/requirements.txt (line 11))

  Downloading pandas-2.2.2.tar.gz (4.4 MB)

     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.4/4.4 MB 58.9 MB/s eta 0:00:00[2026-02-17 02:11:55.518423] 

  Installing build dependencies: started

  Installing build dependencies: finished with status 'done'

  Getting requirements to build wheel: started

  Getting requirements to build wheel: finished with status 'done'

  Installing backend dependencies: started

  Installing backend dependencies: finished with status 'done'

  Preparing metadata (pyproject.toml): started

[02:57:30] ❗️ installer returned a non-zero exit code

[02:57:30] ❗️ Error during processing dependencies! Please fix the error and push an update, or try restarting the app.

[02:57:30] 🐙 Pulling code changes from Github...

[02:57:38] 📦 Processing dependencies...