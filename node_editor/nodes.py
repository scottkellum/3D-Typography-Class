"""
Node type definitions. Each NodeDef knows how to:
  - supply default params
  - build its Dear PyGui widgets inside an existing dpg.add_node() block
  - register its ports in the GraphState attr_map
"""
import dearpygui.dearpygui as dpg
from .model import NodeInstance, Port, GraphState


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

NODE_REGISTRY: dict[str, type["NodeDef"]] = {}


def register(cls):
    NODE_REGISTRY[cls.node_type] = cls
    return cls


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class NodeDef:
    node_type: str = ""
    label: str = ""
    color: tuple[int, int, int] = (100, 100, 100)

    @classmethod
    def default_params(cls) -> dict:
        return {}

    @classmethod
    def build(
        cls,
        node: NodeInstance,
        graph: GraphState,
        on_change,
        editor_tag: str,
    ) -> None:
        """
        Called inside a dpg.node() context manager (already created).
        Must populate node.inputs, node.outputs, node.node_id,
        and register all ports in graph.attr_map.
        `on_change` is a zero-arg callable to trigger codegen + file save.
        """
        raise NotImplementedError

    @classmethod
    def _add_input_port(cls, node: NodeInstance, graph: GraphState, name: str, data_type: str) -> int:
        port = Port(name=name, port_type="input", data_type=data_type)
        attr_id = dpg.add_node_attribute(
            label=name.replace("_", " ").title(),
            attribute_type=dpg.mvNode_Attr_Input,
        )
        port.attribute_id = attr_id
        node.inputs.append(port)
        graph.attr_map[attr_id] = (node, port)
        return attr_id

    @classmethod
    def _add_output_port(cls, node: NodeInstance, graph: GraphState, name: str, data_type: str) -> int:
        port = Port(name=name, port_type="output", data_type=data_type)
        attr_id = dpg.add_node_attribute(
            label=name.replace("_", " ").title(),
            attribute_type=dpg.mvNode_Attr_Output,
        )
        port.attribute_id = attr_id
        node.outputs.append(port)
        graph.attr_map[attr_id] = (node, port)
        return attr_id

    @classmethod
    def _add_static_attr(cls, node: NodeInstance, graph: GraphState) -> int:
        """Static attribute for embedding widgets with no port."""
        attr_id = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Static)
        return attr_id


# ---------------------------------------------------------------------------
# Output Node
# ---------------------------------------------------------------------------

