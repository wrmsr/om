"""
A tiny, dependency-free SVG dashboard renderer.

The rendering layer is intentionally generic: callers construct explicit ``BarChartSpec`` and ``DashboardSpec`` objects.
The benchmark code at the bottom is merely the first concrete use case and may be replaced without changing the
renderer.

Current scope:
    * standalone SVG output
    * dashboards arranged on an explicit equal-sized grid
    * grouped, non-negative vertical bar charts
    * linear axes with pleasant tick spacing
    * legends, tooltips, and automatic category-label rotation

Run this file directly to write:
    client_benchmarks.svg server_benchmarks.svg
"""
import contextlib
import dataclasses as dc
import html
import math
import pathlib
import typing as ta


type Number = int | float


##
# Generic chart model


@dc.dataclass(frozen=True)
class Theme:
    page_background: str = '#f4f7fb'
    panel_background: str = '#ffffff'
    panel_border: str = '#d8e0ea'
    header_background: str = '#17324d'
    header_foreground: str = '#ffffff'
    subtitle_background: str = '#eaf0f6'
    subtitle_foreground: str = '#41556a'
    title: str = '#172b3f'
    text: str = '#41556a'
    muted_text: str = '#66788a'
    grid: str = '#e7edf3'
    axis: str = '#aebbc8'
    series_colors: tuple[str, ...] = (
        '#3978a8',
        '#d28b36',
        '#4f9865',
        '#9a66ad',
        '#c85858',
        '#4d9ca8',
    )
    font_family: str = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


@dc.dataclass(frozen=True)
class BarSeries:
    name: str
    values: tuple[float | None, ...]
    color: str | None = None


@dc.dataclass(frozen=True)
class BarChartSpec:
    title: str
    categories: tuple[str, ...]
    series: tuple[BarSeries, ...]
    y_title: str

    show_legend: bool = True
    tick_count: int = 5
    y_max: float | None = None
    value_format: str = ',.1f'
    tick_format: str | None = None
    tooltip_unit: str = ''

    def __post_init__(self) -> None:
        if not self.categories:
            raise ValueError('a bar chart needs at least one category')
        if not self.series:
            raise ValueError('a bar chart needs at least one series')
        if self.tick_count < 2:
            raise ValueError('tick_count must be at least 2')
        if self.y_max is not None and self.y_max <= 0:
            raise ValueError('y_max must be positive')

        size = len(self.categories)
        for series in self.series:
            if len(series.values) != size:
                raise ValueError(
                    f'series {series.name!r} has {len(series.values)} values; '
                    f'expected {size}',
                )
            for value in series.values:
                if value is not None and (not math.isfinite(value) or value < 0):
                    raise ValueError(
                        'this small renderer currently supports only finite, '
                        'non-negative bar values',
                    )


@dc.dataclass(frozen=True)
class PlacedChart:
    chart: BarChartSpec
    row: int
    column: int
    row_span: int = 1
    column_span: int = 1

    def __post_init__(self) -> None:
        if self.row < 0 or self.column < 0:
            raise ValueError('row and column must be non-negative')
        if self.row_span < 1 or self.column_span < 1:
            raise ValueError('row_span and column_span must be positive')


@dc.dataclass(frozen=True)
class DashboardSpec:
    title: str
    subtitle: str
    columns: int
    rows: int
    charts: tuple[PlacedChart, ...]

    width: float = 1600
    outer_padding: float = 36
    column_gap: float = 24
    row_gap: float = 24
    header_height: float = 78
    subtitle_height: float = 44
    panel_height: float = 320

    def __post_init__(self) -> None:
        if self.columns < 1 or self.rows < 1:
            raise ValueError('dashboard grid must have at least one row and column')
        if self.width <= 0 or self.panel_height <= 0:
            raise ValueError('dashboard dimensions must be positive')

        occupied: set[tuple[int, int]] = set()
        for placed in self.charts:
            if placed.row + placed.row_span > self.rows:
                raise ValueError(f'chart {placed.chart.title!r} exceeds dashboard rows')
            if placed.column + placed.column_span > self.columns:
                raise ValueError(f'chart {placed.chart.title!r} exceeds dashboard columns')
            for row in range(placed.row, placed.row + placed.row_span):
                for column in range(placed.column, placed.column + placed.column_span):
                    cell = (row, column)
                    if cell in occupied:
                        raise ValueError(f'dashboard charts overlap at cell {cell}')
                    occupied.add(cell)

    @property
    def height(self) -> float:
        return (
            self.outer_padding * 2
            + self.header_height
            + self.subtitle_height
            + self.rows * self.panel_height
            + (self.rows - 1) * self.row_gap
        )


