from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from typing import Optional
import hashlib, os, sys, smtplib
from email.mime.text import MIMEText

# ── Cargar config privada ──
try:
    from config_secretos import ADMIN_PASSWORD, GMAIL_USER, GMAIL_PASSWORD
except ImportError:
    ADMIN_PASSWORD = "SaludNatura2026!"
    GMAIL_USER = ""
    GMAIL_PASSWORD = ""

def _enviar_correo(asunto: str, cuerpo: str):
    if not GMAIL_USER or not GMAIL_PASSWORD:
        return
    try:
        msg = MIMEText(cuerpo, "plain", "utf-8")
        msg["Subject"] = asunto
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
    except Exception:
        pass

def _hash_password(password: str) -> str:
    """Hash seguro con salt usando pbkdf2 (sin instalar nada extra)."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
    return salt.hex() + ":" + dk.hex()

def _verify_password(password: str, stored: str) -> bool:
    """Verifica contraseña con hash pbkdf2 o legacy sha256."""
    if ":" in stored:  # formato nuevo con salt
        salt_hex, dk_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
        return dk.hex() == dk_hex
    else:  # formato viejo sha256 sin salt — aceptar pero migrar
        return hashlib.sha256(password.encode()).hexdigest() == stored

def _verificar_admin(request: Request):
    """Verifica cookie/header de sesión admin."""
    token = request.cookies.get("admin_token") or request.headers.get("X-Admin-Token", "")
    expected = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
    if token != expected:
        raise HTTPException(status_code=401, detail="No autorizado")

from app.config import settings
from app.database import init_db, get_db
from app.models import RemedioIn, UsuarioIn


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings,
    })


@app.get("/grimorio")
async def grimorio(request: Request):
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "grimorio.html")
    return FileResponse(path, media_type="text/html")


@app.get("/botiquin")
async def botiquin(request: Request):
    return templates.TemplateResponse("botiquin.html", {"request": request})




@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/remedios")
async def listar_remedios():
    conn = get_db()
    remedios = [dict(r) for r in conn.execute("SELECT * FROM base_conocimiento_salud").fetchall()]
    conn.close()
    return {"ok": True, "data": remedios}


@app.get("/api/botiquin")
async def listar_botiquin():
    conn = get_db()
    # Calcular índice del grimorio (posición 0-based en lista ordenada por id_remedio)
    idx_map = {r[0]: i for i, r in enumerate(
        conn.execute("SELECT id_remedio FROM base_conocimiento_salud ORDER BY id_remedio").fetchall()
    )}
    rows = []
    for r in conn.execute("SELECT * FROM botiquin ORDER BY id").fetchall():
        item = dict(r)
        item["grimorio_idx"] = idx_map.get(item.get("id_remedio"), None)
        rows.append(item)
    conn.close()
    return {"ok": True, "data": rows}


@app.get("/api/plantas")
async def listar_plantas():
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        "SELECT id_remedio, nombre_remedio, planta_base, propiedades, contraindicaciones, "
        "dosificacion, link_articulo_web, nombres_alternativos, partes_utilizadas, fuentes, "
        "imagen_fuente, imagen_miniatura_url, imagen_directa_url FROM base_conocimiento_salud ORDER BY id_remedio"
    ).fetchall()]
    conn.close()
    for r in rows:
        r["imagen"] = r.get("imagen_miniatura_url") or ""
    return {"ok": True, "plantas": rows}


@app.get("/api/plantas/{id_planta}/miniatura")
async def miniatura_planta(id_planta: int):
    conn = get_db()
    row = conn.execute(
        "SELECT imagen_miniatura FROM base_conocimiento_salud WHERE id_remedio = ?", (id_planta,)
    ).fetchone()
    conn.close()
    if not row or not row["imagen_miniatura"]:
        return Response(status_code=404)
    return Response(content=bytes(row["imagen_miniatura"]), media_type="image/jpeg")


@app.get("/api/jugos")
async def listar_jugos():
    import json as _json
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM jugos ORDER BY id").fetchall()]
    conn.close()
    for r in rows:
        r["plantas"] = _json.loads(r["plantas"]) if r.get("plantas") else []
        r["ingredientes"] = _json.loads(r["ingredientes"]) if r.get("ingredientes") else []
        r["pasos"] = _json.loads(r["pasos"]) if r.get("pasos") else []
    return {"ok": True, "jugos": rows}


@app.get("/api/infusiones")
async def listar_infusiones():
    import json as _json
    conn = get_db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM infusiones ORDER BY id").fetchall()]
    conn.close()
    for r in rows:
        r["plantas"] = _json.loads(r["plantas"]) if r.get("plantas") else []
        r["ingredientes"] = _json.loads(r["ingredientes"]) if r.get("ingredientes") else []
        r["pasos"] = _json.loads(r["pasos"]) if r.get("pasos") else []
    return {"ok": True, "infusiones": rows}


@app.get("/api/remedios/{id_remedio}")
async def obtener_remedio(id_remedio: int):
    conn = get_db()
    remedio = conn.execute("SELECT * FROM base_conocimiento_salud WHERE id_remedio = ?", (id_remedio,)).fetchone()
    conn.close()
    if not remedio:
        return {"ok": False, "error": "Remedio no encontrado"}
    return {"ok": True, "data": dict(remedio)}


@app.post("/api/remedios")
async def crear_remedio(remedio: RemedioIn):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO base_conocimiento_salud (nombre_remedio, planta_base, propiedades, contraindicaciones, dosificacion, link_articulo_web) VALUES (?, ?, ?, ?, ?, ?)",
        (remedio.nombre_remedio, remedio.planta_base, remedio.propiedades, remedio.contraindicaciones, remedio.dosificacion, remedio.link_articulo_web),
    )
    conn.commit()
    id_nuevo = cursor.lastrowid
    conn.close()
    return {"ok": True, "id_remedio": id_nuevo}


@app.post("/api/contacto")
async def contacto(request: Request):
    body = await request.json()
    nombre  = body.get("nombre", "").strip()
    email   = body.get("email", "").strip()
    mensaje = body.get("mensaje", "").strip()
    id_usuario = body.get("id_usuario")
    if not nombre or not email or not mensaje:
        return {"ok": False, "error": "Faltan campos"}
    conn = get_db()
    conn.execute(
        "INSERT INTO consultas (nombre, email, mensaje, id_usuario) VALUES (?, ?, ?, ?)",
        (nombre, email, mensaje, id_usuario)
    )
    conn.commit()
    conn.close()
    _enviar_correo(
        f"Nueva consulta de {nombre} — Salud Natura",
        f"Nombre: {nombre}\nCorreo: {email}\n\nMensaje:\n{mensaje}"
    )
    return {"ok": True}


@app.post("/api/registro")
async def registro(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    if not email:
        return JSONResponse({"ok": False, "error": "Email requerido"}, status_code=400)
    conn = get_db()
    existente = conn.execute(
        "SELECT id_usuario, nombre_completo, email, celular, ciudad_prov_pais, pais_codigo FROM usuarios_y_clientes WHERE LOWER(email)=?", (email,)
    ).fetchone()
    if existente:
        conn.close()
        return JSONResponse({"ok": False, "error": "Email ya registrado", "usuario": dict(existente)}, status_code=409)
    password = body.get("password") or ""
    phash = _hash_password(password) if password else ""
    cursor = conn.execute(
        "INSERT INTO usuarios_y_clientes (nombre_completo, celular, email, direccion_completa, ciudad_prov_pais, latitud, longitud, pais_codigo, fecha_registro, password_hash) VALUES (?,?,?,?,?,?,?,?,datetime('now'),?)",
        (body.get("nombre_completo",""), body.get("celular",""), email,
         body.get("direccion_completa",""), body.get("ciudad_prov_pais",""),
         body.get("latitud"), body.get("longitud"),
         body.get("pais_codigo",""), phash)
    )
    conn.commit()
    id_nuevo = cursor.lastrowid
    nuevo = conn.execute(
        "SELECT id_usuario, nombre_completo, email, celular, ciudad_prov_pais, pais_codigo, latitud, longitud FROM usuarios_y_clientes WHERE id_usuario=?", (id_nuevo,)
    ).fetchone()
    conn.close()
    return {"ok": True, "usuario": dict(nuevo)}


@app.post("/api/login")
async def login(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not email:
        return JSONResponse({"ok": False, "error": "Email requerido"}, status_code=400)
    conn = get_db()
    usuario = conn.execute(
        "SELECT id_usuario, nombre_completo, email, celular, ciudad_prov_pais, pais_codigo, latitud, longitud, password_hash FROM usuarios_y_clientes WHERE LOWER(email)=?", (email,)
    ).fetchone()
    if not usuario:
        conn.close()
        return JSONResponse({"ok": False, "error": "Email o contraseña incorrectos"}, status_code=401)
    stored_hash = usuario["password_hash"] or ""
    if stored_hash and not _verify_password(password, stored_hash):
        conn.close()
        return JSONResponse({"ok": False, "error": "Email o contraseña incorrectos"}, status_code=401)
    # Si era hash viejo (sha256 sin salt), migrar al nuevo formato
    if stored_hash and ":" not in stored_hash and password:
        nuevo_hash = _hash_password(password)
        conn.execute("UPDATE usuarios_y_clientes SET password_hash=? WHERE id_usuario=?",
                     (nuevo_hash, usuario["id_usuario"]))
        conn.commit()
    conn.close()
    datos = {k: usuario[k] for k in ["id_usuario","nombre_completo","email","celular","ciudad_prov_pais","pais_codigo","latitud","longitud"]}
    return {"ok": True, "usuario": datos}


@app.post("/api/usuarios")
async def registrar_usuario(usuario: UsuarioIn):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO usuarios_y_clientes (nombre_completo, celular, email, direccion_completa, ciudad_prov_pais, latitud, longitud) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (usuario.nombre_completo, usuario.celular, usuario.email, usuario.direccion_completa, usuario.ciudad_prov_pais, usuario.latitud, usuario.longitud),
    )
    conn.commit()
    id_nuevo = cursor.lastrowid
    conn.close()
    return {"ok": True, "id_usuario": id_nuevo}


# ── Admin ──

_ADMIN_COOKIE = "sn_admin"

def _admin_ok(request: Request) -> bool:
    token = request.cookies.get(_ADMIN_COOKIE, "")
    return token == hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

def _redir_login(msg=""):
    r = RedirectResponse(f"/admin/login?msg={msg}", status_code=303)
    return r

@app.get("/admin/login")
async def admin_login_get(request: Request, msg: str = ""):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>Admin — Salud Natura</title>
    <style>body{{background:#0a1a0d;color:#f5edd8;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
    .box{{background:#0d2b1a;border:1px solid rgba(212,175,55,.3);border-radius:6px;padding:2rem 2.5rem;min-width:300px;text-align:center}}
    h2{{color:#d4af37;font-size:1.3rem;margin-bottom:1.5rem}}
    input{{width:100%;padding:.6rem;margin:.4rem 0 1rem;background:#060f08;border:1px solid rgba(212,175,55,.3);color:#f5edd8;border-radius:3px;box-sizing:border-box}}
    button{{background:#d4af37;color:#0a1a0d;border:none;padding:.7rem 2rem;border-radius:3px;cursor:pointer;font-weight:700;width:100%}}
    .err{{color:#ff6b6b;font-size:.85rem;margin-bottom:.5rem}}</style></head>
    <body><div class="box"><h2>🌿 Admin Salud Natura</h2>
    {"<p class='err'>Contraseña incorrecta</p>" if msg else ""}
    <form method="post"><input type="password" name="password" placeholder="Contraseña admin" autofocus/>
    <button type="submit">Entrar</button></form></div></body></html>"""
    return Response(content=html, media_type="text/html")

