# PyNext Charts

Chart components built on Chart.js for data visualization.

## Installation

Add Chart.js to your layout:

```python
from pynext.charts import ChartJSLoader

@layout
def root_layout(children):
    return html()[
        head()[
            ChartJSLoader(),  # Include Chart.js
        ],
        body()[children]
    ]
```

## Components

```python
from pynext.charts import Chart, LineChart, BarChart, PieChart, AreaChart
```

## Quick Start

```python
# Simple line chart
LineChart(
    data=[
        {"month": "Jan", "sales": 100},
        {"month": "Feb", "sales": 120},
        {"month": "Mar", "sales": 90},
    ],
    x="month",
    y="sales",
    title="Monthly Sales"
)
```

## Line Chart

```python
LineChart(
    data=sales_data,
    x="month",
    y="revenue",
    title="Monthly Revenue",
    smooth=True,      # Curved lines
    fill=False,       # No area fill
    height="300px"
)

# Multi-series
LineChart(
    data=comparison_data,
    x="month",
    y=["2023", "2024"],  # Multiple series
    title="Year over Year"
)
```

## Bar Chart

```python
# Vertical bars
BarChart(
    data=sales_by_region,
    x="region",
    y="total",
    title="Sales by Region"
)

# Horizontal bars
BarChart(
    data=data,
    x="category",
    y="value",
    horizontal=True
)

# Stacked bars
BarChart(
    data=quarterly_data,
    x="quarter",
    y=["product_a", "product_b"],
    stacked=True
)
```

## Pie / Donut Chart

```python
# Pie chart
PieChart(
    data=market_share,
    label="company",
    value="share",
    title="Market Share"
)

# Donut chart
PieChart(
    data=distribution,
    label="category",
    value="amount",
    donut=True
)
```

## Area Chart

```python
AreaChart(
    data=traffic_data,
    x="date",
    y="visitors",
    title="Website Traffic"
)

# Stacked area
AreaChart(
    data=source_data,
    x="date",
    y=["direct", "organic", "referral"],
    stacked=True
)
```

## Full Chart.js Configuration

For complete control, use the base `Chart` component:

```python
Chart(
    type="line",
    data={
        "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
        "datasets": [{
            "label": "Revenue",
            "data": [100, 200, 150, 300, 250],
            "borderColor": "rgb(75, 192, 192)",
            "backgroundColor": "rgba(75, 192, 192, 0.2)",
            "tension": 0.4,
            "fill": True
        }]
    },
    options={
        "responsive": True,
        "plugins": {
            "legend": {"position": "top"},
            "title": {"display": True, "text": "Revenue Chart"}
        },
        "scales": {
            "y": {"beginAtZero": True}
        }
    }
)
```

## API Reference

### LineChart / AreaChart

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `list[dict]` | required | Data points |
| `x` | `str` | `None` | X-axis key |
| `y` | `str \| list` | `None` | Y-axis key(s) |
| `title` | `str` | `None` | Chart title |
| `smooth` | `bool` | `True` | Curved lines |
| `fill` | `bool` | `False` | Fill area |
| `height` | `str` | `"300px"` | Chart height |
| `colors` | `list` | `None` | Custom colors |

### BarChart

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `list[dict]` | required | Data points |
| `x` | `str` | `None` | X-axis key |
| `y` | `str \| list` | `None` | Y-axis key(s) |
| `horizontal` | `bool` | `False` | Horizontal bars |
| `stacked` | `bool` | `False` | Stack bars |

### PieChart

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `list[dict]` | required | Data points |
| `label` | `str` | `None` | Label key |
| `value` | `str` | `None` | Value key |
| `donut` | `bool` | `False` | Donut style |

### Chart (Base)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `str` | `"line"` | Chart.js type |
| `data` | `dict` | `{}` | Chart.js data config |
| `options` | `dict` | `{}` | Chart.js options |
| `height` | `str` | `"300px"` | Chart height |
| `responsive` | `bool` | `True` | Responsive sizing |

## Dark Mode

Charts automatically adapt to dark mode by detecting the `dark` class on the document. Colors and grid lines adjust accordingly.

## Custom Colors

```python
LineChart(
    data=data,
    x="month",
    y="value",
    colors=["#3b82f6", "#10b981", "#f59e0b"]
)
```

Default colors use CSS variables that match your theme:
- `hsl(var(--chart-1))`
- `hsl(var(--chart-2))`
- etc.

