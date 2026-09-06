"""Shared visual identity for all benchmark figures."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Okabe-Ito colorblind-safe palette subset
COLOR_INTERIOR = "#0072B2"  # blue      -- nodes 1,2,3 (I)
COLOR_BOUNDARY = "#E69F00"  # orange    -- nodes 4,5   (B)
COLOR_EXTERIOR = "#009E73"  # bluish green -- nodes 6,7,8 (E)
COLOR_EDGE = "#555555"
COLOR_ACCENT = "#D55E00"    # vermillion, for highlighting (e.g. leakage edge, frontier)
COLOR_ACCENT2 = "#CC79A7"   # reddish purple, secondary highlight

NODE_COLOR = {
    1: COLOR_INTERIOR, 2: COLOR_INTERIOR, 3: COLOR_INTERIOR,
    4: COLOR_BOUNDARY, 5: COLOR_BOUNDARY,
    6: COLOR_EXTERIOR, 7: COLOR_EXTERIOR, 8: COLOR_EXTERIOR,
}

# Fixed 2D layout, identical across all graph-diagram panels
NODE_POS = {
    1: (-2.0, 1.0), 2: (-2.0, 0.0), 3: (-2.0, -1.0),
    4: (0.0, 0.55), 5: (0.0, -0.55),
    6: (2.0, 1.0), 7: (2.0, 0.0), 8: (2.0, -1.0),
}

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "svg.fonttype": "none",
})


def save_all(fig, path_noext):
    fig.savefig(path_noext + ".png", bbox_inches="tight")
    fig.savefig(path_noext + ".pdf", bbox_inches="tight")
    fig.savefig(path_noext + ".svg", bbox_inches="tight")


def draw_graph(ax, edges, node_color=NODE_COLOR, pos=NODE_POS, highlight_edges=None,
               node_labels=True, title=None):
    """edges: list of (a,b,weight). highlight_edges: set of frozenset({a,b}) to draw in accent color."""
    highlight_edges = highlight_edges or set()
    max_w = max((w for _, _, w in edges), default=1.0)
    for a, b, w in edges:
        is_hi = frozenset((a, b)) in highlight_edges
        color = COLOR_ACCENT if is_hi else COLOR_EDGE
        lw = 0.8 + 3.2 * (w / max_w)
        alpha = 0.95 if is_hi else 0.55
        xa, ya = pos[a]; xb, yb = pos[b]
        ax.plot([xa, xb], [ya, yb], color=color, linewidth=lw, alpha=alpha, zorder=1,
                linestyle="-" if not is_hi else "--")
    for n, (x, y) in pos.items():
        ax.scatter([x], [y], s=650, color=node_color[n], edgecolor="black", linewidth=1.0, zorder=2)
        if node_labels:
            ax.text(x, y, str(n), ha="center", va="center", zorder=3, fontsize=11,
                    color="white" if node_color[n] != COLOR_BOUNDARY else "black", fontweight="bold")
    ax.set_xlim(-2.8, 2.8)
    ax.set_ylim(-1.7, 1.7)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=11)
