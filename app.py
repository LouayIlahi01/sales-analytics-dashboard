"""Sales Analytics Dashboard - Python Dash + Plotly (dark theme)."""
from functools import lru_cache

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

DATA_PATH = "data/sales_data.csv"

PURPLE, SOFT, LIME, MUTED, LINE = "#7c4dff", "#b9a4ff", "#c8f03c", "#8a8a96", "#1f1f27"
FONT = "Plus Jakarta Sans, Segoe UI, sans-serif"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HEAT = ["#1a1530", "#35267a", "#5b36c9", "#8c6bff", "#c4b3ff"]  # low -> high; also used by the legend
CATEGORY_COLORS = {"Electronics": LIME, "Clothing": SOFT, "Books": "#5ad7ff", "Home & Living": "#ff9f6b"}


# ---------- Data ----------
@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Read and prepare the data once; later calls hit the cache."""
    df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Quarter"] = "Q" + df["Date"].dt.quarter.astype(str)
    df["Weekday"] = df["Date"].dt.dayofweek
    return df


def filter_data(df, categories, regions, quarter):
    mask = pd.Series(True, index=df.index)
    if categories:
        mask &= df["Category"].isin(categories)
    if regions:
        mask &= df["Region"].isin(regions)
    if quarter and quarter != "All":
        mask &= df["Quarter"] == quarter
    return df[mask]


def monthly_totals(d):
    return d.groupby("Month", as_index=False).agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum"),
        Orders=("Orders", "sum"), Customers=("Customer_ID", "nunique"))


def month_over_month(series):
    """% change of the last month vs the one before, or None if it can't be computed."""
    if len(series) >= 2 and series.iloc[-2] != 0:
        return (series.iloc[-1] / series.iloc[-2] - 1) * 100
    return None


# ---------- Figures ----------
def style_fig(fig, height):
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=MUTED, size=11),
        hoverlabel=dict(bgcolor="#000", font_family=FONT, bordercolor=LINE),
    )
    return fig


def trend_fig(monthly):
    fig = go.Figure()
    fig.add_scatter(x=monthly["Month"], y=monthly["Sales"], name="Sales", mode="lines",
                    line=dict(color=LIME, width=2.5, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(200,240,60,0.07)")
    fig.add_scatter(x=monthly["Month"], y=monthly["Profit"], name="Profit", mode="lines",
                    line=dict(color=MUTED, width=2, dash="dot", shape="spline"))

    if len(monthly) > 1:  # mark the best month, like a pinned tooltip
        best = monthly.loc[monthly["Sales"].idxmax()]
        on_right = monthly["Month"].tolist().index(best["Month"]) > len(monthly) / 2
        for y, color in ((best["Sales"], LIME), (best["Profit"], MUTED)):
            fig.add_scatter(x=[best["Month"]], y=[y], mode="markers", showlegend=False, hoverinfo="skip",
                            marker=dict(size=9, color="#0c0c10", line=dict(color=color, width=2)))
            fig.add_annotation(x=best["Month"], y=y, text=f"${y:,.0f}", showarrow=False,
                               xanchor="right" if on_right else "left", xshift=-12 if on_right else 12,
                               font=dict(size=11, color="#f4f4f7"), bgcolor="#000",
                               bordercolor=LINE, borderpad=4)

    fig.update_xaxes(tickformat="%b", showgrid=False, linecolor=LINE)
    if len(monthly) <= 6:  # few months: one tick per month instead of repeated half-month labels
        fig.update_xaxes(tickvals=monthly["Month"])
    fig.update_yaxes(gridcolor="#17171d", zeroline=False, tickformat="~s")
    fig.update_layout(showlegend=False, hovermode="x unified")
    style_fig(fig, 280)
    fig.update_layout(margin=dict(l=0, r=18, t=8, b=0))  # room for the last month label
    return fig


def heatmap_fig(d):
    if d.empty:
        return style_fig(go.Figure(), 300)
    grid = (d.groupby([d["Month"].dt.month, d["Weekday"]])["Sales"].sum()
              .unstack(fill_value=0).reindex(columns=range(7), fill_value=0))
    month_labels = [pd.Timestamp(2025, m, 1).strftime("%b") for m in grid.index]
    stops = [[i / (len(HEAT) - 1), c] for i, c in enumerate(HEAT)]
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=WEEKDAYS, y=month_labels, xgap=3, ygap=3, showscale=False,
        colorscale=stops, hovertemplate="%{y}, %{x}: %{z:$,.0f}<extra></extra>"))
    fig.update_xaxes(side="top", showgrid=False, ticks="")
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    return style_fig(fig, 300)


# ---------- Text and small components ----------
def build_insights(d, monthly):
    if d.empty:
        return [html.Span("No data for these filters", className="chip")]
    best_cat = d.groupby("Category")["Sales"].sum().idxmax()
    margin = d["Profit"].sum() / d["Sales"].sum() * 100
    return [
        html.Span(f"Top category: {best_cat}", className="chip"),
        html.Span(f"Margin: {margin:.1f}%", className="chip"),
        html.Span(f"Best month: {monthly.loc[monthly['Sales'].idxmax(), 'Month']:%B}", className="chip"),
    ]


def delta_tag(g):
    if g is None:
        return html.Span(className="delta flat")
    return html.Span(f"{g:+.1f}% vs last month", className="delta up" if g >= 0 else "delta down")