@register
class OutputNodeDef(NodeDef):
    node_type = "output"
    label = "Output"
    color = (180, 80, 80)

    @classmethod
    def default_params(cls):
        return {
            "mode": "b3d",
            "timeline": 60,
            "center_x": 0.0,
            "center_y": 1.0,
            "upright": 1,
        }

    @classmethod
    def build(cls, node: NodeInstance, graph: GraphState, on_change, editor_tag: str):
        dpg.set_item_label(node.node_id, f"Output")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, parent=node.node_id) as attr_id:
            port = Port("scene", "input", "scene", attr_id)
            node.inputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Scene In", indent=4)

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_combo(
                items=["b3d", "2d"],
                default_value=node.params.get("mode", "b3d"),
                label="Mode",
                width=120,
                callback=lambda s, a: (node.params.update({"mode": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_int(
                label="Timeline",
                default_value=node.params.get("timeline", 60),
                width=120,
                callback=lambda s, a: (node.params.update({"timeline": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="Center X",
                default_value=node.params.get("center_x", 0.0),
                width=120,
                step=0.1,
                format="%.1f",
                callback=lambda s, a: (node.params.update({"center_x": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="Center Y",
                default_value=node.params.get("center_y", 1.0),
                width=120,
                step=0.1,
                format="%.1f",
                callback=lambda s, a: (node.params.update({"center_y": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_int(
                label="Upright",
                default_value=node.params.get("upright", 1),
                width=120,
                callback=lambda s, a: (node.params.update({"upright": a}), on_change()),
            )


# ---------------------------------------------------------------------------
# Text Node
# ---------------------------------------------------------------------------

@register
class TextNodeDef(NodeDef):
    node_type = "text"
    label = "Text"
    color = (80, 140, 200)

    @classmethod
    def default_params(cls):
        return {"text": "Cold\nType", "multiline": True}

    @classmethod
    def build(cls, node: NodeInstance, graph: GraphState, on_change, editor_tag: str):
        dpg.set_item_label(node.node_id, "Text")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_text(
                label="Text",
                default_value=node.params.get("text", "Cold\nType"),
                multiline=True,
                width=160,
                height=60,
                callback=lambda s, a: (node.params.update({"text": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="Multiline",
                default_value=node.params.get("multiline", True),
                callback=lambda s, a: (node.params.update({"multiline": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, parent=node.node_id) as attr_id:
            port = Port("text", "output", "text", attr_id)
            node.outputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Text Out", indent=4)


# ---------------------------------------------------------------------------
# Font Style Node
# ---------------------------------------------------------------------------

@register
class StyleNodeDef(NodeDef):
    node_type = "style"
    label = "Font Style"
    color = (80, 180, 120)

    @classmethod
    def default_params(cls):
        return {
            "font_name": "Gamay",
            "size": 375.0,
            "animated": True,
            "wdth_min": 1.0,
            "wdth_max": 0.0,
            "wght_min": 1.0,
            "wght_max": 0.0,
            "easing": "seio",
            "offset_per_glyph": 5,
            "multiline": True,
        }

    @classmethod
    def build(cls, node: NodeInstance, graph: GraphState, on_change, editor_tag: str):
        dpg.set_item_label(node.node_id, "Font Style")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, parent=node.node_id) as attr_id:
            port = Port("text", "input", "text", attr_id)
            node.inputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Text In", indent=4)

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_text(
                label="Font",
                default_value=node.params.get("font_name", "Gamay"),
                width=140,
                callback=lambda s, a: (node.params.update({"font_name": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="Size",
                default_value=node.params.get("size", 375.0),
                width=140,
                step=10.0,
                format="%.0f",
                callback=lambda s, a: (node.params.update({"size": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="Animated",
                default_value=node.params.get("animated", True),
                callback=lambda s, a: (node.params.update({"animated": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_combo(
                items=["seio", "eei", "eeio", "lin"],
                default_value=node.params.get("easing", "seio"),
                label="Easing",
                width=120,
                callback=lambda s, a: (node.params.update({"easing": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_int(
                label="Glyph Offset",
                default_value=node.params.get("offset_per_glyph", 5),
                width=120,
                callback=lambda s, a: (node.params.update({"offset_per_glyph": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_text("Width (wdth) range:")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="wdth min",
                default_value=node.params.get("wdth_min", 1.0),
                width=120, step=0.1, format="%.2f",
                callback=lambda s, a: (node.params.update({"wdth_min": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="wdth max",
                default_value=node.params.get("wdth_max", 0.0),
                width=120, step=0.1, format="%.2f",
                callback=lambda s, a: (node.params.update({"wdth_max": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_text("Weight (wght) range:")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="wght min",
                default_value=node.params.get("wght_min", 1.0),
                width=120, step=0.1, format="%.2f",
                callback=lambda s, a: (node.params.update({"wght_min": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="wght max",
                default_value=node.params.get("wght_max", 0.0),
                width=120, step=0.1, format="%.2f",
                callback=lambda s, a: (node.params.update({"wght_max": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="Multiline",
                default_value=node.params.get("multiline", True),
                callback=lambda s, a: (node.params.update({"multiline": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, parent=node.node_id) as attr_id:
            port = Port("style", "output", "style", attr_id)
            node.outputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Style Out", indent=4)


# ---------------------------------------------------------------------------
# Layout Node
# ---------------------------------------------------------------------------

@register
class LayoutNodeDef(NodeDef):
    node_type = "layout"
    label = "Layout"
    color = (180, 140, 60)

    @classmethod
    def default_params(cls):
        return {
            "xalign": True,
            "track_amount": 50,
            "track_vertical": True,
            "align": True,
        }

    @classmethod
    def build(cls, node: NodeInstance, graph: GraphState, on_change, editor_tag: str):
        dpg.set_item_label(node.node_id, "Layout")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, parent=node.node_id) as attr_id:
            port = Port("style", "input", "style", attr_id)
            node.inputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Style In", indent=4)

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="xalign",
                default_value=node.params.get("xalign", True),
                callback=lambda s, a: (node.params.update({"xalign": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_int(
                label="Track",
                default_value=node.params.get("track_amount", 50),
                width=120,
                callback=lambda s, a: (node.params.update({"track_amount": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="Track Vertical",
                default_value=node.params.get("track_vertical", True),
                callback=lambda s, a: (node.params.update({"track_vertical": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="align",
                default_value=node.params.get("align", True),
                callback=lambda s, a: (node.params.update({"align": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, parent=node.node_id) as attr_id:
            port = Port("layout", "output", "layout", attr_id)
            node.outputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Layout Out", indent=4)


# ---------------------------------------------------------------------------
# Extrude Node (Blender)
# ---------------------------------------------------------------------------

@register
class ExtrudeNodeDef(NodeDef):
    node_type = "extrude"
    label = "Extrude (Blender)"
    color = (160, 80, 200)

    @classmethod
    def default_params(cls):
        return {
            "animated": True,
            "easing": "seio",
            "rng_min": 0.1,
            "rng_max": 1.75,
            "offset_per_glyph": 5,
            "static_val": 0.5,
        }

    @classmethod
    def build(cls, node: NodeInstance, graph: GraphState, on_change, editor_tag: str):
        dpg.set_item_label(node.node_id, "Extrude (Blender)")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, parent=node.node_id) as attr_id:
            port = Port("layout", "input", "layout", attr_id)
            node.inputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Layout In", indent=4)

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_checkbox(
                label="Animated",
                default_value=node.params.get("animated", True),
                callback=lambda s, a: (node.params.update({"animated": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_combo(
                items=["seio", "eei", "eeio", "lin"],
                default_value=node.params.get("easing", "seio"),
                label="Easing",
                width=120,
                callback=lambda s, a: (node.params.update({"easing": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="Range Min",
                default_value=node.params.get("rng_min", 0.1),
                width=120, step=0.05, format="%.2f",
                callback=lambda s, a: (node.params.update({"rng_min": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="Range Max",
                default_value=node.params.get("rng_max", 1.75),
                width=120, step=0.05, format="%.2f",
                callback=lambda s, a: (node.params.update({"rng_max": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_int(
                label="Glyph Offset",
                default_value=node.params.get("offset_per_glyph", 5),
                width=120,
                callback=lambda s, a: (node.params.update({"offset_per_glyph": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=node.node_id):
            dpg.add_input_float(
                label="Static Val",
                default_value=node.params.get("static_val", 0.5),
                width=120, step=0.1, format="%.2f",
                callback=lambda s, a: (node.params.update({"static_val": a}), on_change()),
            )

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, parent=node.node_id) as attr_id:
            port = Port("scene", "output", "scene", attr_id)
            node.outputs.append(port)
            graph.attr_map[attr_id] = (node, port)
            dpg.add_text("Scene Out", indent=4)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_node(
    node_type: str,
    graph: GraphState,
    on_change,
    editor_tag: str,
    pos: tuple[float, float] = (100.0, 100.0),
    params: dict | None = None,
) -> NodeInstance:
    """Create a NodeInstance, add its DPG node, and build all widgets."""
    cls = NODE_REGISTRY[node_type]
    p = cls.default_params()
    if params:
        p.update(params)

    node = NodeInstance(node_type=node_type, pos=pos, params=p)

    node_id = dpg.add_node(
        label=cls.label,
        parent=editor_tag,
        pos=list(pos),
    )
    node.node_id = node_id

    # Set header color theme
    r, g, b = cls.color
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvNode):
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (r, g, b, 255), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (min(r+30, 255), min(g+30, 255), min(b+30, 255), 255), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (min(r+50, 255), min(g+50, 255), min(b+50, 255), 255), category=dpg.mvThemeCat_Nodes)
    dpg.bind_item_theme(node_id, theme_id)

    cls.build(node, graph, on_change, editor_tag)
    graph.nodes.append(node)
    return node
