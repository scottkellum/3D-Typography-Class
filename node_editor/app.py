"""
Main Dear PyGui application for the ColdType node editor.
"""
import json
from pathlib import Path

import dearpygui.dearpygui as dpg

from .model import GraphState, Link
from .nodes import NODE_REGISTRY, create_node
from .codegen import generate
from . import runner

PROJECT_ROOT = Path(__file__).parent.parent
TARGET_FILE = PROJECT_ROOT / "cold-node.py"
STATE_FILE = PROJECT_ROOT / "node_editor_state.json"

EDITOR_TAG = "node_editor"
CODE_TAG = "code_preview"
STATUS_TAG = "status_text"

graph = GraphState()
_status = {"text": "Idle"}


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def _save_code() -> None:
    code = generate(graph)
    TARGET_FILE.write_text(code)
    dpg.set_value(CODE_TAG, code)


def _save_state() -> None:
    data = {
        "nodes": [
            {
                "node_type": n.node_type,
                "pos": list(dpg.get_item_pos(n.node_id)) if n.node_id != -1 else list(n.pos),
                "params": n.params,
            }
            for n in graph.nodes
        ],
        "links": [
            {
                "from_node_idx": _attr_to_node_idx(lk.from_attr),
                "from_port": _attr_to_port_name(lk.from_attr),
                "to_node_idx": _attr_to_node_idx(lk.to_attr),
                "to_port": _attr_to_port_name(lk.to_attr),
            }
            for lk in graph.links
        ],
    }
    STATE_FILE.write_text(json.dumps(data, indent=2))


def _attr_to_node_idx(attr_id: int) -> int:
    entry = graph.attr_map.get(attr_id)
    if entry:
        node = entry[0]
        try:
            return graph.nodes.index(node)
        except ValueError:
            pass
    return -1


def _attr_to_port_name(attr_id: int) -> str:
    entry = graph.attr_map.get(attr_id)
    if entry:
        return entry[1].name
    return ""


def on_change() -> None:
    _save_code()
    _save_state()


# ---------------------------------------------------------------------------
# Graph mutation helpers
# ---------------------------------------------------------------------------

def add_node(node_type: str, pos: tuple[float, float] | None = None) -> None:
    if pos is None:
        pos = (200.0, 200.0)
    create_node(node_type, graph, on_change, EDITOR_TAG, pos=pos)
    on_change()


def _link_nodes(from_attr: int, to_attr: int) -> None:
    link_id = dpg.add_node_link(from_attr, to_attr, parent=EDITOR_TAG)
    graph.links.append(Link(link_id=link_id, from_attr=from_attr, to_attr=to_attr))
    on_change()


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def on_link_created(sender, app_data) -> None:
    from_attr, to_attr = app_data[0], app_data[1]
    # Remove any existing link going INTO the same input port
    to_remove = [lk for lk in graph.links if lk.to_attr == to_attr]
    for lk in to_remove:
        dpg.delete_item(lk.link_id)
        graph.links.remove(lk)
    link_id = dpg.add_node_link(from_attr, to_attr, parent=EDITOR_TAG)
    graph.links.append(Link(link_id=link_id, from_attr=from_attr, to_attr=to_attr))
    on_change()


def on_link_deleted(sender, app_data) -> None:
    link_id = app_data
    graph.links = [lk for lk in graph.links if lk.link_id != link_id]
    dpg.delete_item(link_id)
    on_change()


def _set_status(text: str) -> None:
    _status["text"] = text
    dpg.set_value(STATUS_TAG, f"  {text}")


# ---------------------------------------------------------------------------
# Popup context menu
# ---------------------------------------------------------------------------

def _show_add_menu() -> None:
    dpg.configure_item("add_node_popup", show=True)


def _build_context_menu() -> None:
    with dpg.window(
        tag="add_node_popup",
        popup=True,
        show=False,
        no_title_bar=True,
        min_size=(160, 10),
    ):
        dpg.add_text("Add Node", color=(200, 200, 200, 200))
        dpg.add_separator()
        labels = {
            "output": "Output",
            "text": "Text",
            "style": "Font Style",
            "layout": "Layout",
            "extrude": "Extrude (Blender)",
        }
        for node_type, label in labels.items():
            dpg.add_menu_item(
                label=label,
                callback=lambda s, a, u=node_type: (
                    add_node(u, pos=tuple(dpg.get_mouse_pos(local=False))),
                    dpg.configure_item("add_node_popup", show=False),
                ),
            )


# ---------------------------------------------------------------------------
# Starter graph (mirrors cold-node.py)
# ---------------------------------------------------------------------------

