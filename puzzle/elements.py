"""Generic, puzzle-agnostic drawing elements shared by every rule.

A *layer* binds one of these elements to a variable (or to instance
parameters), so the same visual primitive — a number, a shaded cell, a circle,
an arrow, a loop segment — can be reused by any number of puzzles. The web
front-end renders layers purely from this table; it never special-cases a
puzzle type.

``target`` is the lattice the element is drawn on (``cell`` / ``corner`` /
``edge`` / ``outside``). ``values`` documents the integer encoding used by the
solver variable behind the layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ElementType:
    id: str
    label: str
    targets: tuple[str, ...]
    doc: str
    # Suggested integer encoding: value -> human meaning.
    values: dict[str, str] = field(default_factory=dict)
    # Editing style used by the front-end palette.
    editor: str = "cycle"  # cycle | int | text | paint | toggle | direction


ELEMENT_TYPES: tuple[ElementType, ...] = (
    ElementType(
        "number", "数字", ("cell", "corner", "edge", "outside"),
        "An integer drawn inside the target (clues and filled answers).",
        editor="int",
    ),
    ElementType(
        "text", "字符", ("cell", "outside"),
        "A short string (letters used by Easy as ABC, Pentominous, ...).",
        editor="text",
    ),
    ElementType(
        "shade", "涂色", ("cell",),
        "A solid fill; the value selects the colour from the layer palette.",
        {"0": "留白 (white)", "1": "涂黑 (black)", "2": "第三色 (extra)"},
        editor="paint",
    ),
    ElementType(
        "circle", "圆圈", ("cell", "corner"),
        "A circle outline/fill; value selects white / black / grey.",
        {"0": "无", "1": "白圈", "2": "黑圈", "3": "灰圈"},
    ),
    ElementType(
        "square", "方块", ("cell",),
        "A small square marker; value selects white / black / grey.",
        {"0": "无", "1": "白方", "2": "黑方", "3": "灰方"},
    ),
    ElementType(
        "triangle", "三角形", ("cell",),
        "A right triangle occupying one corner of the cell (Shakashaka, "
        "Nurimaze, Reflect Link).",
        {"0": "无", "1": "↖", "2": "↗", "3": "↘", "4": "↙"},
    ),
    ElementType(
        "star", "星星", ("cell",),
        "A star marker (Star Battle, Guide Arrow goal).",
        {"0": "无", "1": "星"},
    ),
    ElementType(
        "cross", "叉号", ("cell", "corner"),
        "A ✕ mark, usually meaning 'forbidden here'.",
        {"0": "无", "1": "✕"},
    ),
    ElementType(
        "dot", "圆点", ("corner", "edge"),
        "A dot on a lattice corner or edge midpoint (Kropki, Border Block).",
        {"0": "无", "1": "白点", "2": "黑点", "3": "灰点"},
    ),
    ElementType(
        "arrow", "箭头", ("cell", "outside"),
        "An arrow; the value is a direction code 0-7 "
        "(UP/DOWN/LEFT/RIGHT/UP_LEFT/UP_RIGHT/DOWN_LEFT/DOWN_RIGHT), 8 = none.",
        {str(i): d for i, d in enumerate(
            ["↑", "↓", "←", "→", "↖", "↗", "↙", "↘", "无"]
        )},
        editor="direction",
    ),
    ElementType(
        "edgeline", "格线", ("edge",),
        "A thick segment drawn on a lattice edge — region borders, walls and "
        "Slitherlink-style loops that run along cell boundaries.",
        {"0": "无", "1": "有线"},
        editor="toggle",
    ),
    ElementType(
        "link", "连线", ("edge",),
        "A segment joining the centres of the two cells an edge separates — "
        "loops and paths that run through cell centres.",
        {"0": "无", "1": "有线"},
        editor="toggle",
    ),
    ElementType(
        "diagonal", "对角线", ("cell",),
        "A diagonal drawn inside a cell (Slant, Slash Pack, mirrors).",
        {"0": "无", "1": "╲", "2": "╱"},
    ),
    ElementType(
        "region", "区域", ("cell",),
        "Region membership: cells sharing a value form one region, drawn as a "
        "tint plus thick borders between different values.",
        editor="paint",
    ),
    ElementType(
        "outside", "盘外提示", ("outside",),
        "Clues written outside the board, stored in the instance parameters "
        "as one list per row/column and per side.",
        editor="text",
    ),
    # -- special picture elements (特殊题面) --------------------------------
    ElementType(
        "tree", "树", ("cell",),
        "A tree (Tents 帐篷).",
        {"0": "无", "1": "树"},
    ),
    ElementType(
        "tent", "帐篷", ("cell",),
        "A tent (Tents 帐篷).",
        {"0": "无", "1": "帐篷"},
    ),
    ElementType(
        "ship", "船", ("cell",),
        "A battleship part (Battleships 战舰).",
        {"0": "无", "1": "单格船", "2": "船身", "3": "船头朝上",
         "4": "船头朝下", "5": "船头朝左", "6": "船头朝右"},
    ),
    ElementType(
        "wave", "水波", ("cell",),
        "Water marker: no ship may occupy this cell (Battleships).",
        {"0": "无", "1": "水"},
    ),
    ElementType(
        "bulb", "灯泡", ("cell",),
        "A light bulb (Akari 美术馆).",
        {"0": "无", "1": "灯泡"},
    ),
)

ELEMENTS_BY_ID = {element.id: element for element in ELEMENT_TYPES}


def elements_json() -> list[dict]:
    """The element catalogue in a JSON-serialisable form (served to the UI)."""

    return [asdict(element) | {"targets": list(element.targets)} for element in ELEMENT_TYPES]
