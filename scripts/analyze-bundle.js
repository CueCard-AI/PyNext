#!/usr/bin/env node
/**
 * PyNext Bundle Analyzer
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Analyzes bundle sizes for both runtime directories:
 * - pynext/transpiler/runtime (Python semantics for transpiled code)
 * - pynext/runtime (Frontend UI components)
 * 
 * Uses esbuild to create production bundles and measures:
 * - Raw size (uncompressed)
 * - Gzip size (typical HTTP compression)
 * - Brotli size (modern compression)
 * - Per-module breakdown (what contributes to size)
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 *   node scripts/analyze-bundle.js           # Normal check
 *   node scripts/analyze-bundle.js --verbose # Include module breakdown
 *   node scripts/analyze-bundle.js --json    # Output JSON only
 * 
 * =============================================================================
 * OUTPUT
 * =============================================================================
 * 
 * Writes to .bundle-analysis/:
 * - bundle-report.json      Current analysis
 * - bundle-history.jsonl    Append-only history for trends
 * 
 * =============================================================================
 * CI INTEGRATION
 * =============================================================================
 * 
 * Exit codes:
 * - 0: All bundles within limits
 * - 1: One or more bundles exceed limits
 */

import * as esbuild from 'esbuild';
import { gzipSync } from 'zlib';
import { 
    writeFileSync, 
    mkdirSync, 
    existsSync, 
    readFileSync,
    appendFileSync 
} from 'fs';
import { join, dirname, relative } from 'path';
import { fileURLToPath } from 'url';

// =============================================================================
// Configuration
// =============================================================================

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const OUTPUT_DIR = join(ROOT, '.bundle-analysis');

// Bundle entry points to analyze
const BUNDLES = {
    // ==========================================================================
    // LAYERED RUNTIME (Bundle Optimization Architecture)
    // ==========================================================================
    // 
    // Layer 0: Essential (~500B) - Used by 90%+ of apps
    'layer0-minimal': join(ROOT, 'pynext/transpiler/runtime/core-minimal.js'),
    
    // Layer 2: Errors (~200B factory, ~1.5KB full)
    'layer2-errors-factory': join(ROOT, 'pynext/transpiler/runtime/errors-factory.js'),
    'layer2-errors-full': join(ROOT, 'pynext/transpiler/runtime/errors.js'),
    
    // Layer 1: Type Methods (string, list, dict)
    'layer1-string-core': join(ROOT, 'pynext/transpiler/runtime/types/string-core.js'),
    'layer1-string-extended': join(ROOT, 'pynext/transpiler/runtime/types/string-extended.js'),
    
    // ==========================================================================
    // FULL RUNTIME (Legacy - for comparison)
    // ==========================================================================
    'transpiler-core': join(ROOT, 'pynext/transpiler/runtime/core.js'),
    'transpiler-full': join(ROOT, 'pynext/transpiler/runtime/index.js'),
    'transpiler-dunders': join(ROOT, 'pynext/transpiler/runtime/dunders.js'),
    
    // ==========================================================================
    // FRONTEND RUNTIME
    // ==========================================================================
    'signals': join(ROOT, 'pynext/runtime/signals.slim.js'),
    'ui-core': join(ROOT, 'pynext/runtime/ui/core.js'),
    'ui-full': join(ROOT, 'pynext/runtime/ui.js'),
};