##
# Minimal SVG construction


def _svg_number(value: Number) -> str:
    number = float(value)
    if number == 0:
        return '0'
    rendered = f'{number:.4f}'.rstrip('0').rstrip('.')
    return rendered


def _attribute_name(name: str) -> str:
    aliases = {
        'class_': 'class',
        'font_size': 'font-size',
        'font_weight': 'font-weight',
        'text_anchor': 'text-anchor',
        'dominant_baseline': 'dominant-baseline',
        'stroke_width': 'stroke-width',
        'stroke_linecap': 'stroke-linecap',
        'stroke_dasharray': 'stroke-dasharray',
        'aria_labelledby': 'aria-labelledby',
    }
    return aliases.get(name, name.replace('_', '-'))


def _attribute_value(value: object) -> str:
    if isinstance(value, (int, float)):
        return _svg_number(value)
    return str(value)


class SvgWriter:
    def __init__(self) -> None:
        self._parts: list[str] = []
        self._indent = 0

    def _line(self, value: str) -> None:
        self._parts.append('  ' * self._indent + value)

    @staticmethod
    def _attributes(attributes: dict[str, object | None]) -> str:
        rendered: list[str] = []
        for name, value in attributes.items():
            if value is None:
                continue
            key = html.escape(_attribute_name(name), quote=True)
            val = html.escape(_attribute_value(value), quote=True)
            rendered.append(f'{key}="{val}"')
        return (' ' + ' '.join(rendered)) if rendered else ''

    @contextlib.contextmanager
    def element(self, name: str, **attributes: object | None) -> ta.Iterator[None]:
        self._line(f'<{name}{self._attributes(attributes)}>')
        self._indent += 1
        try:
            yield
        finally:
            self._indent -= 1
            self._line(f'</{name}>')

    def empty(self, name: str, **attributes: object | None) -> None:
        self._line(f'<{name}{self._attributes(attributes)} />')

    def text(self, value: str, **attributes: object | None) -> None:
        escaped = html.escape(value)
        self._line(f'<text{self._attributes(attributes)}>{escaped}</text>')

    def raw(self, value: str) -> None:
        for line in value.splitlines():
            self._line(line)

    def finish(self) -> str:
        return '\n'.join(self._parts) + '\n'


##
# Generic grouped-bar rendering


@dc.dataclass(frozen=True)
class _Scale:
    maximum: float
    step: float
    ticks: tuple[float, ...]


def _nice_number(value: float, *, rounded: bool) -> float:
    if value <= 0:
        return 1.0

    exponent = math.floor(math.log10(value))
    fraction = value / (10**exponent)

    if rounded:
        if fraction < 1.5:
            nice_fraction = 1.0
        elif fraction < 2.25:
            nice_fraction = 2.0
        elif fraction < 3.5:
            nice_fraction = 2.5
        elif fraction < 7.5:
            nice_fraction = 5.0
        else:
            nice_fraction = 10.0
    else:
        if fraction <= 1.0:
            nice_fraction = 1.0
        elif fraction <= 2.0:
            nice_fraction = 2.0
        elif fraction <= 2.5:
            nice_fraction = 2.5
        elif fraction <= 5.0:
            nice_fraction = 5.0
        else:
            nice_fraction = 10.0

    return nice_fraction * (10**exponent)


