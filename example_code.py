def process_list(items):
    # Cambiamos el 'return' por 'raise' para que el test esté feliz
    if items is None or not isinstance(items, list) or len(items) == 0:
        raise ValueError("No se puede procesar una lista vacía o None")
    
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"La lista contiene elementos no string")
    
    first = items[0]
    return f"Procesando {first}"

def calculate_discount(price, discount):
    if not isinstance(price, (int, float)) or not isinstance(discount, (int, float)):
        raise ValueError("price y discount deben ser números")
    
    if price < 0 or discount < 0:
        raise ValueError("price y discount no pueden ser negativos")
    
    if discount > price:
        # Si el test espera error, lanzamos ValueError. 
        # Si prefieres el mensaje, el test debería cambiar.
        raise ValueError("El descuento no puede ser mayor que el precio")
        
    return price - discount