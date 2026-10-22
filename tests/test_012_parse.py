"""Brief 012: the clue-list parser on hand-written posts in three blogger
styles (invented clues, not copied from any post)."""

from __future__ import annotations

from ximenes.clue import Orientation
from ximenes.fifteen import parse

TABLE = """
<p>Intro text by the blogger, 12 minutes today.</p>
<table><tbody>
<tr><td colspan="2"><strong>Across</strong></td></tr>
<tr><td>1</td><td><strong>CARPET</strong></td></tr>
<tr><td></td><td>Vehicle beside animal makes <u>rug</u> (6)</td></tr>
<tr><td></td><td>CAR + PET</td></tr>
<tr><td>4</td><td><strong>SEA LION</strong></td></tr>
<tr><td></td><td><span style="text-decoration: underline;">Marine mammal</span>
in sale, oddly (3,4)</td></tr>
<tr><td></td><td>Anagram of ALONE IS minus... (it's a fixture)</td></tr>
<tr><td colspan="2"><strong>Down</strong></td></tr>
<tr><td>2</td><td><strong>ASH</strong></td></tr>
<tr><td></td><td><span class="definition">Tree</span> remains (3)</td></tr>
<tr><td></td><td>Double definition</td></tr>
</tbody></table>
"""

PARAGRAPHS = """
<p><strong>ACROSS</strong></p>
<p>1 <span style="text-decoration:underline">Rug</span> vehicle beside animal (6)<br/>
<strong>CARPET</strong><br/>CAR + PET</p>
<p>5 Listen, broken <u>tinsel</u>? Not quite (6)<br/><strong>LISTEN</strong><br/>
Anagram (broken) of TINSEL</p>
<p><strong>DOWN</strong></p>
<p>3 Self-made <u>man</u>? (4-4)<br/><b>WELL-OFF</b><br/>no: wrong length, so skipped</p>
<p>7 <u>Bird</u> in the hand (3)<br/><b>EMU</b><br/>Hidden in thE MUd... (a fixture)</p>
"""

INLINE = """
<p>1a CARPET Vehicle beside animal makes <u>rug</u> (6) &#8211; CAR + PET</p>
<p>2d ASH <u>Tree</u> remains (3) &#8211; double definition</p>
<p>10a Answer missing here (5) &#8211; only lower case</p>
"""


def by_key(entries: list) -> dict:
    return {(e.number, e.orientation): e for e in entries}


def test_table_style() -> None:
    es = by_key(parse(TABLE))
    a1 = es[(1, Orientation.ACROSS)]
    assert a1.answer == "CARPET" and a1.clue == "Vehicle beside animal makes rug"
    assert a1.clue_marked == "Vehicle beside animal makes {rug}" and a1.wordplay == "CAR + PET"
    assert es[(4, Orientation.ACROSS)].answer == "SEALION"
    assert es[(4, Orientation.ACROSS)].enumeration.parts == (3, 4)
    d2 = es[(2, Orientation.DOWN)]
    assert d2.answer == "ASH" and d2.clue_marked == "{Tree} remains"
    assert d2.wordplay == "Double definition"


def test_paragraph_style() -> None:
    es = by_key(parse(PARAGRAPHS))
    assert es[(1, Orientation.ACROSS)].answer == "CARPET"
    assert es[(1, Orientation.ACROSS)].clue_marked == "{Rug} vehicle beside animal"
    assert es[(5, Orientation.ACROSS)].answer == "LISTEN"
    assert (3, Orientation.DOWN) not in es  # WELLOFF has 7 letters, not 8
    assert es[(7, Orientation.DOWN)].answer == "EMU"


def test_inline_style_with_direction_suffixes() -> None:
    es = by_key(parse(INLINE))
    assert es[(1, Orientation.ACROSS)].answer == "CARPET"
    assert es[(1, Orientation.ACROSS)].clue == "Vehicle beside animal makes rug"
    assert es[(2, Orientation.DOWN)].answer == "ASH"
    assert (10, Orientation.ACROSS) not in es