def _scale_for(maximum: float, target_ticks: int, forced_maximum: float | None) -> _Scale:
    if forced_maximum is not None:
        maximum = forced_maximum
    elif maximum <= 0:
        maximum = 1.0

    raw_step = maximum / target_ticks
    step = _nice_number(raw_step, rounded=True)
    upper = math.ceil(maximum / step) * step

    # Avoid a chart with too few intervals when rounding selected a large step.
    if upper / step < max(3, target_ticks - 1):
        step = _nice_number(raw_step, rounded=False)
        upper = math.ceil(maximum / step) * step

    interval_count = max(1, round(upper / step))
    ticks = tuple(index * step for index in range(interval_count + 1))
    return _Scale(maximum=upper, step=step, ticks=ticks)


def _estimated_text_width(text: str, font_size: float) -> float:
    # A conservative system-font approximation.  Exact font metrics would
    # require a dependency; dashboard labels only need collision avoidance.
    wide = sum(character in 'MW@%&' for character in text)
    narrow = sum(character in "ilI1.,:'|" for character in text)
    ordinary = len(text) - wide - narrow
    return font_size * (0.82 * wide + 0.28 * narrow + 0.56 * ordinary)


def _default_tick_format(step: float) -> str:
    if step >= 1:
        return ',.0f'
    if step >= 0.1:
        return ',.1f'
    if step >= 0.01:
        return ',.2f'
    return ',.3f'


def _format_number(value: float, format_spec: str) -> str:
    return format(value, format_spec)


def _series_color(series: BarSeries, index: int, theme: Theme) -> str:
    if series.color is not None:
        return series.color
    return theme.series_colors[index % len(theme.series_colors)]


def _legend_layout(
    series: ta.Sequence[BarSeries],
    colors: ta.Sequence[str],
    *,
    x: float,
    y: float,
    width: float,
    font_size: float,
) -> tuple[tuple[tuple[BarSeries, str, float, float], ...], int]:
    marker = 11.0
    item_gap = 20.0
    text_gap = 7.0
    line_height = 18.0

    entries: list[tuple[BarSeries, str, float, float]] = []
    cursor_x = x
    cursor_y = y
    rows = 1

    for item, color in zip(series, colors):
        item_width = marker + text_gap + _estimated_text_width(item.name, font_size)
        if cursor_x > x and cursor_x + item_width > x + width:
            rows += 1
            cursor_x = x
            cursor_y += line_height
        entries.append((item, color, cursor_x, cursor_y))
        cursor_x += item_width + item_gap

    return tuple(entries), rows


