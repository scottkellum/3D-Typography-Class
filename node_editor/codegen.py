"""
Translates a GraphState into a valid ColdType Python source string.
Assembly is inside-out: Text → Style → Layout → Extrude → Output.
"""
from .model import GraphState, NodeInstance


def _ind(level: int, s: str) -> str:
    return "    " * level + s


def _quote(text: str) -> str:
    """Produce a Python string literal, escaping newlines."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _animated_val(easing: str, rng_min: float, rng_max: float, offset: int, var: str = "g.i") -> str:
    return f'f.adj(-{var}*{offset}).e("{easing}", 1, rng=({rng_min}, {rng_max}))'


# ---------------------------------------------------------------------------
# Per-node expression builders
# ---------------------------------------------------------------------------

def _text_expr(node: NodeInstance) -> str:
    text = node.params.get("text", "Hello")
    return _quote(text)


def _style_expr(node: NodeInstance, text_expr: str) -> str:
    font = node.params.get("font_name", "Gamay")
    size = node.params.get("size", 375.0)
    animated = node.params.get("animated", True)
    easing = node.params.get("easing", "seio")
    offset = node.params.get("offset_per_glyph", 5)
    multiline = node.params.get("multiline", True)
    multiline_arg = ",\n            multiline=1" if multiline else ""

    size_str = f"{int(size)}" if size == int(size) else str(size)

    if animated:
        wdth_min = node.params.get("wdth_min", 1.0)
        wdth_max = node.params.get("wdth_max", 0.0)
        wght_min = node.params.get("wght_min", 1.0)
        wght_max = node.params.get("wght_max", 0.0)
        wdth_val = _animated_val(easing, wdth_min, wdth_max, offset)
        wght_val = _animated_val(easing, wght_min, wght_max, offset)
        return (
            f"Glyphwise({text_expr}, lambda g:\n"
            f"            Style(\n"
            f"                '{font}',\n"
            f"                {size_str},\n"
            f"                wdth={wdth_val},\n"
            f"                wght={wght_val}){multiline_arg}\n"
            f"        )"
        )
    else:
        wdth = node.params.get("wdth_min", 1.0)
        wght = node.params.get("wght_min", 1.0)
        return f"StSt({text_expr}, '{font}', {size_str}, wdth={wdth}, wght={wght})"


def _layout_expr(node: NodeInstance, inner: str) -> str:
    xalign = node.params.get("xalign", True)
    track_amount = node.params.get("track_amount", 50)
    track_vertical = node.params.get("track_vertical", True)
    align = node.params.get("align", True)

    chain = ""
    if xalign:
        chain += "\n            .xalign(f.a.r)"
    if track_amount != 0:
        v_arg = ", v=1" if track_vertical else ""
        chain += f"\n            .track({track_amount}{v_arg})"
    if align:
        chain += "\n            .align(f.a.r)"

    return inner + chain


def _extrude_expr(node: NodeInstance, inner: str) -> str:
    animated = node.params.get("animated", True)
    easing = node.params.get("easing", "seio")
    rng_min = node.params.get("rng_min", 0.1)
    rng_max = node.params.get("rng_max", 1.75)
    offset = node.params.get("offset_per_glyph", 5)
    static_val = node.params.get("static_val", 0.5)

    if animated:
        extrude_line = f'f.adj(-i*{offset}).e("{easing}", 1, rng=({rng_min}, {rng_max}))'
    else:
        extrude_line = str(static_val)

    return (
        inner
        + "\n            .mapv(lambda i, p: p"
        + f"\n                .ch(b3d(lambda bp: bp"
        + f"\n                    .extrude({extrude_line}))))"
    )


# ---------------------------------------------------------------------------
# Top-level generator
# ---------------------------------------------------------------------------

def generate(graph: GraphState) -> str:
    output_node = graph.find_node("output")
    if output_node is None:
        return "# Add an Output node to generate code\n"

    mode = output_node.params.get("mode", "b3d")

    lines = [
        "from coldtype import *",
    ]
    if mode == "b3d":
        lines.append("from coldtype.blender import *")
    lines.append("")

    # Trace the chain from output backwards
    if mode == "b3d":
        scene_node = graph.find_upstream(output_node, "scene")
    else:
        scene_node = graph.find_upstream(output_node, "scene")

    layout_node = None
    extrude_node = None
    style_node = None
    text_node = None

    if scene_node:
        if scene_node.node_type == "extrude":
            extrude_node = scene_node
            layout_node = graph.find_upstream(extrude_node, "layout")
        elif scene_node.node_type == "layout":
            layout_node = scene_node

    if layout_node:
        style_node = graph.find_upstream(layout_node, "style")

    if style_node:
        text_node = graph.find_upstream(style_node, "text")

    # Also handle direct connections (style → output, text → output, etc.)
    if not style_node and scene_node and scene_node.node_type == "style":
        style_node = scene_node
        text_node = graph.find_upstream(style_node, "text")
    if not text_node and scene_node and scene_node.node_type == "text":
        text_node = scene_node

    # Build inner expression bottom-up
    if text_node:
        expr = _text_expr(text_node)
    else:
        expr = '"Hello"'

    if style_node:
        expr = _style_expr(style_node, expr)

    if layout_node:
        expr = _layout_expr(layout_node, expr)

    if extrude_node:
        expr = _extrude_expr(extrude_node, expr)

    # Wrap in P(...) if we have a chain
    if style_node or layout_node or extrude_node:
        expr = f"P(\n        {expr})"
    else:
        expr = f"P(\n        {expr})"

    # Build decorators + function
    if mode == "b3d":
        timeline = output_node.params.get("timeline", 60)
        cx = output_node.params.get("center_x", 0)
        cy = output_node.params.get("center_y", 1)
        upright = output_node.params.get("upright", 1)

        lines += [
            "@b3d_runnable(playback=B3DPlayback.KeepPlaying)",
            "def prerun(bw:BpyWorld):",
            "    bw.delete_previous(materials=False)",
            "",
            f"@b3d_animation(timeline={timeline}, center=({cx}, {cy}), upright={upright})",
            "def render(f):",
            f"    return ({expr})",
        ]
    else:
        timeline = output_node.params.get("timeline", 60)
        bg_r = output_node.params.get("bg_r", 0)
        bg_g = output_node.params.get("bg_g", 0)
        bg_b = output_node.params.get("bg_b", 0)
        bg_str = f"hsl({bg_r}, {bg_g}, {bg_b})"

        lines += [
            f"@animation(timeline={timeline}, bg=\"{bg_str}\")",
            "def render(f):",
            f"    return ({expr})",
        ]

    return "\n".join(lines) + "\n"
