from dataclasses import dataclass, field
from typing import Any


@dataclass
class Port:
    name: str           # "text", "style", "layout", "scene"
    port_type: str      # "input" | "output"
    data_type: str      # "text" | "style" | "layout" | "scene"
    attribute_id: int = -1  # Dear PyGui attribute item ID, set on build


@dataclass
class NodeInstance:
    node_type: str                          # "output" | "text" | "style" | "layout" | "extrude"
    node_id: int = -1                       # Dear PyGui node item ID
    pos: tuple[float, float] = (100.0, 100.0)
    params: dict[str, Any] = field(default_factory=dict)
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)

    def get_input(self, name: str) -> "Port | None":
        return next((p for p in self.inputs if p.name == name), None)

    def get_output(self, name: str) -> "Port | None":
        return next((p for p in self.outputs if p.name == name), None)


@dataclass
class Link:
    link_id: int    # Dear PyGui link item ID
    from_attr: int  # source attribute_id
    to_attr: int    # destination attribute_id


@dataclass
class GraphState:
    nodes: list[NodeInstance] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    # attribute_id -> (NodeInstance, Port)
    attr_map: dict[int, tuple[NodeInstance, Port]] = field(default_factory=dict)

    def find_node(self, node_type: str) -> "NodeInstance | None":
        return next((n for n in self.nodes if n.node_type == node_type), None)

    def find_upstream(self, node: NodeInstance, input_port_name: str) -> "NodeInstance | None":
        """Return the node connected to the named input port of `node`, or None."""
        port = node.get_input(input_port_name)
        if port is None or port.attribute_id == -1:
            return None
        for link in self.links:
            if link.to_attr == port.attribute_id:
                source_attr = link.from_attr
                entry = self.attr_map.get(source_attr)
                if entry:
                    return entry[0]
        return None
