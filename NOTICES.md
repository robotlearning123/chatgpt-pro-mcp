# Third-Party Notices

This project includes portions of code from:

## lanqian528/chat2api

- **License:** MIT License
- **Copyright:** Copyright (c) 2024 aurora-develop
- **Source:** https://github.com/lanqian528/chat2api
- **Files derived from upstream:**
  - `openai_mcp/_vendored/pow.py` — ported from `chatgpt/proofofWork.py`
  - `openai_mcp/_vendored/turnstile.py` — ported from `chatgpt/turnstile.py`

Modifications: removed `diskcache`, `pybase64`, `ua_generator`, and `utils.*`
dependencies in favor of the Python standard library; reduced to the minimum
surface needed to produce Sentinel `proof` and `turnstile` tokens.

Full MIT license text is preserved in each vendored file's header and may be
obtained from the upstream repository.
