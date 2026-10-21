from ximenes.clue import normalise, parse_enumeration, split_clue


def test_split_and_enumeration() -> None:
    text, enum = split_clue("Wolf trap missing its lowest crosspiece? (5)")
    assert text == "Wolf trap missing its lowest crosspiece?"
    assert enum.parts == (5,)
    assert enum.matches("SNARF")
    assert not enum.matches("SCARFS")


def test_multiword_enumeration() -> None:
    e = parse_enumeration("4,3-2")
    assert e.parts == (4, 3, 2)
    assert e.hyphens == (False, True)
    assert e.length == 9


def test_tokens_have_stable_ids() -> None:
    text, enum = split_clue("Support broadcast for propaganda? (8)")
    from ximenes.clue import Clue

    toks = Clue(text, enum).tokens
    assert [t.text for t in toks] == ["Support", "broadcast", "for", "propaganda"]
    assert [t.id for t in toks] == [0, 1, 2, 3]


def test_normalise() -> None:
    assert normalise("proposal") == "PROPOSAL"
    assert normalise("Te-He!") == "TEHE"