@app.post("/admin/login")
async def admin_login_post(request: Request, password: str = Form("")):
    if password == ADMIN_PASSWORD:
        token = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        r = RedirectResponse("/admin", status_code=303)
        r.set_cookie(_ADMIN_COOKIE, token, httponly=True, samesite="strict")
        return r
    return RedirectResponse("/admin/login?msg=1", status_code=303)

@app.get("/admin/logout")
async def admin_logout():
    r = RedirectResponse("/admin/login", status_code=303)
    r.delete_cookie(_ADMIN_COOKIE)
    return r

@app.get("/admin")
async def admin_inicio(request: Request):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    total_remedios = conn.execute("SELECT COUNT(*) FROM base_conocimiento_salud").fetchone()[0]
    total_usuarios = conn.execute("SELECT COUNT(*) FROM usuarios_y_clientes").fetchone()[0]
    conn.close()
    return templates.TemplateResponse("admin_inicio.html", {
        "request": request, "settings": settings, "seccion": "inicio",
        "total_remedios": total_remedios, "total_usuarios": total_usuarios,
    })


@app.get("/admin/remedios")
async def admin_remedios(request: Request, mensaje: Optional[str] = None):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    remedios = conn.execute("SELECT * FROM base_conocimiento_salud ORDER BY id_remedio DESC").fetchall()
    conn.close()
    return templates.TemplateResponse("admin_remedios.html", {
        "request": request, "settings": settings, "seccion": "remedios",
        "remedios": remedios, "mensaje": mensaje,
    })


