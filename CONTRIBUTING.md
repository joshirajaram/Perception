# Contributing

Contribute reusable integrations and extensions built using Perception APIs.
Content is community-provided and separate from the Perception product.

Contributions follow this repository's [MIT license](LICENSE), the Contributor
License Agreement process described in [README.md](README.md), and the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Submit a contribution

1. Fork the repository and create a branch for one contribution.
2. Copy `templates\contribution` into the appropriate content category using a
   descriptive lowercase, hyphen-separated folder name.
3. Replace the template README and manifest with accurate documentation and
   metadata. Include the actual source or deployment artifacts.
4. Include sanitized examples and focused tests where applicable. Do not include
   passwords, tokens, private tenant data, or real customer output.
5. Run the local checks below and submit a pull request using its template.
6. Address validation failures, CLA checks, and maintainer feedback. A maintainer
   approves and merges accepted content; passing static checks is not approval.

## Required documentation

Every contribution must explain its purpose, prerequisites, required permissions,
inputs, deployment or setup, usage, expected results, cost implications, and cleanup.
Distinguish Graph authentication from direct Perception API authentication.

Document and test runtime input validation appropriate to the contribution:
metadata checks alone do not validate URLs, tenant authorization, or deployment
parameters supplied by a user.

Use [manifest conventions](docs/contribution-validation.md) and
[deployment guidance](docs/deployment-guide.md). Browse categories in
[getting started](docs/getting-started.md).

## Local checks

Python 3.10 or newer is required; no additional packages are needed.

```powershell
python -B tools\validation\validate.py
python -B -m unittest discover -s tools\validation -p "test_*.py"
```

## Maintainer configuration

Assign real reviewers in `.github\CODEOWNERS` and configure branch protection to
require their approval and the validation check. Confirm CLA enforcement and
enable secret scanning. CODEOWNERS comments alone enforce nothing.

Follow [SECURITY.md](SECURITY.md) for private vulnerability reporting and
[SUPPORT.md](SUPPORT.md) for support guidance.
