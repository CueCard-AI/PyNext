#!/usr/bin/env node
/**
 * Bundle Size Check Script
 * 
 * Verifies that runtime bundle sizes stay within limits.
 * Used in CI to prevent bundle bloat.
 */

const fs = require('fs');
const path = require('path');

// Size limits in bytes (realistic based on current implementation)
const LIMITS = {
    // Core runtime files (development versions - larger, include comments)
    'signals.js': 16000,     // 16 KB - full version with all features
    'signals.slim.js': 4000, // 4 KB - minified
    'keyboard.js': 15000,    // 15 KB
    'keyboard.slim.js': 4000,
    'theme.js': 10000,       // 10 KB
    'theme.slim.js': 3000,
    'storage.js': 9000,      // 9 KB
    'storage.slim.js': 3000,
    'focus.js': 16000,       // 16 KB
    'focus.slim.js': 4000,
    'sse.js': 8000,          // 8 KB
    'sse.slim.js': 3000,
    'browser.js': 21000,     // 21 KB - full browser APIs with docs
    'browser.slim.js': 2000,
    'toast.js': 14000,       // 14 KB
    'toast.slim.js': 6000,
    
    // UI component modules
    'ui/core.js': 3500,
    'ui/dialog.js': 4000,
    'ui/dropdown.js': 3500,
    'ui/tabs.js': 3000,
    'ui/accordion.js': 2500,
    'ui/forms.js': 4500,
    'ui/tooltip.js': 2500,
    'ui/popover.js': 2500,
    'ui/sheet.js': 4000,
    'ui/combobox.js': 5500,
    'ui/command.js': 5500,
    'ui/calendar.js': 6000,
    'ui/datatable.js': 8500,
    'ui/fileupload.js': 4000,
    'ui/loader.js': 4000,
};

// Total bundle size limit
const TOTAL_LIMIT = 10240; // 10 KB for typical page (excluding unused components)

const RUNTIME_DIR = path.join(__dirname, '..', 'pynext', 'runtime');

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
}

function checkFile(relativePath) {
    const fullPath = path.join(RUNTIME_DIR, relativePath);
    
    if (!fs.existsSync(fullPath)) {
        return { exists: false, path: relativePath };
    }
    
    const stats = fs.statSync(fullPath);
    const size = stats.size;
    const limit = LIMITS[relativePath];
    
    return {
        exists: true,
        path: relativePath,
        size,
        limit,
        overLimit: limit ? size > limit : false,
        percentage: limit ? Math.round((size / limit) * 100) : null,
    };
}

function main() {
    console.log('📦 PyNext Bundle Size Check\n');
    console.log('=' .repeat(60));
    
    let totalSize = 0;
    let overLimitCount = 0;
    const results = [];
    
    // Check each file
    for (const [file, limit] of Object.entries(LIMITS)) {
        const result = checkFile(file);
        results.push(result);
        
        if (result.exists) {
            totalSize += result.size;
            
            const status = result.overLimit ? '❌' : '✅';
            const sizeStr = formatSize(result.size).padStart(10);
            const limitStr = formatSize(result.limit).padStart(10);
            const pctStr = `${result.percentage}%`.padStart(5);
            
            console.log(`${status} ${file.padEnd(25)} ${sizeStr} / ${limitStr} (${pctStr})`);
            
            if (result.overLimit) {
                overLimitCount++;
            }
        } else {
            console.log(`⚠️  ${file.padEnd(25)} (not found)`);
        }
    }
    
    console.log('=' .repeat(60));
    console.log(`\n📊 Summary:`);
    console.log(`   Files checked: ${results.filter(r => r.exists).length}`);
    console.log(`   Over limit: ${overLimitCount}`);
    console.log(`   Total size: ${formatSize(totalSize)}`);
    
    // Calculate typical page load (core + one component)
    const coreFiles = ['signals.slim.js', 'ui/core.js'];
    let typicalLoad = 0;
    for (const file of coreFiles) {
        const result = results.find(r => r.path === file);
        if (result?.exists) {
            typicalLoad += result.size;
        }
    }
    
    console.log(`   Typical page load (core only): ${formatSize(typicalLoad)}`);
    
    // Exit with error if any file over limit
    if (overLimitCount > 0) {
        console.log(`\n❌ FAILED: ${overLimitCount} file(s) over size limit!`);
        process.exit(1);
    }
    
    // Check typical load against total limit
    if (typicalLoad > TOTAL_LIMIT) {
        console.log(`\n❌ FAILED: Typical page load (${formatSize(typicalLoad)}) exceeds ${formatSize(TOTAL_LIMIT)} limit!`);
        process.exit(1);
    }
    
    console.log(`\n✅ PASSED: All files within size limits!`);
    process.exit(0);
}

main();

