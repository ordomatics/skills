Implement a change in an Odoo module: feature, fix, improvement, removal, refactor, breaking change, or security fix.

## Arguments: $ARGUMENTS

Expected format: `[type] [module] [description]`

Examples:
- `add sale_custom support for custom pricing per partner`
- `fix whatsapp_connector message status not updating on delivery`
- `imp product_ext use read_group instead of loop for variant count`
- `rem hr_custom remove deprecated grade_ids field`
- `ref account_ext extract tax validation into standalone method`
- `breaking sale_custom rename confirm() to action_confirm() for consistency`
- `sec res_partner_ext restrict sensitive fields to managers only`
- `migration sale_custom rename column old_field to new_field`

If type is missing or ambiguous, infer it from the description or ask.

## Change Type Reference

| Type | Tag | What it means |
|------|-----|---------------|
| `add` | [ADD] | New capability, model, field, or endpoint |
| `fix` | [FIX] | Bug correction — restore intended behavior |
| `imp` | [IMP] | Improvement — better UX, performance, or code quality, no API change |
| `rem` | [REM] | Remove a feature, field, method, or view |
| `ref` | [REF] | Refactor — restructure without changing behavior |
| `breaking` | [BREAKING] | API or behavior change that breaks existing callers |
| `sec` | [SEC] | Security fix — access control, injection, data leakage |
| `migration` | [MIGRATION] | DB schema migration script only |

---

## Step 1 — Locate & Read

Before writing a single line, find and read the relevant code. Use Glob and Grep
to locate the right files — do not assume paths.

```bash
# Find the model definition
grep -rn "_name = \"mymodule.mymodel\""

# Find all files related to the module
ls {addons_path}/{module}/

# Search for the specific method, field, or class to change
grep -rn "method_or_field_name" {addons_path}/{module}/

# Find views for a model
grep -rl "model.*mymodule.mymodel" --include="*.xml"
```

Read in full:
- Every Python file you will edit
- Every XML file you will edit
- `__manifest__.py` of the affected module
- `security/ir.model.access.csv` if touching models or fields

Do not edit anything you have not read.

---

## Step 2 — Implement by Type

### ADD — New feature

Determine scope first:
- **New module needed?** → use the `odoo-module-creator` skill
- **Adding to an existing module?** → proceed below

Add in this order:
1. Model fields / methods in `.py`
2. View changes in `.xml` (add xpath if inheriting another module's view)
3. Security: new row in `ir.model.access.csv` if new model; update rules if field is sensitive
4. Register new `.py` in `models/__init__.py` if new file; register new `.xml` in `__manifest__.py` `"data"` if new file
5. Write at least one test covering the happy path

### FIX — Bug fix

1. Reproduce the bug mentally by reading the code path end-to-end
2. Identify the root cause — don't patch the symptom
3. Apply the minimal targeted fix; avoid touching surrounding code
4. Add or update a test that would have caught this bug
5. Check if the same bug exists in sibling modules with the same pattern

### IMP — Improvement

1. Read the current implementation fully
2. Measure / reason about why the current approach is suboptimal
3. Apply the improvement (common examples: replace loop with `read_group`, add `store=True` to computed field used in domain, add `index=True` to filtered field)
4. Verify behavior is unchanged — no API surface should change

### REM — Remove feature

1. Search for all usages of what you're removing across the entire addons tree
2. Remove in reverse dependency order: views → methods → fields → model (if full removal)
3. For **stored fields**: write a migration script to drop the column (see MIGRATION section below)
4. For **XML ids**: check they are not referenced by `ref()` elsewhere
5. Clean up `__init__.py` imports for removed files
6. Remove from `__manifest__.py` `"data"` list if removing a data file

### REF — Refactor

1. Map all callers of what you're moving/renaming with Grep before touching anything
2. Make the structural change
3. Update every caller — no caller should be left broken
4. Run a final Grep to confirm nothing still references the old location/name
5. Behavior must be identical before and after — no logic changes allowed in a REF

### BREAKING — Breaking change

Breaking changes require extra ceremony:

1. Implement the change
2. Write a migration script (see MIGRATION section)
3. Document what breaks in a comment at the top of the changed method/class:
   ```python
   # BREAKING (18.0.X.Y.Z): renamed from old_name(). Update all callers.
   ```
4. The version bump (via `/bump-version`) must be a **minor** or **major** bump, not a patch

### SEC — Security fix

1. Identify the vulnerability: missing ir.rule, overly broad access CSV row, unsanitized input, exposed sensitive field
2. Apply the fix with minimal blast radius
3. Do NOT describe the vulnerability in detail in commit messages or comments — use neutral language
4. Common fixes:
   - Add `ir.rule` to restrict record-level access
   - Change `perm_unlink` from `1` → `0` for regular users
   - Add `groups=` to sensitive fields in views
   - Sanitize user input before passing to external services

### MIGRATION — Migration script

Create the migration file at:

```
{module}/migrations/{version}/
├── pre-migrate.py    # runs before ORM update (use for renaming/dropping)
└── post-migrate.py   # runs after ORM update (use for data backfill)
```

```python
# migrations/18.0.X.Y.Z/pre-migrate.py
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Describe what this migration does."""
    if not version:
        return  # fresh install, nothing to migrate

    cr.execute("""
        ALTER TABLE my_table
        RENAME COLUMN old_field TO new_field
    """)
    _logger.info("Renamed old_field -> new_field in my_table")
```

```python
# migrations/18.0.X.Y.Z/post-migrate.py
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Backfill data after ORM has applied schema changes."""
    if not version:
        return

    cr.execute("""
        UPDATE my_table
        SET new_field = old_computation
        WHERE new_field IS NULL
    """)
    _logger.info("Backfilled new_field in my_table")
```

Use `pre-migrate.py` for: column renames, drops, type changes — anything the ORM would conflict with.
Use `post-migrate.py` for: data backfills, computing new field values from existing data.

---

## Step 3 — Cross-Check

After implementing, verify:

- [ ] Every new `.py` file is imported in `__init__.py`
- [ ] Every new `.xml` file is listed in `__manifest__.py` `"data"` (security files before views)
- [ ] No model that `_inherit`s the changed model is broken by the change
- [ ] If a stored field was added/removed: a migration script exists
- [ ] If a view was extended from another module: used `inherit_id` + xpath, not direct edit

---

## Step 4 — Bump Version

After implementing, run `/bump-version {module}` to update the version and changelog
with the appropriate tag for this change type.

---

## Step 5 — Verify

```bash
# Update the module (catches XML errors, missing security rows, import errors)
odoo-bin -d {db} -u {module} --stop-after-init

# Run tests
odoo-bin -d {db} --test-enable --stop-after-init --test-tags={module}

# Lint
ruff check {addons_path}/{module} --fix
```

Adjust the command to match your project's setup (docker compose, virtual env, etc.).