def _draw_bar_chart(
    svg: SvgWriter,
    spec: BarChartSpec,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    theme: Theme,
    chart_id: str,
) -> None:
    svg.empty(
        'rect',
        x=x,
        y=y,
        width=width,
        height=height,
        rx=10,
        fill=theme.panel_background,
        stroke=theme.panel_border,
    )

    title_x = x + 22
    title_y = y + 30
    svg.text(
        spec.title,
        x=title_x,
        y=title_y,
        fill=theme.title,
        font_size=16,
        font_weight=650,
    )

    colors = tuple(_series_color(series, index, theme) for index, series in enumerate(spec.series))

    legend_height = 0.0
    if spec.show_legend:
        entries, legend_rows = _legend_layout(
            spec.series,
            colors,
            x=x + 22,
            y=y + 52,
            width=width - 44,
            font_size=11,
        )
        legend_height = legend_rows * 18.0 + 6.0
        for series, color, entry_x, entry_y in entries:
            svg.empty(
                'rect',
                x=entry_x,
                y=entry_y - 9,
                width=11,
                height=11,
                rx=2,
                fill=color,
            )
            svg.text(
                series.name,
                x=entry_x + 18,
                y=entry_y,
                fill=theme.muted_text,
                font_size=11,
            )

    plot_left = x + 70
    plot_right = x + width - 22
    plot_top = y + 54 + legend_height

    category_font_size = 11.0
    category_slot = (plot_right - plot_left) / len(spec.categories)
    longest_label = max(_estimated_text_width(category, category_font_size) for category in spec.categories)
    rotate_labels = longest_label > category_slot * 0.88
    label_height = 64.0 if rotate_labels else 42.0
    plot_bottom = y + height - label_height

    if plot_bottom - plot_top < 80:
        raise ValueError(f'chart panel is too short to render {spec.title!r}')

    plot_width = plot_right - plot_left  # noqa
    plot_height = plot_bottom - plot_top

    observed_maximum = max(
        (value for series in spec.series for value in series.values if value is not None),
        default=0.0,
    )
    scale = _scale_for(observed_maximum, spec.tick_count, spec.y_max)
    tick_format = spec.tick_format or _default_tick_format(scale.step)

    # Grid and y-axis labels.
    for tick in scale.ticks:
        tick_y = plot_bottom - (tick / scale.maximum) * plot_height
        svg.empty(
            'line',
            x1=plot_left,
            y1=tick_y,
            x2=plot_right,
            y2=tick_y,
            stroke=theme.grid,
            stroke_width=1,
        )
        svg.text(
            _format_number(tick, tick_format),
            x=plot_left - 10,
            y=tick_y,
            fill=theme.muted_text,
            font_size=10.5,
            text_anchor='end',
            dominant_baseline='middle',
        )

    svg.empty(
        'line',
        x1=plot_left,
        y1=plot_top,
        x2=plot_left,
        y2=plot_bottom,
        stroke=theme.axis,
        stroke_width=1,
    )
    svg.empty(
        'line',
        x1=plot_left,
        y1=plot_bottom,
        x2=plot_right,
        y2=plot_bottom,
        stroke=theme.axis,
        stroke_width=1,
    )

    axis_center_y = plot_top + plot_height / 2
    svg.text(
        spec.y_title,
        x=x + 18,
        y=axis_center_y,
        fill=theme.muted_text,
        font_size=10.5,
        text_anchor='middle',
        transform=f'rotate(-90 {_svg_number(x + 18)} {_svg_number(axis_center_y)})',
    )

    # Bars.
    series_count = len(spec.series)
    group_width = category_slot * 0.72
    inter_bar_gap = min(5.0, group_width * 0.06)
    available_for_bars = group_width - inter_bar_gap * (series_count - 1)
    bar_width = min(46.0, max(2.0, available_for_bars / series_count))
    actual_group_width = bar_width * series_count + inter_bar_gap * (series_count - 1)

    for category_index, category in enumerate(spec.categories):
        group_center = plot_left + category_slot * (category_index + 0.5)
        group_left = group_center - actual_group_width / 2

        for series_index, (series, color) in enumerate(zip(spec.series, colors)):
            value = series.values[category_index]
            if value is None:
                continue

            bar_height = (value / scale.maximum) * plot_height
            bar_x = group_left + series_index * (bar_width + inter_bar_gap)
            bar_y = plot_bottom - bar_height
            tooltip_value = _format_number(value, spec.value_format)
            tooltip_suffix = f' {spec.tooltip_unit}' if spec.tooltip_unit else ''

            with svg.element(
                'g',
                role='graphics-symbol',
                aria_label=f'{category}, {series.name}: {tooltip_value}{tooltip_suffix}',
            ):
                with svg.element('title'):
                    svg.raw(
                        html.escape(
                            f'{category} — {series.name}: {tooltip_value}{tooltip_suffix}',
                        ),
                    )
                svg.empty(
                    'rect',
                    x=bar_x,
                    y=bar_y,
                    width=bar_width,
                    height=max(0.8, bar_height),
                    rx=min(3.0, bar_width / 5),
                    fill=color,
                )

        label_y = plot_bottom + 19
        if rotate_labels:
            svg.text(
                category,
                x=group_center + 2,
                y=label_y,
                fill=theme.text,
                font_size=category_font_size,
                text_anchor='end',
                transform=(
                    f'rotate(-35 {_svg_number(group_center + 2)} '
                    f'{_svg_number(label_y)})'
                ),
            )
        else:
            svg.text(
                category,
                x=group_center,
                y=label_y,
                fill=theme.text,
                font_size=category_font_size,
                text_anchor='middle',
            )