@app.post("/admin/remedios/guardar")
async def admin_remedios_guardar(
    request: Request,
    nombre_remedio: str = Form(...),
    planta_base: str = Form(""),
    propiedades: str = Form(""),
    contraindicaciones: str = Form(""),
    dosificacion: str = Form(""),
    link_articulo_web: str = Form(""),
    imagen_url: str = Form(""),
    id_remedio: str = Form(""),
):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    if id_remedio:
        conn.execute(
            "UPDATE base_conocimiento_salud SET nombre_remedio=?, planta_base=?, propiedades=?, contraindicaciones=?, dosificacion=?, link_articulo_web=?, imagen_url=? WHERE id_remedio=?",
            (nombre_remedio, planta_base or None, propiedades or None, contraindicaciones or None, dosificacion or None, link_articulo_web or None, imagen_url or None, int(id_remedio)),
        )
        mensaje = "Remedio actualizado"
    else:
        conn.execute(
            "INSERT INTO base_conocimiento_salud (nombre_remedio, planta_base, propiedades, contraindicaciones, dosificacion, link_articulo_web, imagen_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nombre_remedio, planta_base or None, propiedades or None, contraindicaciones or None, dosificacion or None, link_articulo_web or None, imagen_url or None),
        )
        mensaje = "Remedio creado"
    conn.commit()
    conn.close()
    return RedirectResponse(f"/admin/remedios?mensaje={mensaje}", status_code=303)