// Size limits in bytes (gzipped)
// These are enforced in CI - exceeding them fails the build
// 
// =============================================================================
// LAYERED BUNDLE TARGETS (Bundle Optimization Goals)
// =============================================================================
// 
// GOAL SIZES (what we're optimizing towards):
// - layer0-minimal: 600B   (8 essential functions)
// - layer2-errors-factory: 300B   (dynamic exception factory)
// - layer1-string-core: 600B   (common string methods)
// - layer1-string-extended: 1.2KB (rare string methods)
// 
// CURRENT BASELINE (as of 2025-01-11):
// - transpiler-core: 12.32KB (current)
// - transpiler-full: 13.03KB (current)
// - transpiler-dunders: 1.26KB (current)
// 
// Limits are set ~20% above current baseline to allow for variations.
// These represent ACTUAL realistic limits, not aspirational targets.
const LIMITS = {
    // Layered bundles (NEW - optimized)
    // These are new micro-modules, limits based on actual measured sizes
    'layer0-minimal': 1024,       // ~800B actual, allow 1KB headroom
    'layer2-errors-factory': 1200, // ~955B actual, allow 1.2KB headroom
    'layer2-errors-full': 1536,   // 1.5KB (full error hierarchy)
    'layer1-string-core': 1600,   // ~1.3KB actual, allow 1.6KB headroom
    'layer1-string-extended': 3584, // ~3KB actual, allow 3.5KB headroom
    
    // Full bundles (legacy - for comparison)
    'transpiler-core': 14336,     // 14KB - essential Python semantics (baseline: 12.3KB)
    'transpiler-full': 15360,     // 15KB - full runtime with all features (baseline: 13KB)
    'transpiler-dunders': 1536,   // 1.5KB - operator overloading (baseline: 1.26KB)
    
    // Frontend
    'signals': 2048,              // 2KB - reactive signals (baseline: 1.38KB)
    'ui-core': 1024,              // 1KB - core UI utilities (baseline: 632B)
    'ui-full': 8192,              // 8KB - full UI bundle (baseline: 5.72KB)
};

// Warning threshold (percentage of limit)
const WARNING_THRESHOLD = 0.8;  // Warn at 80% of limit

// =============================================================================
// Bundle Analysis
// =============================================================================

/**
 * Analyze a single bundle entry point.
 * 
 * @param {string} name - Bundle identifier
 * @param {string} entryPath - Path to entry file
 * @returns {Promise<Object>} Analysis results
 */