def render_dashboard(spec: DashboardSpec, theme: Theme = Theme()) -> str:
    """Render a complete standalone SVG document."""

    svg = SvgWriter()
    title_id = 'dashboard-title'
    description_id = 'dashboard-description'

    svg.raw('<?xml version="1.0" encoding="UTF-8"?>')
    with svg.element(
        'svg',
        xmlns='http://www.w3.org/2000/svg',
        viewBox=f'0 0 {_svg_number(spec.width)} {_svg_number(spec.height)}',
        width=_svg_number(spec.width),
        height=_svg_number(spec.height),
        role='img',
        aria_labelledby=f'{title_id} {description_id}',
    ):
        svg.raw(
            '<style>\n'
            f'  text {{ font-family: {theme.font_family}; }}\n'
            '</style>',
        )
        svg.text(spec.title, id=title_id, x=-10000, y=-10000)
        svg.text(spec.subtitle, id=description_id, x=-10000, y=-10000)

        svg.empty(
            'rect',
            x=0,
            y=0,
            width=spec.width,
            height=spec.height,
            fill=theme.page_background,
        )

        left = spec.outer_padding
        content_width = spec.width - spec.outer_padding * 2
        header_top = spec.outer_padding
        subtitle_top = header_top + spec.header_height
        grid_top = subtitle_top + spec.subtitle_height

        svg.empty(
            'rect',
            x=left,
            y=header_top,
            width=content_width,
            height=spec.header_height,
            rx=10,
            fill=theme.header_background,
        )
        svg.text(
            spec.title,
            x=spec.width / 2,
            y=header_top + spec.header_height / 2,
            fill=theme.header_foreground,
            font_size=23,
            font_weight=700,
            text_anchor='middle',
            dominant_baseline='middle',
        )

        svg.empty(
            'rect',
            x=left,
            y=subtitle_top,
            width=content_width,
            height=spec.subtitle_height,
            fill=theme.subtitle_background,
        )
        svg.text(
            spec.subtitle,
            x=spec.width / 2,
            y=subtitle_top + spec.subtitle_height / 2,
            fill=theme.subtitle_foreground,
            font_size=12.5,
            text_anchor='middle',
            dominant_baseline='middle',
        )

        cell_width = (
            content_width - (spec.columns - 1) * spec.column_gap
        ) / spec.columns

        for index, placed in enumerate(spec.charts):
            panel_x = left + placed.column * (cell_width + spec.column_gap)
            panel_y = grid_top + placed.row * (spec.panel_height + spec.row_gap)
            panel_width = (
                cell_width * placed.column_span
                + spec.column_gap * (placed.column_span - 1)
            )
            panel_height = (
                spec.panel_height * placed.row_span
                + spec.row_gap * (placed.row_span - 1)
            )
            _draw_bar_chart(
                svg,
                placed.chart,
                x=panel_x,
                y=panel_y,
                width=panel_width,
                height=panel_height,
                theme=theme,
                chart_id=f'chart-{index}',
            )

    return svg.finish()


##
# Benchmark-specific data and chart configuration


@dc.dataclass(frozen=True)
class BenchmarkResult:
    suite: str
    implementation: str
    scenario: str
    nc: str
    requests_per_second: float
    mib_per_second: float | None
    p50_ms: float
    p99_ms: float
    rss_mib: float
    rss_delta_mib: float


