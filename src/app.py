
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from amm import get_amount_out, get_swap_details
from reader import get_reserves

# // theme ///
BG       = "#0E1117"
SURFACE  = "#1C2333"
BORDER   = "#2D3547"
TEXT     = "#FAFAFA"
SUBTEXT  = "#8B8FA8"
ACCENT   = "#FF4B4B"
GREEN    = "#21C354"

try:
    _reserves = get_reserves()
    _default_weth = _reserves["weth"]
    _default_usdc = _reserves["usdc"]
except Exception:
    _default_weth = 4781
    _default_usdc = 8577724

# ///helpers ///

def metric_card(label: str, value: str, delta: str = "", delta_color: str = GREEN) -> html.Div:
    """This renders a metric card."""
    children = [
        html.P(label, style={"color": SUBTEXT, "fontSize": "12px", "margin": "0 0 4px"}),
        html.H3(value, style={"color": TEXT, "margin": "0", "fontSize": "22px", "fontWeight": "600"}),
    ]
    if delta:
        children.append(html.P(delta, style={"color": delta_color, "fontSize": "12px", "margin": "4px 0 0"}))
    return html.Div(children, style={
        "background": SURFACE,
        "border": f"1px solid {BORDER}",
        "borderRadius": "8px",
        "padding": "16px 20px",
        "flex": "1",
    })


def slider_section(label: str, slider: dcc.Slider) -> html.Div:
    """Wrap a slider with a styled label inside the controls panel.

    Args:
        label:  Text label displayed above the slider.
        slider: A configured dcc.Slider component.

    Returns:
        A styled html.Div with label + slider.
    """
    return html.Div([
        html.P(label, style={"color": SUBTEXT, "fontSize": "13px", "fontWeight": "500", "margin": "0 0 8px"}),
        slider,
    ], style={"marginBottom": "28px"})


# /// layout ///

app = dash.Dash(__name__, title="AMM Calculator")
# Flask WSGI 
server = app.server

app.layout = html.Div([

    html.Div([
        html.H1("AMM Calculator", style={"margin": "0", "fontSize": "28px", "fontWeight": "700"}),
        html.P("Uniswap V2 · WETH / USDC · Ethereum Mainnet",
            style={"color": SUBTEXT, "margin": "4px 0 0", "fontSize": "14px"}),
    ], style={"marginBottom": "32px"}),

    html.Div([
        slider_section("Amount In (ETH)", dcc.Slider(
            min=1, max=int(_default_weth * 0.8), step=1,
            value=int(_default_weth * 0.1), id="amount-in", marks={},
            tooltip={"placement": "bottom", "always_visible": False},
        )),
        slider_section("Reserve WETH", dcc.Slider(
            min=100, max=50000, step=100, value=_default_weth, id="reserve-in",
            marks={100: "100", 10000: "10K", 20000: "20K", 30000: "30K", 40000: "40K", 50000: "50K"},
            tooltip={"placement": "bottom", "always_visible": False},
        )),
        slider_section("Reserve USDC", dcc.Slider(
            min=100000, max=100000000, step=100000, value=_default_usdc, id="reserve-out",
            marks={100000: "100K", 25000000: "25M", 50000000: "50M", 75000000: "75M", 100000000: "100M"},
            tooltip={"placement": "bottom", "always_visible": False},
        )),
    ], style={
        "background": SURFACE,
        "border": f"1px solid {BORDER}",
        "borderRadius": "8px",
        "padding": "24px",
        "marginBottom": "24px",
    }),

    # metric cards row
    html.Div(id="metric-cards", style={"display": "flex", "gap": "16px", "marginBottom": "24px"}),

    # new-k info bar
    html.Div(id="k-bar", style={
        "background": SURFACE,
        "border": f"1px solid {BORDER}",
        "borderRadius": "8px",
        "padding": "12px 20px",
        "fontSize": "13px",
        "color": SUBTEXT,
        "marginBottom": "24px",
    }),

    # chart
    dcc.Graph(id="price-impact-graph", config={"displayModeBar": False}),

], style={"maxWidth": "1000px", "margin": "0 auto", "padding": "40px 24px", "backgroundColor": BG})