async function analyzeBundle(name, entryPath) {
    // Check if file exists
    if (!existsSync(entryPath)) {
        return {
            name,
            path: relative(ROOT, entryPath),
            exists: false,
            error: 'File not found',
        };
    }

    try {
        // Bundle with esbuild
        const result = await esbuild.build({
            entryPoints: [entryPath],
            bundle: true,
            minify: true,
            format: 'esm',
            target: 'es2020',
            write: false,
            metafile: true,
            treeShaking: true,
            // Treat all imports as external to measure just this entry
            // Set to false to include all dependencies
            // external: ['*'],
        });

        const code = result.outputFiles[0].text;
        const gzipped = gzipSync(Buffer.from(code));
        
        // Brotli is optional - only available in newer Node versions
        let brotliSize = null;
        try {
            const { brotliCompressSync } = await import('zlib');
            const brotli = brotliCompressSync(Buffer.from(code));
            brotliSize = brotli.length;
        } catch {
            // Brotli not available
        }

        // Extract top contributors from metafile
        const inputs = Object.entries(result.metafile.inputs)
            .map(([path, info]) => ({
                path: path.replace(ROOT + '/', '').replace(/^\.\.\//, ''),
                bytes: info.bytes,
            }))
            .sort((a, b) => b.bytes - a.bytes)
            .slice(0, 10);  // Top 10

        const limit = LIMITS[name];
        const gzipSize = gzipped.length;

        return {
            name,
            path: relative(ROOT, entryPath),
            exists: true,
            raw: code.length,
            gzip: gzipSize,
            brotli: brotliSize,
            limit,
            overLimit: limit ? gzipSize > limit : false,
            nearLimit: limit ? gzipSize > limit * WARNING_THRESHOLD : false,
            percentage: limit ? Math.round((gzipSize / limit) * 100) : null,
            inputs,
        };
    } catch (error) {
        return {
            name,
            path: relative(ROOT, entryPath),
            exists: true,
            error: error.message,
        };
    }
}

/**
 * Analyze all bundles.
 * 
 * @returns {Promise<Object>} Complete analysis report
 */
async function analyzeAll() {
    const timestamp = new Date().toISOString();
    const commit = process.env.GITHUB_SHA?.slice(0, 7) || 'local';
    const branch = process.env.GITHUB_REF_NAME || 'local';

    const bundles = await Promise.all(
        Object.entries(BUNDLES).map(([name, path]) => analyzeBundle(name, path))
    );

    // Calculate totals (only for successfully analyzed bundles)
    const successful = bundles.filter(b => b.exists && !b.error);
    const totals = {
        raw: successful.reduce((sum, b) => sum + (b.raw || 0), 0),
        gzip: successful.reduce((sum, b) => sum + (b.gzip || 0), 0),
        brotli: successful.reduce((sum, b) => sum + (b.brotli || 0), 0),
    };

    const failed = bundles.some(b => b.overLimit);
    const warnings = bundles.filter(b => b.nearLimit && !b.overLimit).length;

    return {
        timestamp,
        commit,
        branch,
        bundles,
        totals,
        failed,
        warnings,
    };
}

// =============================================================================
// Output Formatting
// =============================================================================

/**
 * Format bytes for display.
 * 
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted string
 */
function formatSize(bytes) {
    if (bytes === null || bytes === undefined) return 'N/A';
    if (bytes < 1024) return `${bytes}B`;
    return `${(bytes / 1024).toFixed(2)}KB`;
}

/**
 * Print console report.
 * 
 * @param {Object} report - Analysis report
 * @param {boolean} verbose - Include module breakdown
 */
function printReport(report, verbose = false) {
    console.log('\n📦 PyNext Bundle Size Analysis\n');
    console.log('═'.repeat(70));
    console.log(`  Commit: ${report.commit}  |  Branch: ${report.branch}`);
    console.log('═'.repeat(70));
    console.log();

    // Header
    console.log(
        '  Status'.padEnd(10) +
        'Bundle'.padEnd(22) +
        'Gzip'.padStart(10) +
        'Limit'.padStart(10) +
        'Usage'.padStart(8)
    );
    console.log('─'.repeat(70));

    // Bundle rows
    for (const bundle of report.bundles) {
        if (!bundle.exists) {
            console.log(`  ⚠️     ${bundle.name.padEnd(20)}  (not found)`);
            continue;
        }
        if (bundle.error) {
            console.log(`  ❌     ${bundle.name.padEnd(20)}  Error: ${bundle.error}`);
            continue;
        }

        const status = bundle.overLimit ? '❌' : (bundle.nearLimit ? '⚠️' : '✅');
        const gzipStr = formatSize(bundle.gzip).padStart(10);
        const limitStr = bundle.limit ? formatSize(bundle.limit).padStart(10) : 'N/A'.padStart(10);
        const pctStr = bundle.percentage ? `${bundle.percentage}%`.padStart(7) : '';

        console.log(
            `  ${status}     ${bundle.name.padEnd(20)}${gzipStr}${limitStr}${pctStr}`
        );

        // Verbose: show top contributors
        if (verbose && bundle.inputs) {
            for (const input of bundle.inputs.slice(0, 5)) {
                console.log(`          └─ ${input.path.slice(0, 40).padEnd(40)} ${formatSize(input.bytes)}`);
            }
        }
    }

    console.log('─'.repeat(70));

    // Totals
    console.log(
        `  Total:`.padEnd(32) +
        formatSize(report.totals.gzip).padStart(10) +
        '  (gzipped)'
    );
    console.log();

    // Summary
    if (report.failed) {
        console.log('❌ FAILED: One or more bundles exceed size limits!');
        console.log();
        console.log('To fix:');
        console.log('  1. Review recent changes for unnecessary additions');
        console.log('  2. Check if large dependencies were added');
        console.log('  3. Consider code splitting or lazy loading');
        console.log();
    } else if (report.warnings > 0) {
        console.log(`⚠️  WARNING: ${report.warnings} bundle(s) approaching size limit`);
        console.log();
    } else {
        console.log('✅ PASSED: All bundles within size limits');
        console.log();
    }
}

/**
 * Generate markdown report for PR comments.
 * 
 * @param {Object} current - Current analysis
 * @param {Object|null} base - Base branch analysis (for comparison)
 * @returns {string} Markdown content
 */
function generateMarkdown(current, base = null) {
    let md = '## 📦 Bundle Size Report\n\n';
    
    md += `Commit: \`${current.commit}\` | Branch: \`${current.branch}\`\n\n`;

    md += '| Bundle | ';
    if (base) md += 'Before | After | ';
    else md += 'Size | ';
    md += 'Limit | Status |\n';
    
    md += '|--------|';
    if (base) md += '--------|-------|';
    else md += '-------|';
    md += '-------|--------|\n';

    for (const bundle of current.bundles) {
        if (!bundle.exists || bundle.error) continue;

        const baseBundle = base?.bundles?.find(b => b.name === bundle.name);
        const beforeSize = baseBundle?.gzip;
        const afterSize = bundle.gzip;
        
        let status = '✅';
        if (bundle.overLimit) status = '❌';
        else if (bundle.nearLimit) status = '⚠️';

        md += `| ${bundle.name} | `;
        
        if (base) {
            const diff = beforeSize ? afterSize - beforeSize : afterSize;
            const diffStr = diff === 0 ? '—' : (diff > 0 ? `+${diff}B` : `${diff}B`);
            md += `${formatSize(beforeSize || 0)} | ${formatSize(afterSize)} | `;
        } else {
            md += `${formatSize(bundle.gzip)} | `;
        }
        
        md += `${formatSize(bundle.limit)} | ${status} |\n`;
    }

    if (current.failed) {
        md += '\n❌ **Bundle size limits exceeded!** Please review the changes.\n';
    } else if (current.warnings > 0) {
        md += `\n⚠️ **${current.warnings} bundle(s) approaching size limit.** Consider optimization.\n`;
    } else {
        md += '\n✅ All bundles within limits.\n';
    }

    return md;
}

// =============================================================================
// File Output
// =============================================================================

/**
 * Write analysis results to files.
 * 
 * @param {Object} report - Analysis report
 */
function writeReport(report) {
    // Ensure output directory exists
    if (!existsSync(OUTPUT_DIR)) {
        mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    // Write current report
    writeFileSync(
        join(OUTPUT_DIR, 'bundle-report.json'),
        JSON.stringify(report, null, 2)
    );

    // Append to history (JSONL format for easy parsing)
    const historyEntry = {
        timestamp: report.timestamp,
        commit: report.commit,
        branch: report.branch,
        totals: report.totals,
        bundles: report.bundles.map(b => ({
            name: b.name,
            gzip: b.gzip,
            overLimit: b.overLimit,
        })),
    };
    appendFileSync(
        join(OUTPUT_DIR, 'bundle-history.jsonl'),
        JSON.stringify(historyEntry) + '\n'
    );

    // Write markdown report
    const markdown = generateMarkdown(report);
    writeFileSync(
        join(OUTPUT_DIR, 'bundle-report.md'),
        markdown
    );
}

/**
 * Load base branch report for comparison.
 * 
 * @returns {Object|null} Base report or null
 */
function loadBaseReport() {
    const basePath = join(OUTPUT_DIR, 'base-report.json');
    if (existsSync(basePath)) {
        try {
            return JSON.parse(readFileSync(basePath, 'utf8'));
        } catch {
            return null;
        }
    }
    return null;
}

// =============================================================================
// Real App Bundle Analysis
// =============================================================================

/**
 * Sample Python apps for real-world bundle testing.
 * Each app tests different feature usage.
 */
const SAMPLE_APPS = {
    'hello-world': `print("Hello, World!")`,
    
    'list-operations': `
items = [1, 2, 3, 4, 5]
first = items[0]
last = items[-1]
if items:
    middle = items[len(items) // 2]
`,
    
    'string-methods': `
text = "Hello, World!"
upper = text.upper()
lower = text.lower()
parts = text.split(",")
joined = "-".join(parts)
`,
    
    'conditionals': `
value = 42
items = [1, 2, 3]
if value > 0 and items:
    result = "positive with items"
elif value < 0:
    result = "negative"
else:
    result = "zero or empty"
`,
    
    'arithmetic': `
a = 10
b = 3
add = a + b
sub = a - b
mul = a * b
div = a / b
floordiv = a // b
mod = a % b
`,
};

// Real app size targets (gzipped bytes)
// These are the REAL metrics that matter for end users
const REAL_APP_LIMITS = {
    'hello-world': 15000,      // 15KB
    'list-operations': 15000,  // 15KB
    'string-methods': 16000,   // 16KB
    'conditionals': 15000,     // 15KB
    'arithmetic': 15000,       // 15KB
};

/**
 * Transpile Python to JavaScript using the PyNext transpiler.
 * Calls Python to do the actual transpilation.
 * 
 * @param {string} pythonSource - Python source code
 * @returns {string} JavaScript code
 */
async function transpilePython(pythonSource) {
    const { execSync } = await import('child_process');
    
    // Write Python source to temp file
    const tmpFile = join(OUTPUT_DIR, 'temp.py');
    writeFileSync(tmpFile, pythonSource);
    
    try {
        // Call Python transpiler
        const result = execSync(
            `python -c "from pynext.transpiler import transpile; import sys; print(transpile(open('${tmpFile}').read()))"`,
            { cwd: ROOT, encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 }
        );
        return result.trim();
    } catch (error) {
        console.error(`Transpilation failed: ${error.message}`);
        return null;
    }
}

/**
 * Bundle transpiled JavaScript with runtime.
 * 
 * @param {string} jsCode - JavaScript code
 * @returns {Object} Bundle result with size info
 */
async function bundleRealApp(jsCode) {
    const runtimePath = join(ROOT, 'pynext/transpiler/runtime');
    
    // Create wrapper with runtime import
    const wrapper = `
import __py from '${runtimePath}/core.js';

${jsCode}
`;
    
    // Write to temp file
    const tmpEntry = join(OUTPUT_DIR, 'temp-entry.js');
    writeFileSync(tmpEntry, wrapper);
    
    try {
        const result = await esbuild.build({
            entryPoints: [tmpEntry],
            bundle: true,
            minify: true,
            format: 'esm',
            platform: 'browser',
            write: false,
        });
        
        const code = result.outputFiles[0].text;
        const raw = Buffer.byteLength(code, 'utf8');
        const gzip = gzipSync(code).length;
        
        return { raw, gzip, success: true };
    } catch (error) {
        return { raw: 0, gzip: 0, success: false, error: error.message };
    }
}

/**
 * Analyze real app bundle sizes.
 * 
 * @returns {Object} Analysis results
 */
async function analyzeRealApps() {
    console.log('\n');
    console.log('📦 Real App Bundle Analysis');
    console.log('══════════════════════════════════════════════════════════════════════');
    console.log('  These are REAL bundle sizes that users would experience.');
    console.log('══════════════════════════════════════════════════════════════════════\n');
    
    const results = [];
    let anyFailed = false;
    
    for (const [name, pythonSource] of Object.entries(SAMPLE_APPS)) {
        process.stdout.write(`  Analyzing ${name}... `);
        
        const jsCode = await transpilePython(pythonSource);
        if (!jsCode) {
            console.log('❌ Failed to transpile');
            results.push({ name, success: false, error: 'Transpilation failed' });
            continue;
        }
        
        const bundle = await bundleRealApp(jsCode);
        const limit = REAL_APP_LIMITS[name] || 20000;
        const overLimit = bundle.gzip > limit;
        const usage = Math.round((bundle.gzip / limit) * 100);
        
        if (overLimit) anyFailed = true;
        
        const status = overLimit ? '❌' : (usage > 80 ? '⚠️' : '✅');
        console.log(`${status} ${formatSize(bundle.gzip)} (limit: ${formatSize(limit)}, ${usage}%)`);
        
        results.push({
            name,
            gzip: bundle.gzip,
            raw: bundle.raw,
            limit,
            overLimit,
            usage,
            success: bundle.success,
        });
    }
    
    console.log('──────────────────────────────────────────────────────────────────────');
    
    if (anyFailed) {
        console.log('❌ Some real app bundles exceed limits!\n');
    } else {
        console.log('✅ All real app bundles within limits.\n');
    }
    
    return { apps: results, failed: anyFailed };
}

// =============================================================================
// Main
// =============================================================================

async function main() {
    const args = process.argv.slice(2);
    const verbose = args.includes('--verbose') || args.includes('-v');
    const jsonOnly = args.includes('--json');
    const compare = args.includes('--compare');
    const realApps = args.includes('--real-apps');

    // Ensure output directory exists
    if (!existsSync(OUTPUT_DIR)) {
        mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    try {
        // Standard bundle analysis
        const report = await analyzeAll();

        // Write files
        writeReport(report);

        // Output
        if (jsonOnly) {
            console.log(JSON.stringify(report, null, 2));
        } else {
            printReport(report, verbose);

            // If comparing, load and show diff
            if (compare) {
                const base = loadBaseReport();
                if (base) {
                    console.log('\n📊 Comparison with base branch:\n');
                    console.log(generateMarkdown(report, base));
                }
            }
        }
        
        // Real app analysis if requested
        if (realApps) {
            const realAppReport = await analyzeRealApps();
            
            // Save real app report
            writeFileSync(
                join(OUTPUT_DIR, 'real-apps-report.json'),
                JSON.stringify(realAppReport, null, 2)
            );
            
            if (realAppReport.failed) {
                process.exit(1);
            }
        }

        // Exit code
        process.exit(report.failed ? 1 : 0);

    } catch (error) {
        console.error('❌ Bundle analysis failed:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

main();