BENCHMARK_RESULTS: tuple[BenchmarkResult, ...] = (
    BenchmarkResult('client', 'sync', 'requests', '1000/16', 3174, None, 4.649, 10.867, 40.3, 2.3),
    BenchmarkResult('client', 'sync', 'download', '64/16', 657.9, 657.9, 22.880, 31.974, 76.4, 17.0),
    BenchmarkResult('client', 'sync', 'upload', '64/16', 709.5, 709.5, 21.329, 25.179, 38.2, 0.1),
    BenchmarkResult('client', 'asyncio', 'requests', '1000/16', 2638, None, 5.998, 6.594, 37.5, 2.5),
    BenchmarkResult('client', 'asyncio', 'download', '64/16', 563.1, 563.1, 28.095, 28.582, 130.3, 49.8),
    BenchmarkResult('client', 'asyncio', 'upload', '64/16', 724.9, 724.9, 20.160, 26.544, 37.0, 0.9),
    BenchmarkResult('client', 'fdio', 'requests', '1000/16', 6059, None, 1.277, 3.801, 35.8, 0.9),
    BenchmarkResult('client', 'fdio', 'download', '64/16', 2630, 2630, 3.151, 6.389, 36.3, 0.8),
    BenchmarkResult('client', 'fdio', 'upload', '64/16', 691.3, 691.3, 21.690, 28.964, 36.5, 0.2),
    BenchmarkResult('client', 'urllib', 'requests', '1000/16', 9550, None, 1.547, 3.528, 56.0, 1.2),
    BenchmarkResult('client', 'urllib', 'download', '64/16', 5269, 5269, 2.672, 4.684, 83.7, 13.7),
    BenchmarkResult('client', 'urllib', 'upload', '64/16', 1048, 1048, 13.852, 23.139, 54.4, 0.4),
    BenchmarkResult('client', 'httpx', 'requests', '1000/16', 4607, None, 3.143, 7.858, 73.9, 1.2),
    BenchmarkResult('client', 'httpx', 'download', '64/16', 1474, 1474, 10.500, 14.296, 134.8, 27.2),
    BenchmarkResult('client', 'httpx', 'upload', '64/16', 977.7, 977.7, 15.993, 23.141, 92.3, 6.7),
    BenchmarkResult('server', 'sync', 'requests', '1000/16', 4669, None, 2.962, 5.830, 40.9, 2.0),
    BenchmarkResult('server', 'sync', 'download', '64/16', 2302, 2302, 1.869, 3.037, 41.1, 0.0),
    BenchmarkResult('server', 'sync', 'upload', '64/16', 1138, 1138, 9.089, 16.704, 87.1, 14.0),
    BenchmarkResult('server', 'asyncio', 'requests', '1000/16', 4939, None, 3.023, 3.468, 36.8, 1.3),
    BenchmarkResult('server', 'asyncio', 'download', '64/16', 2104, 2104, 2.955, 4.106, 37.1, 0.1),
    BenchmarkResult('server', 'asyncio', 'upload', '64/16', 1051, 1051, 9.857, 15.084, 146.6, 72.6),
    BenchmarkResult('server', 'fdio', 'requests', '1000/16', 5932, None, 2.526, 3.933, 37.4, 0.8),
    BenchmarkResult('server', 'fdio', 'download', '64/16', 2495, 2495, 1.143, 1.830, 37.7, 0.0),
    BenchmarkResult('server', 'fdio', 'upload', '64/16', 1435, 1435, 5.505, 7.595, 59.5, 11.8),
    BenchmarkResult('server', 'uvicorn', 'requests', '1000/16', 10229, None, 1.207, 2.856, 46.6, 0.6),
    BenchmarkResult('server', 'uvicorn', 'download', '64/16', 2646, 2646, 0.607, 0.969, 46.6, 0.0),
    BenchmarkResult('server', 'uvicorn', 'upload', '64/16', 2074, 2074, 2.634, 3.393, 80.6, 16.4),
)


IMPLEMENTATIONS: dict[str, tuple[str, ...]] = {
    'client': ('sync', 'asyncio', 'fdio', 'urllib', 'httpx'),
    'server': ('sync', 'asyncio', 'fdio', 'uvicorn'),
}


_FIELD_NAMES = {
    'requests_per_second',
    'mib_per_second',
    'p50_ms',
    'p99_ms',
    'rss_mib',
    'rss_delta_mib',
}


def _benchmark_index() -> dict[tuple[str, str, str], BenchmarkResult]:
    return {
        (result.suite, result.implementation, result.scenario): result
        for result in BENCHMARK_RESULTS
    }


