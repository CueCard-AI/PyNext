# PyNext Bundle Analysis Guide

A comprehensive guide to analyzing and optimizing bundle sizes in PyNext, designed for developers, CI systems, and AI assistants.

---

## WHO Should Read This

- **Developers**: Monitor bundle sizes before committing to prevent bloat
- **CI/CD Pipelines**: Automatically fail builds if bundles exceed limits
- **AI Assistants/LLMs**: When implementing features, check that bundle sizes don't grow unexpectedly

---

## WHAT Gets Analyzed

PyNext has a layered runtime architecture:

| Layer | Module | Target Size | Purpose |
|-------|--------|-------------|---------|
| 0 | `core-minimal.js` | ~800B | Essential functions (`at`, `slice`, `bool`, etc.) |
| 1 | `string-core.js` | ~1.3KB | Common string methods |
| 1 | `string-extended.js` | ~3.5KB | Less common string methods |
| 2 | `errors-factory.js` | ~1KB | Dynamic exception creation |
| 2 | `errors.js` (full) | ~1.5KB | All exception classes |
| 2 | `dunders.js` | ~1.5KB | Operator overloading |
| Full | `transpiler-core` | ~14KB | Core transpiler runtime |
| Full | `transpiler-full` | ~15KB | Complete transpiler runtime |

---

## WHEN To Check Bundle Sizes

| Scenario | Command |
|----------|---------|
| Quick check before commit | `make bundle` |
| Full analysis with breakdown | `make bundle-verbose` |
| Real app sizes (most accurate) | `make bundle-real-apps` |
| CI/CD pipeline | `make bundle` (auto-fails on limit exceeded) |

---

## WHERE To Run Commands

All commands should be run from the **project root**:

```bash
cd /path/to/PyNext
```

---

## WHY Bundle Size Matters

- **Performance**: Smaller bundles = faster page loads
- **User Experience**: Mobile users especially benefit from small bundles
- **Tree Shaking**: Layered modules enable efficient tree shaking
- **Cost**: Less data transfer = lower hosting costs

---

## HOW To Analyze Bundles

### Quick Commands

```bash
# Basic check (most common)
make bundle

# Include real app bundle sizes
make bundle-real-apps

# Full verbose analysis
make bundle-verbose

# Output as JSON (for scripts)
make bundle-json
```

### Using Python (Alternative)

```bash
# Basic check
python scripts/bundle_analyzer.py

# Real apps
python scripts/bundle_analyzer.py --real-apps

# Verbose
python scripts/bundle_analyzer.py --verbose

# JSON output
python scripts/bundle_analyzer.py --json
```

### Programmatic Use (Python)

```python
from scripts.bundle_analyzer import analyze_bundles, analyze_real_apps

# Analyze runtime bundles
report = analyze_bundles()
print(f"Total: {report['totals']['gzip']} bytes")

# Check if any bundles exceed limits
if report.get('failed'):
    print("❌ Some bundles exceed limits!")
    for bundle in report['bundles']:
        if bundle.get('overLimit'):
            print(f"  - {bundle['name']}: {bundle['gzip']}B > {bundle['limit']}B")

# Analyze real transpiled apps
real_report = analyze_real_apps()
```

---

## Interpreting Results

### Status Icons

| Icon | Meaning |
|------|---------|
| ✅ | Under limit (safe) |
| ⚠️ | Approaching limit (>80% of limit) |
| ❌ | Over limit (CI will fail) |

### Example Output

```
📦 PyNext Bundle Size Analysis
══════════════════════════════════════════════════════════════════════
  Commit: abc1234  |  Branch: main
══════════════════════════════════════════════════════════════════════

  Status  Bundle                      Gzip     Limit   Usage
──────────────────────────────────────────────────────────────────────
  ✅     layer0-minimal            799B    1.00KB    78%
  ✅     layer2-errors-factory      955B    1.17KB    80%
  ⚠️     layer2-errors-full      1.23KB    1.50KB    82%
  ⚠️     layer1-string-core      1.28KB    1.56KB    82%
  ✅     layer1-string-extended    1.28KB    3.50KB    37%
  ⚠️     transpiler-core        12.48KB   14.00KB    89%
  ⚠️     transpiler-full        13.17KB   15.00KB    88%

══════════════════════════════════════════════════════════════════════
  Total: 21.42KB gzip

⚠️  WARNING: 4 bundle(s) approaching limit
```

---

## Bundle Limits

Current limits are defined in `scripts/analyze-bundle.js`:

```javascript
const LIMITS = {
  'layer0-minimal': 1024,           // 1KB
  'layer1-string-core': 1600,       // 1.56KB
  'layer1-string-extended': 3584,   // 3.5KB
  'layer2-errors-factory': 1200,    // 1.17KB
  'layer2-errors-full': 1536,       // 1.5KB
  'layer2-dunders': 1536,           // 1.5KB
  'transpiler-core': 14336,         // 14KB
  'transpiler-full': 15360,         // 15KB
  // ...
};
```

---

## Optimizing Bundle Size

### If a bundle exceeds limits:

1. **Identify the culprit**
   ```bash
   make bundle-verbose
   # Look at the module breakdown to find large modules
   ```

2. **Check for duplications**
   - Core functions should be in `core-minimal.js` only
   - String methods should be in `string-core.js` only

3. **Use dynamic imports for stdlib**
   - Stdlib modules are lazily loaded
   - Only imported modules are bundled

4. **Inline simple methods**
   - The transpiler inlines methods like `.upper()` → `.toUpperCase()`
   - Check `pynext/transpiler/optimizer/inline.py`

5. **Run real app analysis**
   ```bash
   make bundle-real-apps
   ```
   This shows actual bundle sizes for common use cases.

---

## CI/CD Integration

### GitHub Actions

Bundle size is automatically checked on every push:

```yaml
- name: Check bundle sizes
  run: make bundle
```

If any bundle exceeds its limit, the CI will fail.

### PR Comments

On pull requests, the workflow posts a comment comparing bundle sizes between the base branch and the PR:

```
📦 Bundle Size Report

| Bundle | Base | PR | Δ |
|--------|------|-----|-----|
| transpiler-full | 13.1KB | 13.5KB | +400B ⚠️ |
```

---

## Troubleshooting

### "Cannot find module 'esbuild'"

```bash
npm install
```

### Analysis is slow

The analyzer caches results in `.bundle-analysis/`. Clear it to force re-analysis:

```bash
rm -rf .bundle-analysis/
make bundle
```

### Bundle size unexpectedly grew

1. Check what changed:
   ```bash
   git diff HEAD~1 -- pynext/transpiler/runtime/
   ```

2. Run verbose analysis:
   ```bash
   make bundle-verbose
   ```

3. Compare with previous commit:
   ```bash
   git stash
   make bundle-json > /tmp/before.json
   git stash pop
   make bundle-json > /tmp/after.json
   diff /tmp/before.json /tmp/after.json
   ```

---

## Summary

| What You Want | Command |
|---------------|---------|
| Quick check | `make bundle` |
| Real app sizes | `make bundle-real-apps` |
| Full breakdown | `make bundle-verbose` |
| JSON output | `make bundle-json` |
| Python CLI | `python scripts/bundle_analyzer.py` |
| Programmatic | `from scripts.bundle_analyzer import analyze_bundles` |