# /// callbacks ///

@app.callback(
    Output("amount-in", "max"),
    Output("amount-in", "marks"),
    Input("reserve-in", "value"),
)
def sync_amount_slider(reserve_in: float):
    """Rescale the amount-in slider to 80% of reserve_in so the hyperbola bend is always visible.

    Args:
        reserve_in: Current value of the reserve-in slider.

    Returns:
        Tuple of (new max, new marks dict) for the amount-in slider.
    """
    max_val = int(reserve_in * 0.8)
    step = max(1, max_val // 4)
    marks = {i: str(i) for i in range(step, max_val + 1, step)}
    return max_val, marks


@app.callback(
    Output("metric-cards", "children"),
    Output("k-bar", "children"),
    Output("price-impact-graph", "figure"),
    Input("amount-in", "value"),
    Input("reserve-in", "value"),
    Input("reserve-out", "value"),
)
def update(amount_in: float, reserve_in: float, reserve_out: float):
    """Recompute all outputs whenever any slider moves.

    Builds metric cards, the k info bar, and the effective-price chart
    from the raw values returned by get_swap_details.

    Args:
        amount_in:   ETH amount to swap (from slider).
        reserve_in:  WETH pool reserve (from slider).
        reserve_out: USDC pool reserve (from slider).

    Returns:
        Tuple of (metric cards list, k bar string, plotly figure).
    """
    if amount_in is None:
        amount_in = int(_default_weth * 0.1)
    if reserve_in is None:
        reserve_in = _default_weth
    if reserve_out is None:
        reserve_out = _default_usdc

    market_price, amount_out, effective_price, price_impact, \
        new_reserve_in, new_reserve_out, new_k = get_swap_details(amount_in, reserve_in, reserve_out)

    old_k = reserve_in * reserve_out
    k_growth = (new_k - old_k) / old_k * 100

    cards = [
        metric_card("Market Price",    f"${market_price:,.2f}",   "USDC / ETH"),
        metric_card("Amount Out",      f"{amount_out:,.2f}",       "USDC received"),
        metric_card("Effective Price", f"${effective_price:,.2f}", "USDC / ETH"),
        metric_card("Price Impact",    f"{price_impact:.4f}%",
                    "low" if price_impact < 1 else "high ⚠",
                    GREEN if price_impact < 1 else ACCENT),
    ]

    k_bar = (
        f"k before swap: {old_k:,.0f}  →  "
        f"k after swap: {new_k:,.0f}  "
        f"(+{k_growth:.6f}% — LP fee accumulated)"
    )

    x_max = reserve_in * 0.8
    n = 100
    xs = [1 + (x_max - 1) * i / (n - 1) for i in range(n)]
    effective_prices = [get_amount_out(x, reserve_in, reserve_out) / x for x in xs]
    market_line = [market_price] * n

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=market_line, mode="lines", name="Market Price",
        line=dict(dash="dot", color=SUBTEXT, width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=effective_prices, mode="lines", name="Effective Price",
        line=dict(color=ACCENT, width=2.5),
        fill="tonexty", fillcolor="rgba(255,75,75,0.08)",
    ))
    fig.add_vline(
        x=amount_in, line_dash="dash", line_color=GREEN, line_width=1.5,
        annotation_text=f"{amount_in} ETH",
        annotation_font_color=GREEN,
        annotation_font_size=12,
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=SURFACE,
        font=dict(family="Inter, sans-serif", color=TEXT),
        title=dict(text="Effective Price vs Market Price", font=dict(size=15)),
        xaxis=dict(title="Amount In (ETH)", range=[1, x_max], gridcolor=BORDER, showgrid=True),
        yaxis=dict(title="Price (USDC / ETH)", gridcolor=BORDER, showgrid=True),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER),
        margin=dict(t=50, b=40, l=60, r=20),
        hovermode="x unified",
    )

    return cards, k_bar, fig