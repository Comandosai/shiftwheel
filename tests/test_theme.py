"""ShiftWheel: the Comandos Light radial theme renders with the expected palette."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QColor, QImage  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _render(app, hover):
    from dragshift import radial
    rings = {"Convert": [radial.Item(t, hint="x") for t in ("MOV", "WEBM", "GIF", "MP3", "M4A", "WAV")]}
    m = radial.RadialMenu(lambda p: rings, lambda p: "12 MB")
    m.paths, m.rings, m.ring_names, m.ring_idx = ["/x/a.mp4"], rings, ["Convert"], 0
    m.hub_text = "12 MB"
    m.spring = [0.0] * 6
    m.hover = hover
    if hover >= 0:
        m.spring[hover] = 1.0
    img = QImage(radial.SIZE, radial.SIZE, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    m.render(img, QPoint(0, 0))
    return radial, img


def near(c: QColor, hexcol: str, tol=12):
    t = QColor(hexcol)
    return abs(c.red() - t.red()) <= tol and abs(c.green() - t.green()) <= tol and abs(c.blue() - t.blue()) <= tol


def test_default_theme_is_comandos():
    from dragshift import radial
    assert radial.THEME in ("comandos", "glass")
    if "SHIFTWHEEL_THEME" not in os.environ:
        assert radial.THEME == "comandos"


def test_comandos_palette(app):
    radial, img = _render(app, hover=0)
    if radial.THEME != "comandos":
        pytest.skip("glass theme selected")
    c = radial.SIZE // 2
    assert near(img.pixelColor(c, c - 30), "#16130f")          # ink hub
    assert near(img.pixelColor(c + 15, c - 140), "#d9fc67")    # hovered top petal is lime
    assert near(img.pixelColor(c + 120, c + 20), "#fcfcf6")    # idle petal is cream card
    _, idle = _render(app, hover=-1)
    assert near(idle.pixelColor(c + 15, c - 140), "#fcfcf6")