def bars(monthly, column, fmt, average_tag=False):
    """Monthly bar sparkline with a dashed average line (plain HTML/CSS, hover shows the value)."""
    if monthly.empty:
        return html.Div(className="bars")
    values = monthly[column].tolist()
    top = max(values) or 1
    average = sum(values) / len(values)
    items = [html.Div(className="bar on" if i == len(values) - 1 else "bar",
                      style={"height": f"{v / top * 100:.1f}%"},
                      title=f"{m:%B}: {fmt(v)}")
             for i, (m, v) in enumerate(zip(monthly["Month"], values))]
    items.append(html.Div(html.Span("Average", className="avg-tag") if average_tag else None,
                          className="avg", style={"bottom": f"{average / top * 100:.1f}%"}))
    return html.Div(items, className="bars")


def kpi_column(label, value, monthly, column, fmt):
    return [html.Span(label, className="label"),
            html.Div(value, className="value"),
            delta_tag(month_over_month(monthly[column])),
            bars(monthly, column, fmt)]


def product_rows(d):
    top = d.groupby(["Product", "Category"], as_index=False)["Sales"].sum().nlargest(5, "Sales")
    return [
        html.Div([
            html.Div(r.Product, className="row-title"),
            html.Span([html.Span(className="tag-dot",
                                 style={"background": CATEGORY_COLORS.get(r.Category, MUTED)}),
                       r.Category], className="tag"),
            html.Div(f"${r.Sales:,.0f}", className="row-amount"),
        ], className="row")
        for r in top.itertuples()
    ]


def compute(categories, regions, quarter):
    """All dashboard numbers and figures for the current filters."""
    d = filter_data(load_data(), categories, regions, quarter)
    monthly = monthly_totals(d)

    whole, cents = f"{d['Sales'].sum():,.2f}".split(".")
    revenue = [
        html.Span("Total revenue", className="label"),
        html.Div([html.Span([f"${whole}", html.Span(f".{cents}", className="dim")], className="big"),
                  delta_tag(month_over_month(monthly["Sales"]))], className="big-row"),
        html.Div(build_insights(d, monthly), className="chips"),
        bars(monthly, "Sales", lambda v: f"${v:,.0f}", average_tag=True),
    ]
    span = ([html.Span(f"{monthly['Month'].iloc[0]:%B %Y}"), html.Span(f"{monthly['Month'].iloc[-1]:%B %Y}")]
            if not monthly.empty else [])

    return (revenue,
            kpi_column("Orders", f"{d['Orders'].sum():,}", monthly, "Orders", lambda v: f"{v:,.0f}"),
            kpi_column("Profit", f"${d['Profit'].sum():,.0f}", monthly, "Profit", lambda v: f"${v:,.0f}"),
            kpi_column("Customers", f"{d['Customer_ID'].nunique():,}", monthly, "Customers", lambda v: f"{v:,.0f}"),
            span, trend_fig(monthly), heatmap_fig(d), product_rows(d))


# ---------- Layout ----------
def choice(component, kind, **kw):
    """Radio/checklist styled as pills ('pill') or as a segmented control ('seg')."""
    return component(inline=True, class_name=f"{kind}s", input_class_name="pill-input",
                     label_class_name=kind, label_checked_class_name=f"{kind}-on", **kw)


def card(title, subtitle, body):
    return html.Section([
        html.Div([html.H3(title, className="card-title"), html.Span(subtitle, className="label")],
                 className="card-head"),
        body,
    ], className="card")


def legend(*items):
    return html.Div([html.Span([html.Span(className=f"sw {cls}"), name]) for name, cls in items], className="legend")


df = load_data()
GRAPH_CFG = {"displayModeBar": False}

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Sales Analytics Dashboard"
server = app.server  # for deployment (gunicorn app:server)

app.layout = html.Div([
    html.Header([
        html.Div([html.Div(className="logo"), html.Span("Sales Analytics")], className="brand"),
        html.Div(choice(dbc.Checklist, "pill", id="category", value=[],
                        options=sorted(df["Category"].unique())), className="nav"),
        html.Div(choice(dbc.Checklist, "pill", id="region", value=[],
                        options=sorted(df["Region"].unique())), className="nav"),
    ], className="topbar"),

    html.Div([
        html.H1([html.Span("Sales"), html.Span(" overview", className="dim")], className="title"),
        choice(dbc.RadioItems, "seg", id="quarter", value="All",
               options=[{"label": "All year", "value": "All"}] +
                       [{"label": q, "value": q} for q in ("Q1", "Q2", "Q3", "Q4")]),
    ], className="heading"),

    html.Section([
        html.Div(id="revenue", className="rev"),
        html.Div(id="col-orders", className="col"),
        html.Div(id="col-profit", className="col"),
        html.Div(id="col-customers", className="col"),
    ], className="strip"),
    html.Div(id="span", className="span"),

    html.Div([
        card("Sales vs profit", "By month", html.Div([
            legend(("Sales", "lime"), ("Profit", "mute")),
            dcc.Graph(id="trend", config=GRAPH_CFG)])),
        card("Activity", "Sales by weekday", html.Div([
            dcc.Graph(id="heatmap", config=GRAPH_CFG),
            html.Div([html.Span("Less")] + [html.I(style={"background": c}) for c in HEAT] +
                     [html.Span("More")], className="heat-legend")])),
        card("Top products", "By sales", html.Div(id="top-products", className="rows")),
    ], className="grid"),

    html.P("Demo data is synthetic. Pick categories or regions to filter; none selected shows all.",
           className="footnote"),
], className="app")


@app.callback(
    Output("revenue", "children"), Output("col-orders", "children"),
    Output("col-profit", "children"), Output("col-customers", "children"),
    Output("span", "children"), Output("trend", "figure"),
    Output("heatmap", "figure"), Output("top-products", "children"),
    Input("category", "value"), Input("region", "value"), Input("quarter", "value"),
)
def update(categories, regions, quarter):
    return compute(categories, regions, quarter)


if __name__ == "__main__":
    app.run(debug=True)
