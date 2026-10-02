import hashlib, hmac, re
from .config import APP_SECRET
BLOCKED=[r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', r'(?<!\d)(?:\+?57)?[ -]?(?:3\d{2})[ -]?\d{3}[ -]?\d{4}(?!\d)']
def hash_token(value:str)->str: return hashlib.sha256(value.encode()).hexdigest()
def safe_text(value:str)->str:
    value=value.strip()
    if not value: raise ValueError('El texto está vacío.')
    for p in BLOCKED:
        if re.search(p,value,re.I): raise ValueError('No publiques teléfonos ni correos.')
    return value
def server_alias(code:str, thread_id:str)->str:
    digest=hmac.new(APP_SECRET.encode(), f'{code}:{thread_id}'.encode(), hashlib.sha256).hexdigest()
    animals=['Zorro','Marea','Cuervo','Lince','Bruma','Faro','Nube','Búho']
    colors=['Azul','Ámbar','Violeta','Verde','Gris','Rojo','Índigo','Dorado']
    return f'{animals[int(digest[:2],16)%len(animals)]} {colors[int(digest[2:4],16)%len(colors)]} {int(digest[4:8],16)%100}'
