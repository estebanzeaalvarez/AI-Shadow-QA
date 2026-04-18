import pytest
from example_code import process_list

def test_process_list_empty():
    with pytest.raises(ValueError) as e:
        process_list(None)
    assert str(e.value) == "No se puede procesar una lista vacía o None"

def test_process_list_non_string():
    with pytest.raises(ValueError) as e:
        process_list([1, 2, 3])
    assert str(e.value) == "La lista contiene elementos no string"

def test_process_list_valid():
    result = process_list(["hello", "world"])
    assert result == "Procesando hello"




import pytest
from example_code import calculate_discount

def test_calculate_discount_invalid_price_type():
    with pytest.raises(ValueError) as e:
        calculate_discount("price", 10)
    assert str(e.value) == "price y discount deben ser números"

def test_calculate_discount_negative_price():
    with pytest.raises(ValueError) as e:
        calculate_discount(-10, 5)
    assert str(e.value) == "price no puede ser negativo"

def test_calculate_discount_invalid_discount_type():
    with pytest.raises(ValueError) as e:
        calculate_discount(10, "discount")
    assert str(e.value) == "price y discount deben ser números"

def test_calculate_discount_negative_discount():
    with pytest.raises(ValueError) as e:
        calculate_discount(10, -5)
    assert str(e.value) == "discount no puede ser negativo"

def test_calculate_discount_invalid_discount_value():
    with pytest.raises(ValueError) as e:
        calculate_discount(10, 15)
    assert str(e.value) == "El descuento no puede ser mayor que el precio"

def test_calculate_discount_valid():
    result = calculate_discount(100, 20)
    assert result == 80