"""
PyNext Charts

Chart components built on Chart.js for data visualization.
Automatically handles dark mode, responsive sizing, and PyNext integration.

Usage:
    from pynext.charts import Chart, LineChart, BarChart, PieChart, AreaChart
    
    # Simple line chart
    LineChart(
        data=sales_data,
        x="month",
        y="revenue",
        title="Monthly Revenue"
    )
    
    # Multi-series bar chart
    BarChart(
        data=comparison_data,
        x="category",
        y=["2023", "2024"],
        title="Year over Year Comparison"
    )
    
    # Pie/Donut chart
    PieChart(
        data=distribution_data,
        label="category",
        value="amount",
        donut=True
    )
    
    # Full configuration
    Chart(
        type="line",
        data={
            "labels": ["Jan", "Feb", "Mar"],
            "datasets": [{
                "label": "Sales",
                "data": [100, 200, 150]
            }]
        },
        options={
            "responsive": True,
            "plugins": {"legend": {"position": "top"}}
        }
    )
"""

from typing import Any, Optional, List, Union, Dict, Literal
from pynext.tw import cn
import json
import hashlib


# Chart container styles
CHART_CONTAINER_BASE = "relative"

# Default colors (matches Tailwind/ShadCN theme)
DEFAULT_COLORS = [
    "hsl(var(--chart-1))",
    "hsl(var(--chart-2))",
    "hsl(var(--chart-3))",
    "hsl(var(--chart-4))",
    "hsl(var(--chart-5))",
]

# Fallback colors if CSS variables aren't set
FALLBACK_COLORS = [
    "#2563eb",  # blue-600
    "#16a34a",  # green-600
    "#dc2626",  # red-600
    "#ca8a04",  # yellow-600
    "#9333ea",  # purple-600
    "#0891b2",  # cyan-600
    "#db2777",  # pink-600
    "#ea580c",  # orange-600
]


