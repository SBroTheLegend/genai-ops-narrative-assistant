# Contributing

This repository is a portfolio sample. Changes should keep a third party able to install, test, and regenerate a brief without an API key.

The development notes in [README.md](README.md) are the working agreement: how to add a metric, how to add a template version, and the review bar a change has to pass. [ARCHITECTURE.md](ARCHITECTURE.md) is the map of module boundaries. If a change moves a threshold, update the policy module, the architecture note, and the tests together. A threshold that lives only in a sentence will drift from the gate.

Do not add real companies, people, customers, credentials, or datasets. Synthetic packs stay marked fictional. The default engine stays deterministic. An external polish hook may be extended, but it stays off unless `OPS_NARRATIVE_LLM=1`, and a polish that fails the review gate is discarded.

Run `pytest` before sending a change. If the brief wording changes, regenerate the committed samples with `ops-narrative samples` so the files in `samples/` match the code.