@app.post("/admin/remedios/{id_remedio}/eliminar")
async def admin_remedios_eliminar(request: Request, id_remedio: int):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    conn.execute("DELETE FROM base_conocimiento_salud WHERE id_remedio=?", (id_remedio,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin/remedios?mensaje=Remedio eliminado", status_code=303)


@app.get("/admin/botiquin")
async def admin_botiquin(request: Request, mensaje: Optional[str] = None):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    items = conn.execute("SELECT * FROM botiquin ORDER BY id").fetchall()
    conn.close()
    return templates.TemplateResponse("admin_botiquin.html", {
        "request": request, "settings": settings, "items": items, "mensaje": mensaje,
    })


@app.post("/admin/botiquin/guardar")
async def admin_botiquin_guardar(
    request: Request,
    dolencia: str = Form(...),
    emoji: str = Form(""),
    categoria: str = Form(""),
    planta: str = Form(""),
    nombre_cientifico: str = Form(""),
    preparacion: str = Form(""),
    nota: str = Form(""),
    id: str = Form(""),
):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    if id:
        conn.execute(
            "UPDATE botiquin SET dolencia=?, emoji=?, categoria=?, planta=?, nombre_cientifico=?, preparacion=?, nota=? WHERE id=?",
            (dolencia, emoji, categoria, planta, nombre_cientifico, preparacion, nota, int(id)),
        )
        mensaje = "Dolencia actualizada"
    else:
        conn.execute(
            "INSERT INTO botiquin (dolencia, emoji, categoria, planta, nombre_cientifico, preparacion, nota) VALUES (?,?,?,?,?,?,?)",
            (dolencia, emoji, categoria, planta, nombre_cientifico, preparacion, nota),
        )
        mensaje = "Dolencia creada"
    conn.commit()
    conn.close()
    return RedirectResponse(f"/admin/botiquin?mensaje={mensaje}", status_code=303)


@app.post("/admin/botiquin/{id}/eliminar")
async def admin_botiquin_eliminar(request: Request, id: int):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    conn.execute("DELETE FROM botiquin WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin/botiquin?mensaje=Dolencia eliminada", status_code=303)


@app.get("/admin/usuarios")
async def admin_usuarios(request: Request, mensaje: Optional[str] = None):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    usuarios = conn.execute("SELECT * FROM usuarios_y_clientes ORDER BY id_usuario DESC").fetchall()
    conn.close()
    return templates.TemplateResponse("admin_usuarios.html", {
        "request": request, "settings": settings, "seccion": "usuarios",
        "usuarios": usuarios, "mensaje": mensaje,
    })


@app.post("/admin/usuarios/guardar")
async def admin_usuarios_guardar(
    request: Request,
    nombre_completo: str = Form(...),
    celular: str = Form(""),
    email: str = Form(""),
    direccion_completa: str = Form(""),
    ciudad_prov_pais: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    id_usuario: str = Form(""),
):
    if not _admin_ok(request): return _redir_login()
    lat = float(latitud) if latitud else None
    lon = float(longitud) if longitud else None
    conn = get_db()
    if id_usuario:
        conn.execute(
            "UPDATE usuarios_y_clientes SET nombre_completo=?, celular=?, email=?, direccion_completa=?, ciudad_prov_pais=?, latitud=?, longitud=? WHERE id_usuario=?",
            (nombre_completo, celular or None, email or None, direccion_completa or None, ciudad_prov_pais or None, lat, lon, int(id_usuario)),
        )
        mensaje = "Usuario actualizado"
    else:
        conn.execute(
            "INSERT INTO usuarios_y_clientes (nombre_completo, celular, email, direccion_completa, ciudad_prov_pais, latitud, longitud) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nombre_completo, celular or None, email or None, direccion_completa or None, ciudad_prov_pais or None, lat, lon),
        )
        mensaje = "Usuario creado"
    conn.commit()
    conn.close()
    return RedirectResponse(f"/admin/usuarios?mensaje={mensaje}", status_code=303)


@app.post("/admin/usuarios/{id_usuario}/eliminar")
async def admin_usuarios_eliminar(request: Request, id_usuario: int):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    conn.execute("DELETE FROM usuarios_y_clientes WHERE id_usuario=?", (id_usuario,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin/usuarios?mensaje=Usuario eliminado", status_code=303)


@app.get("/admin/consultas")
async def admin_consultas(request: Request, mensaje: Optional[str] = None):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    consultas = conn.execute("SELECT * FROM consultas ORDER BY fecha DESC").fetchall()
    conn.close()
    return templates.TemplateResponse("admin_consultas.html", {
        "request": request, "settings": settings, "consultas": consultas, "mensaje": mensaje,
    })


@app.post("/admin/consultas/{id}/eliminar")
async def admin_consultas_eliminar(request: Request, id: int):
    if not _admin_ok(request): return _redir_login()
    conn = get_db()
    conn.execute("DELETE FROM consultas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/admin/consultas?mensaje=Consulta eliminada", status_code=303)