class Chart:
    """
    Base chart component wrapping Chart.js.
    
    Attributes:
        type: Chart type ("line", "bar", "pie", "doughnut", "area", "radar", etc.)
        data: Chart.js data configuration
        options: Chart.js options configuration
        height: Chart height (default "300px")
        width: Chart width (default "100%")
        responsive: Whether chart is responsive
        class_: Additional CSS classes
    
    Example:
        Chart(
            type="line",
            data={
                "labels": ["Jan", "Feb", "Mar"],
                "datasets": [{
                    "label": "Revenue",
                    "data": [100, 200, 150],
                    "borderColor": "rgb(75, 192, 192)",
                }]
            }
        )
    """
    
    def __init__(
        self,
        type: str = "line",
        data: Optional[Dict] = None,
        options: Optional[Dict] = None,
        height: str = "300px",
        width: str = "100%",
        responsive: bool = True,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.type = type
        self.data = data or {"labels": [], "datasets": []}
        self.options = options or {}
        self.height = height
        self.width = width
        self.responsive = responsive
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        chart_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        # Merge default options
        merged_options = {
            "responsive": self.responsive,
            "maintainAspectRatio": False,
            **self.options
        }
        
        class_str = cn(CHART_CONTAINER_BASE, self.extra_class)
        
        # Serialize config
        config = {
            "type": self.type,
            "data": self.data,
            "options": merged_options,
        }
        config_json = json.dumps(config)
        
        return f'''
<div class="{class_str}" style="height:{self.height};width:{self.width}">
    <canvas id="chart-{chart_id}" data-pynext-chart></canvas>
</div>
<script>
    (function() {{
        var config = {config_json};
        var canvas = document.getElementById('chart-{chart_id}');
        
        // Wait for Chart.js to load
        function initChart() {{
            if (typeof Chart === 'undefined') {{
                setTimeout(initChart, 100);
                return;
            }}
            
            // Apply dark mode detection
            var isDark = document.documentElement.classList.contains('dark');
            if (isDark) {{
                Chart.defaults.color = 'hsl(210, 40%, 80%)';
                Chart.defaults.borderColor = 'hsl(217, 33%, 25%)';
            }}
            
            new Chart(canvas, config);
        }}
        
        initChart();
    }})();
</script>
'''
    
    def __str__(self) -> str:
        return self.render()


class LineChart:
    """
    Simplified line chart component.
    
    Attributes:
        data: List of data points or dict with x/y keys
        x: Key for x-axis values (if data is list of dicts)
        y: Key(s) for y-axis values
        title: Chart title
        labels: Override x-axis labels
        colors: Override series colors
        smooth: Use curved lines (tension)
        fill: Fill area under line
        class_: Additional CSS classes
    
    Example:
        LineChart(
            data=[
                {"month": "Jan", "sales": 100, "target": 90},
                {"month": "Feb", "sales": 120, "target": 100},
            ],
            x="month",
            y=["sales", "target"],
            title="Sales vs Target"
        )
    """
    
    def __init__(
        self,
        data: Union[List[Dict], Dict],
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        title: Optional[str] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        smooth: bool = True,
        fill: bool = False,
        height: str = "300px",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.data = data
        self.x = x
        self.y = y if isinstance(y, list) else [y] if y else []
        self.title = title
        self.labels = labels
        self.colors = colors or FALLBACK_COLORS
        self.smooth = smooth
        self.fill = fill
        self.height = height
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        # Build Chart.js config from simplified API
        chart_data = self._build_chart_data()
        
        options = {}
        if self.title:
            options["plugins"] = {
                "title": {"display": True, "text": self.title}
            }
        
        chart = Chart(
            type="line",
            data=chart_data,
            options=options,
            height=self.height,
            class_=self.extra_class,
        )
        
        return chart.render()
    
    def _build_chart_data(self) -> Dict:
        """Convert simplified data to Chart.js format."""
        if isinstance(self.data, dict):
            return self.data
        
        # Extract labels from x key
        labels = self.labels or [item.get(self.x, "") for item in self.data]
        
        # Build datasets
        datasets = []
        for i, y_key in enumerate(self.y):
            color = self.colors[i % len(self.colors)]
            datasets.append({
                "label": y_key,
                "data": [item.get(y_key, 0) for item in self.data],
                "borderColor": color,
                "backgroundColor": f"{color}33",  # 20% opacity
                "tension": 0.4 if self.smooth else 0,
                "fill": self.fill,
            })
        
        return {"labels": labels, "datasets": datasets}
    
    def __str__(self) -> str:
        return self.render()


class BarChart:
    """
    Simplified bar chart component.
    
    Example:
        BarChart(
            data=sales_by_region,
            x="region",
            y="total",
            title="Sales by Region"
        )
    """
    
    def __init__(
        self,
        data: Union[List[Dict], Dict],
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        title: Optional[str] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        horizontal: bool = False,
        stacked: bool = False,
        height: str = "300px",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.data = data
        self.x = x
        self.y = y if isinstance(y, list) else [y] if y else []
        self.title = title
        self.labels = labels
        self.colors = colors or FALLBACK_COLORS
        self.horizontal = horizontal
        self.stacked = stacked
        self.height = height
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        chart_data = self._build_chart_data()
        
        options = {}
        if self.title:
            options["plugins"] = {
                "title": {"display": True, "text": self.title}
            }
        if self.stacked:
            options["scales"] = {
                "x": {"stacked": True},
                "y": {"stacked": True}
            }
        if self.horizontal:
            options["indexAxis"] = "y"
        
        chart = Chart(
            type="bar",
            data=chart_data,
            options=options,
            height=self.height,
            class_=self.extra_class,
        )
        
        return chart.render()
    
    def _build_chart_data(self) -> Dict:
        if isinstance(self.data, dict):
            return self.data
        
        labels = self.labels or [item.get(self.x, "") for item in self.data]
        
        datasets = []
        for i, y_key in enumerate(self.y):
            color = self.colors[i % len(self.colors)]
            datasets.append({
                "label": y_key,
                "data": [item.get(y_key, 0) for item in self.data],
                "backgroundColor": color,
            })
        
        return {"labels": labels, "datasets": datasets}
    
    def __str__(self) -> str:
        return self.render()


class PieChart:
    """
    Simplified pie/donut chart component.
    
    Example:
        PieChart(
            data=distribution,
            label="category",
            value="amount",
            donut=True
        )
    """
    
    def __init__(
        self,
        data: Union[List[Dict], Dict],
        label: Optional[str] = None,
        value: Optional[str] = None,
        title: Optional[str] = None,
        colors: Optional[List[str]] = None,
        donut: bool = False,
        height: str = "300px",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.data = data
        self.label = label
        self.value = value
        self.title = title
        self.colors = colors or FALLBACK_COLORS
        self.donut = donut
        self.height = height
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        chart_data = self._build_chart_data()
        
        options = {}
        if self.title:
            options["plugins"] = {
                "title": {"display": True, "text": self.title}
            }
        
        chart = Chart(
            type="doughnut" if self.donut else "pie",
            data=chart_data,
            options=options,
            height=self.height,
            class_=self.extra_class,
        )
        
        return chart.render()
    
    def _build_chart_data(self) -> Dict:
        if isinstance(self.data, dict):
            return self.data
        
        labels = [item.get(self.label, "") for item in self.data]
        values = [item.get(self.value, 0) for item in self.data]
        
        return {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": self.colors[:len(values)],
            }]
        }
    
    def __str__(self) -> str:
        return self.render()


class AreaChart:
    """
    Line chart with filled area.
    
    Example:
        AreaChart(
            data=traffic_data,
            x="date",
            y="visitors",
            title="Website Traffic"
        )
    """
    
    def __init__(
        self,
        data: Union[List[Dict], Dict],
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        title: Optional[str] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        stacked: bool = False,
        height: str = "300px",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.data = data
        self.x = x
        self.y = y if isinstance(y, list) else [y] if y else []
        self.title = title
        self.labels = labels
        self.colors = colors or FALLBACK_COLORS
        self.stacked = stacked
        self.height = height
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        # Use LineChart with fill enabled
        line = LineChart(
            data=self.data,
            x=self.x,
            y=self.y,
            title=self.title,
            labels=self.labels,
            colors=self.colors,
            smooth=True,
            fill=True,
            height=self.height,
            class_=self.extra_class,
        )
        return line.render()
    
    def __str__(self) -> str:
        return self.render()


# CDN loader for Chart.js
def ChartJSLoader(version: str = "4.4.1") -> str:
    """
    Include Chart.js from CDN.
    Add this to your layout's <head>.
    
    Example:
        head()[
            ChartJSLoader(),
            ...
        ]
    """
    return f'<script src="https://cdn.jsdelivr.net/npm/chart.js@{version}/dist/chart.umd.min.js"></script>'


__all__ = [
    "Chart",
    "LineChart",
    "BarChart",
    "PieChart",
    "AreaChart",
    "ChartJSLoader",
]

