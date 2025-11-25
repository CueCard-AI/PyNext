# NPM Packages Guide

PyNext integrates with npm packages through automatic bundling with esbuild. This guide covers installing, using, and optimizing npm packages in your PyNext applications.

## Table of Contents

- [Overview](#overview)
- [Installing Packages](#installing-packages)
- [Using Packages](#using-packages)
- [Popular Packages](#popular-packages)
- [Bundle Optimization](#bundle-optimization)
- [Custom Wrappers](#custom-wrappers)
- [Debugging](#debugging)
- [Best Practices](#best-practices)

---

## Overview

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NPM Package Flow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Configure packages in pynext.config.py                                  │
│     └── npm_packages = ["chart.js", "lodash"]                               │
│                                                                              │
│  2. PyNext installs packages via npm                                        │
│     └── npm install chart.js lodash                                         │
│                                                                              │
│  3. Esbuild bundles packages for browser                                    │
│     └── chart.js → chart.js.bundle.js (ESM)                                │
│     └── lodash → lodash.bundle.js (ESM)                                     │
│                                                                              │
│  4. Bundles served from /_pynext/npm/                                       │
│     └── /_pynext/npm/chart.js.bundle.js                                     │
│                                                                              │
│  5. Import in components                                                    │
│     └── script()[import Chart from '/_pynext/npm/chart.js.bundle.js']      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Auto-bundling** | Packages automatically bundled with esbuild |
| **ESM Output** | Modern ES modules for optimal browser loading |
| **Tree Shaking** | Unused code eliminated from bundles |
| **Caching** | Bundles cached for fast rebuilds |
| **React Compat** | React packages work via Preact aliasing |

---

## Installing Packages

### Configuration

Add packages to `pynext.config.py`:

```python
# pynext.config.py

# Simple package list
npm_packages = [
    "chart.js",
    "lodash",
    "dayjs"
]
```

### Version Pinning

```python
# pynext.config.py

npm_packages = [
    "chart.js",                     # Latest version
    {"lodash": "^4.17.0"},          # Semver range
    {"dayjs": "1.11.10"},           # Exact version
    {"axios": ">=1.0.0 <2.0.0"}     # Version range
]
```

### Manual Installation

Packages are installed automatically when the dev server starts. To install manually:

```bash
# Navigate to .pynext directory
cd .pynext

# Install packages
npm install

# Or install specific package
npm install chart.js
```

### Checking Installed Packages

```bash
# List installed packages
cd .pynext && npm list

# Check for updates
cd .pynext && npm outdated
```

---

## Using Packages

### In Components

```python
from pynext import page, div, canvas, script

@page(title="Chart Demo")
def chart_page():
    return div()[
        canvas(id="myChart", width="400", height="200"),
        
        script(type="module")["""
            import Chart from '/_pynext/npm/chart.js.bundle.js';
            
            const ctx = document.getElementById('myChart');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Red', 'Blue', 'Yellow'],
                    datasets: [{
                        label: 'Votes',
                        data: [12, 19, 3],
                        backgroundColor: ['red', 'blue', 'yellow']
                    }]
                }
            });
        """]
    ]
```

### Using npm_import Helper

```python
from pynext import page, div, script
from pynext.bundler import npm_import

@page
def my_page():
    # Get bundle URL
    chart_url = npm_import("chart.js")
    
    return div()[
        script(type="module")[f"""
            import Chart from '{chart_url}';
            // Use Chart...
        """]
    ]
```

### Dynamic Imports

```python
from pynext import page, div, button, script

@page
def lazy_chart():
    return div()[
        button(id="loadChart")["Load Chart"],
        div(id="chartContainer"),
        
        script(type="module")["""
            document.getElementById('loadChart').onclick = async () => {
                // Lazy load Chart.js only when needed
                const { default: Chart } = await import('/_pynext/npm/chart.js.bundle.js');
                
                const container = document.getElementById('chartContainer');
                container.innerHTML = '<canvas id="myChart"></canvas>';
                
                new Chart(document.getElementById('myChart'), {
                    type: 'line',
                    data: { /* ... */ }
                });
            };
        """]
    ]
```

---

## Popular Packages

### Chart.js - Charts and Graphs

```python
# pynext.config.py
npm_packages = ["chart.js"]
```

```python
# pages/charts.py
from pynext import page, div, canvas, script, server_action
import random

@server_action
async def get_chart_data() -> dict:
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "data": [random.randint(10, 100) for _ in range(6)]
    }

@page(title="Sales Chart")
def charts():
    return div(class_="chart-container")[
        canvas(id="salesChart"),
        
        script(type="module")["""
            import Chart from '/_pynext/npm/chart.js.bundle.js';
            
            // Fetch data from server action
            const response = await fetch('/_pynext/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({actionId: 'get_chart_data', args: {}})
            });
            const { data } = await response.json();
            
            new Chart(document.getElementById('salesChart'), {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Sales',
                        data: data.data,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' }
                    }
                }
            });
        """]
    ]
```

### D3.js - Data Visualization

```python
# pynext.config.py
npm_packages = ["d3"]
```

```python
# pages/visualization.py
from pynext import page, div, script

@page(title="D3 Visualization")
def d3_demo():
    return div()[
        div(id="chart"),
        
        script(type="module")["""
            import * as d3 from '/_pynext/npm/d3.bundle.js';
            
            const data = [30, 86, 168, 281, 303, 365];
            
            const width = 420;
            const barHeight = 25;
            
            const x = d3.scaleLinear()
                .domain([0, d3.max(data)])
                .range([0, width]);
            
            const svg = d3.select("#chart")
                .append("svg")
                .attr("width", width)
                .attr("height", barHeight * data.length);
            
            svg.selectAll("rect")
                .data(data)
                .enter()
                .append("rect")
                .attr("y", (d, i) => i * barHeight)
                .attr("width", x)
                .attr("height", barHeight - 1)
                .attr("fill", "steelblue");
        """]
    ]
```

### Lodash - Utility Functions

```python
# pynext.config.py
npm_packages = [
    "lodash-es"  # ES modules version for tree shaking
]
```

```python
# pages/utilities.py
from pynext import page, div, script

@page
def utilities_demo():
    return div()[
        div(id="output"),
        
        script(type="module")["""
            // Import only what you need (tree shaking)
            import { debounce, throttle, groupBy } from '/_pynext/npm/lodash-es.bundle.js';
            
            // Debounced search
            const searchInput = document.getElementById('search');
            searchInput.addEventListener('input', debounce((e) => {
                console.log('Searching:', e.target.value);
            }, 300));
            
            // Group data
            const users = [
                { name: 'Alice', role: 'admin' },
                { name: 'Bob', role: 'user' },
                { name: 'Charlie', role: 'admin' }
            ];
            
            const grouped = groupBy(users, 'role');
            console.log(grouped);
        """]
    ]
```

### Day.js - Date Handling

```python
# pynext.config.py
npm_packages = ["dayjs"]
```

```python
# pages/dates.py
from pynext import page, div, span, script

@page
def dates_demo():
    return div()[
        span(id="currentTime"),
        
        script(type="module")["""
            import dayjs from '/_pynext/npm/dayjs.bundle.js';
            
            function updateTime() {
                const now = dayjs();
                document.getElementById('currentTime').textContent = 
                    now.format('MMMM D, YYYY h:mm:ss A');
            }
            
            updateTime();
            setInterval(updateTime, 1000);
        """]
    ]
```

### Axios - HTTP Client

```python
# pynext.config.py
npm_packages = ["axios"]
```

```python
# pages/api-client.py
from pynext import page, div, button, script

@page
def api_demo():
    return div()[
        button(id="fetchData")["Fetch Data"],
        div(id="result"),
        
        script(type="module")["""
            import axios from '/_pynext/npm/axios.bundle.js';
            
            document.getElementById('fetchData').onclick = async () => {
                try {
                    const response = await axios.get('https://api.example.com/data');
                    document.getElementById('result').textContent = 
                        JSON.stringify(response.data, null, 2);
                } catch (error) {
                    document.getElementById('result').textContent = 
                        'Error: ' + error.message;
                }
            };
        """]
    ]
```

### Three.js - 3D Graphics

```python
# pynext.config.py
npm_packages = ["three"]
```

```python
# pages/3d.py
from pynext import page, div, script

@page(title="3D Demo")
def threejs_demo():
    return div()[
        div(id="container", style="width: 100%; height: 400px;"),
        
        script(type="module")["""
            import * as THREE from '/_pynext/npm/three.bundle.js';
            
            // Scene setup
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 400, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer();
            
            renderer.setSize(window.innerWidth, 400);
            document.getElementById('container').appendChild(renderer.domElement);
            
            // Create cube
            const geometry = new THREE.BoxGeometry();
            const material = new THREE.MeshBasicMaterial({ color: 0x00ff00, wireframe: true });
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            
            camera.position.z = 5;
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                cube.rotation.x += 0.01;
                cube.rotation.y += 0.01;
                renderer.render(scene, camera);
            }
            
            animate();
        """]
    ]
```

### React Components (via Preact)

```python
# pynext.config.py
npm_packages = ["@mui/material", "@emotion/react", "@emotion/styled"]
react_compat = True  # Enable Preact aliasing
```

See [React Integration](REACT_INTEGRATION.md) for detailed React usage.

---

## Bundle Optimization

### Tree Shaking

Use ES module packages when available:

```python
# pynext.config.py

npm_packages = [
    "lodash-es",      # ✓ ES modules, tree shakeable
    # "lodash",       # ✗ CommonJS, no tree shaking
]
```

Import only what you need:

```javascript
// ✓ Good - only imports used functions
import { debounce, throttle } from '/_pynext/npm/lodash-es.bundle.js';

// ✗ Bad - imports entire library
import _ from '/_pynext/npm/lodash-es.bundle.js';
```

### Code Splitting

Configure code splitting in `pynext.config.py`:

```python
# pynext.config.py

esbuild_options = {
    "splitting": True,
    "format": "esm",
    "chunk_names": "chunks/[name]-[hash]"
}
```

Use dynamic imports for lazy loading:

```javascript
// Load chart library only when needed
button.onclick = async () => {
    const Chart = await import('/_pynext/npm/chart.js.bundle.js');
    // Use Chart...
};
```

### Package Aliases

Create aliases for smaller alternatives:

```python
# pynext.config.py

package_aliases = {
    # Use Preact instead of React (3KB vs 40KB)
    "react": "preact/compat",
    "react-dom": "preact/compat",
    
    # Use Day.js instead of Moment.js (2KB vs 70KB)
    "moment": "dayjs"
}
```

### Bundle Analysis

Analyze bundle sizes:

```bash
pynext build --analyze
```

Output:

```
📊 Bundle Analysis

Package          Size      Gzipped   Tree Shaken
─────────────────────────────────────────────────
three.js         150.2 KB  45.1 KB   Partial
chart.js          45.2 KB  15.1 KB   No
lodash-es         24.1 KB   8.2 KB   Yes (60% removed)
dayjs              2.9 KB   1.2 KB   Yes
─────────────────────────────────────────────────
Total            222.4 KB  69.6 KB

Recommendations:
- Consider lazy loading three.js (largest bundle)
- chart.js could be replaced with lightweight alternative
```

### Minification

```python
# pynext.config.py

esbuild_options = {
    "minify": True,
    "minify_whitespace": True,
    "minify_identifiers": True,
    "minify_syntax": True,
}
```

### External Dependencies

Mark packages as external if loaded from CDN:

```python
# pynext.config.py

esbuild_options = {
    "external": ["react", "react-dom"],  # Loaded from CDN
}

# Then include CDN in your page
head_scripts = [
    '<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>'
]
```

---

## Custom Wrappers

### Python Wrapper for npm Package

Create a Python wrapper for cleaner integration:

```python
# components/chart.py

from pynext import component, div, canvas, script
from pynext.bundler import npm_import

@component
def Chart(chart_type: str, data: dict, options: dict = None):
    """Wrapper component for Chart.js"""
    import json
    
    chart_id = f"chart-{id(data)}"
    chart_url = npm_import("chart.js")
    
    config = {
        "type": chart_type,
        "data": data,
        "options": options or {}
    }
    
    return div(class_="chart-wrapper")[
        canvas(id=chart_id),
        script(type="module")[f"""
            import Chart from '{chart_url}';
            
            const config = {json.dumps(config)};
            const ctx = document.getElementById('{chart_id}');
            new Chart(ctx, config);
        """]
    ]

# Usage
@page
def dashboard():
    return div()[
        Chart(
            chart_type="bar",
            data={
                "labels": ["Jan", "Feb", "Mar"],
                "datasets": [{
                    "label": "Sales",
                    "data": [10, 20, 30]
                }]
            }
        )
    ]
```

### Signal-Connected Wrapper

```python
# components/reactive_chart.py

from pynext import component, Signal, div, canvas, script
import json

@component
def ReactiveChart(data_signal: Signal, chart_type: str = "line"):
    """Chart that updates when signal changes"""
    
    chart_id = f"chart-{id(data_signal)}"
    signal_id = data_signal._signal_id
    
    return div(class_="chart-wrapper")[
        canvas(id=chart_id),
        script(type="module")[f"""
            import Chart from '/_pynext/npm/chart.js.bundle.js';
            
            let chart = null;
            const ctx = document.getElementById('{chart_id}');
            
            // Subscribe to signal changes
            __pynext__.subscribe('{signal_id}', (data) => {{
                if (chart) {{
                    chart.data = data;
                    chart.update();
                }} else {{
                    chart = new Chart(ctx, {{
                        type: '{chart_type}',
                        data: data,
                        options: {{ responsive: true }}
                    }});
                }}
            }});
        """]
    ]
```

### Utility Wrapper

```python
# utils/npm_utils.py

from pynext import script
from pynext.bundler import npm_import

def use_lodash(*functions):
    """Import specific lodash functions"""
    lodash_url = npm_import("lodash-es")
    imports = ", ".join(functions)
    
    return script(type="module")[f"""
        import {{ {imports} }} from '{lodash_url}';
        window._ = {{ {imports} }};
    """]

# Usage
@page
def my_page():
    return div()[
        use_lodash("debounce", "throttle", "groupBy"),
        # Now _.debounce, _.throttle, _.groupBy available globally
    ]
```

---

## Debugging

### Bundle Not Loading

```javascript
// Check if bundle exists
fetch('/_pynext/npm/chart.js.bundle.js')
    .then(r => console.log('Bundle status:', r.status))
    .catch(e => console.error('Bundle error:', e));
```

### Module Import Errors

```javascript
// Debug import issues
try {
    const module = await import('/_pynext/npm/package.bundle.js');
    console.log('Module exports:', Object.keys(module));
} catch (error) {
    console.error('Import error:', error);
}
```

### Bundle Contents

```bash
# Check bundle contents
cat .pynext/bundles/chart.js.bundle.js | head -50

# Check bundle size
ls -la .pynext/bundles/

# Rebuild bundles
rm -rf .pynext/bundles
pynext dev
```

### Esbuild Errors

```bash
# Run esbuild directly for debugging
cd .pynext
npx esbuild node_modules/chart.js --bundle --format=esm --outfile=test.js

# Check for warnings
npx esbuild node_modules/chart.js --bundle --analyze
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Module not found" | Check package is in `npm_packages` config |
| "Cannot use import" | Ensure `type="module"` on script tag |
| "Unexpected token" | Package may need transpilation |
| Large bundle size | Use tree-shakeable package (e.g., lodash-es) |
| React errors | Enable `react_compat = True` |

---

## Best Practices

### 1. Use ES Modules

```python
# ✓ Prefer ES module versions
npm_packages = [
    "lodash-es",    # Not "lodash"
    "date-fns",     # Not "moment"
]
```

### 2. Lazy Load Large Packages

```javascript
// ✓ Lazy load on demand
button.onclick = async () => {
    const { Chart } = await import('/_pynext/npm/chart.js.bundle.js');
    // Use Chart...
};

// ✗ Don't load everything upfront
import Chart from '/_pynext/npm/chart.js.bundle.js';
```

### 3. Import Only What You Need

```javascript
// ✓ Named imports
import { debounce, throttle } from '/_pynext/npm/lodash-es.bundle.js';

// ✗ Full import
import _ from '/_pynext/npm/lodash-es.bundle.js';
```

### 4. Consider Alternatives

| Heavy Package | Lightweight Alternative |
|---------------|------------------------|
| Moment.js (70KB) | Day.js (2KB) |
| Lodash (70KB) | Lodash-es (tree-shakeable) |
| React (40KB) | Preact (3KB) |
| jQuery (85KB) | Native DOM APIs |

### 5. Cache Busting

```python
# pynext.config.py

esbuild_options = {
    "entry_names": "[name]-[hash]",  # Include hash in filename
}
```

### 6. Monitor Bundle Size

```bash
# Regular size checks
pynext build --analyze

# Set size budget in CI
if [ $(stat -f%z .pynext/build/bundles/*.js | awk '{s+=$1} END {print s}') -gt 500000 ]; then
    echo "Bundle size exceeds 500KB limit"
    exit 1
fi
```

---

## Package Compatibility

### Fully Supported

- Pure JavaScript packages
- ES module packages
- Packages without Node.js dependencies

### Requires Configuration

- React packages (need `react_compat = True`)
- Packages with peer dependencies
- CSS-in-JS libraries

### Not Supported

- Node.js-only packages (fs, path, etc.)
- Native modules (C++ bindings)
- Packages requiring server-side rendering

---

## Next Steps

- [React Integration](REACT_INTEGRATION.md) - Using React packages
- [Configuration](CONFIGURATION.md) - Esbuild options
- [Deployment](DEPLOYMENT.md) - Production optimization

