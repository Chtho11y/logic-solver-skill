"""Write spec JSON + sample for numlin (路径I). Hashi is deferred."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.scaffold import (  # noqa: E402
    clue_number,
    layer,
    link_layer,
    sample,
    var,
    write_sample,
    write_spec,
)
from tools.samples import from_grid  # noqa: E402


def _write():
    write_spec(
        "numlin",
        variables=[
            var("e", "edge", "normal", (0, 1), "1 = 路径"),
            var("x", "cell", "normal", (0, 20), "0=空 其余=路径编号"),
            var("n", "cell", "constant", doc="端点数字"),
        ],
        layers=[
            clue_number("n", "端点数字"),
            layer("answer", "路径编号", "number", role="output", var="x"),
            link_layer("e", "路径"),
        ],
        rows=8, cols=8,
        notes="每对相同数字一条不交叉路径。x 为路径编号（0=不经过）。domain 上限 20。",
    )
    write_sample("numlin", sample(
        "numlin", 4, 4, title="4x4 两对数连",
        clues={"n": from_grid("""
            1 . . 1
            . . . .
            . . . .
            2 . . 2
        """)},
    ))


if __name__ == "__main__":
    _write()
    print("wrote numlin spec and sample")
