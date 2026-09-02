# Contributing & Branch Policy

## 1. Branch Protection Policy for `main`

The `main` branch is protected. The following rules are enforced:

* **No Direct Pushes:** All changes must be submitted via a Pull Request (PR). Direct pushes to `main` are rejected.
* **Required Green CI:** A PR cannot merge unless all CI checks (linting, type checking, tests, and lockfile validation) pass.
* **Review Approval:** At least one approving review is required before merging.
* **Linear History:** Use **Squash and Merge** or **Rebase and Merge**. Force pushes and merge commits are disabled.

---

## 2. Developer Workflow

1. Create a feature branch off `main`:
   ```bash
   git checkout -b feat/<short-description>
   ```
2. Run local checks before pushing:
   ```bash
   uv run ruff check .
   uv run mypy .
   uv run pytest
   ```
3. Open a Pull Request using the repository PR template.

---

## 3. Hotfix Exception Path

For urgent production fixes:
1. Create a branch named `hotfix/<description>`.
2. Implement the minimal required fix.
3. Open a PR with the `hotfix` label.
4. Obtain expedited approval from the Lead Developer. CI must still pass before merging.