def _build_starter_graph() -> None:
    text = create_node("text", graph, on_change, EDITOR_TAG, pos=(40, 100))
    style = create_node("style", graph, on_change, EDITOR_TAG, pos=(280, 60))
    layout = create_node("layout", graph, on_change, EDITOR_TAG, pos=(560, 80))
    extrude = create_node("extrude", graph, on_change, EDITOR_TAG, pos=(790, 60))
    output = create_node("output", graph, on_change, EDITOR_TAG, pos=(1060, 100))

    # text.text_out → style.text_in
    _link_nodes(text.get_output("text").attribute_id, style.get_input("text").attribute_id)
    # style.style_out → layout.style_in
    _link_nodes(style.get_output("style").attribute_id, layout.get_input("style").attribute_id)
    # layout.layout_out → extrude.layout_in
    _link_nodes(layout.get_output("layout").attribute_id, extrude.get_input("layout").attribute_id)
    # extrude.scene_out → output.scene_in
    _link_nodes(extrude.get_output("scene").attribute_id, output.get_input("scene").attribute_id)


# ---------------------------------------------------------------------------
# Session restore
# ---------------------------------------------------------------------------

def _restore_state() -> bool:
    if not STATE_FILE.exists():
        return False
    try:
        data = json.loads(STATE_FILE.read_text())
    except Exception:
        return False

    nodes_data = data.get("nodes", [])
    for nd in nodes_data:
        create_node(
            nd["node_type"],
            graph,
            on_change,
            EDITOR_TAG,
            pos=tuple(nd.get("pos", (100, 100))),
            params=nd.get("params"),
        )

    # Re-link using node index + port name
    for lk_data in data.get("links", []):
        fi = lk_data.get("from_node_idx", -1)
        ti = lk_data.get("to_node_idx", -1)
        fp = lk_data.get("from_port", "")
        tp = lk_data.get("to_port", "")
        if fi == -1 or ti == -1:
            continue
        try:
            from_node = graph.nodes[fi]
            to_node = graph.nodes[ti]
        except IndexError:
            continue
        from_port = from_node.get_output(fp)
        to_port = to_node.get_input(tp)
        if from_port and to_port:
            link_id = dpg.add_node_link(
                from_port.attribute_id, to_port.attribute_id, parent=EDITOR_TAG
            )
            graph.links.append(Link(link_id=link_id, from_attr=from_port.attribute_id, to_attr=to_port.attribute_id))

    return True


# ---------------------------------------------------------------------------
# Mouse handler for right-click on node editor
# ---------------------------------------------------------------------------

def _build_mouse_handler() -> None:
    with dpg.handler_registry():
        dpg.add_mouse_click_handler(
            button=dpg.mvMouseButton_Right,
            callback=lambda: (
                dpg.is_item_hovered(EDITOR_TAG) and _show_add_menu()
            ),
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def run() -> None:
    dpg.create_context()
    dpg.create_viewport(
        title="ColdType Node Editor",
        width=1400,
        height=800,
        min_width=900,
        min_height=500,
    )
    dpg.setup_dearpygui()

    _build_context_menu()
    _build_mouse_handler()

    with dpg.window(tag="main_window", no_title_bar=True, no_move=True, no_resize=True):
        # Top toolbar
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=" Launch ColdType ",
                callback=lambda: runner.launch_coldtype(
                    lambda s: _set_status(s)
                ),
            )
            dpg.add_button(
                label=" Launch Blender ",
                callback=lambda: runner.launch_blender(
                    lambda s: _set_status(s)
                ),
            )
            dpg.add_text("  |  Status: ", color=(160, 160, 160, 200))
            dpg.add_text("Idle", tag=STATUS_TAG, color=(120, 220, 120, 255))

        dpg.add_separator()

        # Two-column layout: node editor | code preview
        with dpg.table(
            header_row=False,
            borders_innerV=True,
            resizable=True,
        ):
            dpg.add_table_column(init_width_or_weight=0.65)
            dpg.add_table_column(init_width_or_weight=0.35)

            with dpg.table_row():
                with dpg.table_cell():
                    with dpg.node_editor(
                        tag=EDITOR_TAG,
                        callback=on_link_created,
                        delink_callback=on_link_deleted,
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                    ):
                        pass  # nodes added dynamically

                with dpg.table_cell():
                    dpg.add_text("Generated Python:", color=(160, 160, 160, 200))
                    dpg.add_input_text(
                        tag=CODE_TAG,
                        multiline=True,
                        readonly=True,
                        width=-1,
                        height=-1,
                        default_value="# Connect nodes to generate code",
                    )

    # Populate graph
    if not _restore_state():
        _build_starter_graph()

    # Initial codegen
    on_change()

    # Make main window fill the viewport
    dpg.set_primary_window("main_window", True)

    def _frame_check():
        status = runner.poll_status()
        if status:
            _set_status(status)

    dpg.set_frame_callback(2, _frame_check)

    dpg.set_exit_callback(runner.cleanup_all)

    dpg.show_viewport()

    # Main loop with per-frame status polling
    while dpg.is_dearpygui_running():
        status = runner.poll_status()
        if status:
            _set_status(status)
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