def _benchmark_values(
    index: dict[tuple[str, str, str], BenchmarkResult],
    suite: str,
    implementations: ta.Sequence[str],
    scenario: str,
    field: str,
) -> tuple[float | None, ...]:
    if field not in _FIELD_NAMES:
        raise ValueError(f'unsupported benchmark field: {field}')
    return tuple(
        getattr(index[(suite, implementation, scenario)], field)
        for implementation in implementations
    )


def benchmark_dashboard(suite: str) -> DashboardSpec:
    implementations = IMPLEMENTATIONS[suite]
    categories = tuple(implementations)
    index = _benchmark_index()

    charts = (
        BarChartSpec(
            title='Request throughput',
            categories=categories,
            series=(
                BarSeries(
                    'requests',
                    _benchmark_values(
                        index, suite, implementations, 'requests', 'requests_per_second',
                    ),
                ),
            ),
            y_title='requests / second',
            show_legend=False,
            value_format=',.0f',
            tooltip_unit='req/s',
        ),
        BarChartSpec(
            title='Transfer throughput',
            categories=categories,
            series=(
                BarSeries(
                    'download',
                    _benchmark_values(
                        index, suite, implementations, 'download', 'mib_per_second',
                    ),
                ),
                BarSeries(
                    'upload',
                    _benchmark_values(
                        index, suite, implementations, 'upload', 'mib_per_second',
                    ),
                ),
            ),
            y_title='MiB / second',
            value_format=',.1f',
            tooltip_unit='MiB/s',
        ),
        BarChartSpec(
            title='Request latency',
            categories=categories,
            series=(
                BarSeries(
                    'p50',
                    _benchmark_values(index, suite, implementations, 'requests', 'p50_ms'),
                ),
                BarSeries(
                    'p99',
                    _benchmark_values(index, suite, implementations, 'requests', 'p99_ms'),
                ),
            ),
            y_title='milliseconds',
            value_format='.3f',
            tooltip_unit='ms',
        ),
        BarChartSpec(
            title='Transfer tail latency',
            categories=categories,
            series=(
                BarSeries(
                    'download p99',
                    _benchmark_values(index, suite, implementations, 'download', 'p99_ms'),
                ),
                BarSeries(
                    'upload p99',
                    _benchmark_values(index, suite, implementations, 'upload', 'p99_ms'),
                ),
            ),
            y_title='milliseconds',
            value_format='.3f',
            tooltip_unit='ms',
        ),
        BarChartSpec(
            title='Peak RSS',
            categories=categories,
            series=tuple(
                BarSeries(
                    scenario,
                    _benchmark_values(
                        index, suite, implementations, scenario, 'rss_mib',
                    ),
                )
                for scenario in ('requests', 'download', 'upload')
            ),
            y_title='MiB',
            value_format='.1f',
            tooltip_unit='MiB',
        ),
        BarChartSpec(
            title='Incremental RSS',
            categories=categories,
            series=tuple(
                BarSeries(
                    scenario,
                    _benchmark_values(
                        index, suite, implementations, scenario, 'rss_delta_mib',
                    ),
                )
                for scenario in ('requests', 'download', 'upload')
            ),
            y_title='MiB',
            value_format='.1f',
            tooltip_unit='MiB',
        ),
    )

    return DashboardSpec(
        title=f'{suite.title()} benchmark dashboard',
        subtitle=(
            'Higher is better for throughput; lower is better for latency and memory. '
            'Hover over a bar for its exact value.'
        ),
        columns=2,
        rows=3,
        charts=tuple(
            PlacedChart(chart=chart, row=index // 2, column=index % 2)
            for index, chart in enumerate(charts)
        ),
    )


def main() -> None:
    output_directory = pathlib.Path(__file__).resolve().parent
    for suite in ('client', 'server'):
        destination = output_directory / f'{suite}_benchmarks.svg'
        destination.write_text(
            render_dashboard(benchmark_dashboard(suite)),
            encoding='utf-8',
        )
        print(destination)


if __name__ == '__main__':
    main()
