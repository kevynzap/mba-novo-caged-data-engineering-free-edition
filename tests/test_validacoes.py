
import re


def cbo_valido(codigo):
    """Verifica se o CBO contém exatamente 6 dígitos."""
    return bool(re.fullmatch(r"\d{6}", str(codigo)))


def test_cbo_valido():
    assert cbo_valido("212405")


def test_cbo_com_zeros_a_esquerda():
    assert cbo_valido("012345")


def test_cbo_invalido():
    assert not cbo_valido("123")
    assert not cbo_valido("ABCDEF")
