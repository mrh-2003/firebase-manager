import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Firebase DB Manager",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: #2a2a3d;
    --accent: #ff6b35;
    --accent2: #f7c59f;
    --green: #39d353;
    --blue: #58a6ff;
    --purple: #bc8cff;
    --red: #ff6b6b;
    --yellow: #ffd60a;
    --text: #e8e8f0;
    --muted: #6e6e8a;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'Syne', sans-serif;
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * { color: var(--text) !important; }

h1, h2, h3, h4 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    color: var(--text) !important;
}

.stButton > button {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    padding: 0.4rem 1.2rem !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: var(--accent2) !important;
    transform: translateY(-1px) !important;
}

.stTextInput input, .stTextArea textarea {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stSelectbox > div > div {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}

.result-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    white-space: pre-wrap;
    max-height: 500px;
    overflow-y: auto;
}

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 4px;
}

.badge-select { background: #1a3a5c; color: var(--blue); border: 1px solid var(--blue); }
.badge-insert { background: #1a3d2a; color: var(--green); border: 1px solid var(--green); }
.badge-update { background: #3d2a1a; color: var(--yellow); border: 1px solid var(--yellow); }
.badge-delete { background: #3d1a1a; color: var(--red); border: 1px solid var(--red); }
.badge-copy { background: #2a1a3d; color: var(--purple); border: 1px solid var(--purple); }

.doc-section {
    background: var(--surface2);
    border-left: 3px solid var(--accent);
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 0.6rem 0;
}

.doc-section code {
    background: var(--surface);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent2);
}

.doc-section pre {
    background: var(--surface);
    padding: 0.7rem 1rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent2);
    overflow-x: auto;
    margin: 0.4rem 0;
}

.success-msg {
    background: #0d2818;
    border: 1px solid var(--green);
    color: var(--green);
    padding: 0.6rem 1rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.error-msg {
    background: #2d0d0d;
    border: 1px solid var(--red);
    color: var(--red);
    padding: 0.6rem 1rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.info-msg {
    background: #0d1a2d;
    border: 1px solid var(--blue);
    color: var(--blue);
    padding: 0.6rem 1rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.warn-box {
    background: #2d2200;
    border: 1px solid var(--yellow);
    color: var(--yellow);
    padding: 0.5rem 0.9rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    margin: 0.4rem 0;
}

.stMarkdown p { color: var(--text); }
.stMarkdown code {
    background: var(--surface2);
    color: var(--accent2);
    font-family: 'JetBrains Mono', monospace;
}

hr { border-color: var(--border) !important; }

[data-testid="stExpander"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

PROJECTS_FILE = "projects.json"

OPERATORS = ["==", "!=", "<", "<=", ">", ">=", "in", "not-in", "array_contains", "array_contains_any"]

OPERATOR_MAP = {op: op for op in OPERATORS}

def load_projects():
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE) as f:
            return json.load(f)
    return {}

def save_projects(projects):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=2)

def get_firebase_app(project_name, config):
    app_name = f"app_{project_name}"
    try:
        return firebase_admin.get_app(app_name)
    except ValueError:
        try:
            cred = credentials.Certificate(config)
            return firebase_admin.initialize_app(cred, name=app_name)
        except Exception as e:
            st.error(f"Error conectando: {e}")
            return None

def get_db(project_name, projects):
    config = projects.get(project_name, {}).get("config")
    if not config:
        return None
    app = get_firebase_app(project_name, config)
    if app:
        return firestore.client(app)
    return None

def parse_value(val):
    if val is None:
        return None
    if isinstance(val, str):
        s = val.strip()
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        if s.lower() in ("null", "none"):
            return None
        try:
            return int(s)
        except:
            pass
        try:
            return float(s)
        except:
            pass
        try:
            return json.loads(s)
        except:
            pass
    return val

def apply_where(query, where_clauses):
    for clause in where_clauses:
        field = clause.get("field", "").strip()
        op = clause.get("op", "==")
        value = clause.get("value")
        if not field:
            continue
        value = parse_value(value)
        query = query.where(filter=firestore.FieldFilter(field, op, value))
    return query

def serialize_value(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: serialize_value(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [serialize_value(i) for i in v]
    return v

def serialize_doc(doc):
    data = doc.to_dict()
    return serialize_value(data) if data else {}

def init_where_keys(prefix, count):
    for i in range(count):
        for suffix, default in [(f"{prefix}_wf_{i}", ""), (f"{prefix}_wo_{i}", "=="), (f"{prefix}_wv_{i}", "")]:
            if suffix not in st.session_state:
                st.session_state[suffix] = default

def render_where_builder(prefix):
    count_key = f"{prefix}_where_count"
    if count_key not in st.session_state:
        st.session_state[count_key] = 1

    count = st.session_state[count_key]
    init_where_keys(prefix, count)

    clauses = []
    for i in range(count):
        fk = f"{prefix}_wf_{i}"
        ok = f"{prefix}_wo_{i}"
        vk = f"{prefix}_wv_{i}"

        cols = st.columns([3, 2, 3, 1])
        field = cols[0].text_input(
            "Campo", key=fk,
            placeholder="ej: status  /  items.tipo",
            help="Para filtrar dentro de un array de objetos usa notación punto: arrayField.campo"
        )
        cur_op = st.session_state.get(ok, "==")
        op_idx = OPERATORS.index(cur_op) if cur_op in OPERATORS else 0
        op = cols[1].selectbox("Op", OPERATORS, index=op_idx, key=ok)
        val = cols[2].text_input(
            "Valor", key=vk,
            placeholder='ej: activo  /  ["a","b"]  /  true',
            help='String: activo | Array: ["x","y"] | Bool: true/false | Null: null'
        )
        if cols[3].button("✕", key=f"{prefix}_rm_{i}"):
            if st.session_state[count_key] > 1:
                for j in range(i, st.session_state[count_key] - 1):
                    st.session_state[f"{prefix}_wf_{j}"] = st.session_state.get(f"{prefix}_wf_{j+1}", "")
                    st.session_state[f"{prefix}_wo_{j}"] = st.session_state.get(f"{prefix}_wo_{j+1}", "==")
                    st.session_state[f"{prefix}_wv_{j}"] = st.session_state.get(f"{prefix}_wv_{j+1}", "")
                st.session_state[count_key] -= 1
                st.rerun()

        if field.strip():
            clauses.append({"field": field.strip(), "op": op, "value": val})

    if st.button("＋ Agregar filtro WHERE", key=f"{prefix}_add_where"):
        st.session_state[count_key] += 1
        st.rerun()

    return clauses

if "projects" not in st.session_state:
    st.session_state.projects = load_projects()
if "active_project" not in st.session_state:
    st.session_state.active_project = None
if "query_result" not in st.session_state:
    st.session_state.query_result = None
if "result_msg" not in st.session_state:
    st.session_state.result_msg = None

with st.sidebar:
    st.markdown("## 🔥 Firebase Manager")
    st.markdown("---")
    menu = st.radio("Navegación", ["Consultas", "Proyectos", "Documentación"], label_visibility="collapsed")

if menu == "Proyectos":
    st.markdown("## ⚙️ Gestor de Proyectos")
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### Proyectos registrados")
        if not st.session_state.projects:
            st.markdown('<div class="info-msg">Sin proyectos. Agrega uno →</div>', unsafe_allow_html=True)
        else:
            for pname in list(st.session_state.projects.keys()):
                label = f"▶ {pname}" if st.session_state.active_project == pname else pname
                if st.button(label, key=f"sel_{pname}", use_container_width=True):
                    st.session_state.active_project = pname
                    st.rerun()

            if st.session_state.active_project:
                st.markdown("---")
                st.markdown(f"**Activo:** `{st.session_state.active_project}`")
                if st.button("🗑 Eliminar proyecto activo", type="secondary"):
                    del st.session_state.projects[st.session_state.active_project]
                    save_projects(st.session_state.projects)
                    st.session_state.active_project = None
                    st.rerun()

    with col2:
        st.markdown("### Agregar / Editar Proyecto")
        pname_input = st.text_input("Nombre del proyecto", placeholder="mi-proyecto-prod", key="proj_name_input")
        st.markdown("**Firebase Service Account JSON**")
        json_input = st.text_area(
            "JSON",
            height=300,
            placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  "private_key": "...",\n  ...\n}',
            label_visibility="collapsed",
            key="proj_json_input"
        )
        if st.button("💾 Guardar proyecto"):
            if pname_input and json_input:
                try:
                    config = json.loads(json_input)
                    if config.get("type") != "service_account":
                        st.error("El JSON debe ser un Service Account de Firebase.")
                    else:
                        st.session_state.projects[pname_input] = {"config": config}
                        save_projects(st.session_state.projects)
                        st.session_state.active_project = pname_input
                        st.success(f"Proyecto '{pname_input}' guardado.")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("JSON inválido.")
            else:
                st.warning("Completa nombre y JSON.")

elif menu == "Documentación":
    st.markdown("## 📖 Documentación")
    st.markdown("---")

    st.markdown("""
<div class="doc-section">
<b>🔧 Configuración inicial</b><br><br>
1. Ve a <b>Proyectos</b> → Agrega tu proyecto pegando el JSON de Service Account.<br>
2. Descarga el JSON desde: <i>Firebase Console → Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada</i>.<br>
3. Selecciona el proyecto activo en <b>Consultas</b> antes de ejecutar.<br>
4. Puedes registrar múltiples proyectos y cambiar entre ellos libremente.
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔵 SELECT — Consultar documentos")
    st.markdown("""
<div class="doc-section">
Trae documentos de una colección con filtros opcionales, ordenamiento y límite.<br><br>
<b>Campos:</b><br>
• <b>Colección:</b> nombre de la colección (ej: <code>usuarios</code>)<br>
• <b>Límite:</b> máximo de documentos a retornar (1–5000)<br>
• <b>Ordenar por:</b> campo para ordenar resultados (ej: <code>createdAt</code>)<br>
• <b>WHERE:</b> filtros encadenados opcionales<br><br>
<b>Ejemplos de WHERE:</b>
<pre>Campo: status          Op: ==               Valor: activo
Campo: edad            Op: >=               Valor: 18
Campo: pais            Op: in               Valor: ["MX","PE","CO"]
Campo: pais            Op: not-in           Valor: ["US","CA"]
Campo: roles           Op: array_contains      Valor: admin
Campo: tags            Op: array_contains_any  Valor: ["nuevo","vip"]</pre>
Los resultados se muestran como JSON y se pueden descargar.
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗂 WHERE en arrays de objetos (campo anidado)")
    st.markdown("""
<div class="doc-section">
Firestore permite filtrar por campos dentro de un array de objetos usando <b>notación punto</b>.<br><br>
<b>Estructura del documento:</b>
<pre>{
  "nombre": "Ana",
  "suscripciones": [
    { "plan": "premium", "activo": true,  "meses": 12 },
    { "plan": "basico",  "activo": false, "meses": 1  }
  ]
}</pre>

<b>Filtrar documentos donde algún objeto del array tenga <code>plan == "premium"</code>:</b>
<pre>Campo: suscripciones.plan    Op: array_contains    Valor: premium</pre>

<b>Filtrar donde <code>activo</code> sea <code>true</code> en algún elemento:</b>
<pre>Campo: suscripciones.activo    Op: array_contains    Valor: true</pre>

<b>Filtrar donde <code>meses</code> esté entre varios valores:</b>
<pre>Campo: suscripciones.meses    Op: array_contains_any    Valor: [1,3,6]</pre>

<div class="warn-box">⚠ Limitación de Firestore: la notación punto en array_contains solo funciona si Firestore tiene un índice compuesto creado para ese campo. Si te aparece un error de índice, el mensaje incluirá un link directo para crearlo en la consola de Firebase.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🟢 INSERT — Insertar documento")
    st.markdown("""
<div class="doc-section">
Crea un nuevo documento en la colección especificada.<br><br>
<b>Con ID autogenerado:</b>
<pre>Colección: usuarios
ID: (vacío)
Datos:
{
  "nombre": "Carlos",
  "email": "carlos@email.com",
  "edad": 28,
  "roles": ["user", "editor"],
  "activo": true,
  "metadata": { "origen": "web", "version": 2 }
}</pre>
<b>Con ID manual:</b>
<pre>Colección: usuarios
ID: usuario-carlos-001
Datos: { "nombre": "Carlos" }</pre>
Si el ID ya existe, el documento se <b>sobreescribe completo</b>.
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🟡 UPDATE — Actualizar documentos")
    st.markdown("""
<div class="doc-section">
Actualiza campos específicos de los documentos que coincidan con el WHERE. Es una actualización <b>parcial</b>: los campos no incluidos en el JSON no se tocan.<br><br>
<b>Cambiar status para usuarios de MX:</b>
<pre>Colección: usuarios
WHERE: pais == MX
Datos: { "status": "inactivo", "updatedAt": "2025-04-01" }</pre>

<b>Actualizar campo anidado:</b>
<pre>Datos: { "metadata.version": 3 }</pre>

<b>Actualizar varios campos a la vez:</b>
<pre>Datos: {
  "status": "activo",
  "plan": "premium",
  "updatedAt": "2025-04-01",
  "intentos": 0
}</pre>
<div class="warn-box">⚠ Sin WHERE se actualizan TODOS los documentos de la colección.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔴 DELETE — Eliminar documentos")
    st.markdown("""
<div class="doc-section">
Elimina todos los documentos que coincidan con el WHERE.<br><br>
<b>Eliminar por ID exacto:</b>
<pre>Colección: usuarios
WHERE: __name__ == usuario-carlos-001</pre>

<b>Eliminar por campo:</b>
<pre>Colección: usuarios
WHERE: status == eliminado</pre>

<b>Eliminar donde el array contiene un valor:</b>
<pre>Colección: pedidos
WHERE: tags    array_contains    cancelado</pre>

<b>Eliminar con múltiples condiciones:</b>
<pre>WHERE 1: pais   ==      MX
WHERE 2: activo ==      false</pre>

<div class="warn-box">⚠ Sin WHERE se eliminan TODOS los documentos. Siempre se requiere confirmar con la casilla antes de ejecutar. La eliminación usa batches de 500 para respetar los límites de Firestore.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🟣 COPIAR — Entre proyectos")
    st.markdown("""
<div class="doc-section">
Copia documentos de una colección de un proyecto a otro. Los IDs se preservan. Si el documento ya existe en destino, se sobreescribe.<br><br>
<b>Copiar usuarios activos de producción a staging:</b>
<pre>Origen: mi-app-prod
Destino: mi-app-staging
Colección: usuarios
WHERE: activo == true
Colección destino: usuarios_backup
Límite: 500</pre>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔑 Referencia de operadores")
    st.markdown("""
<div class="doc-section">
<table style="width:100%; font-family: JetBrains Mono, monospace; font-size: 0.78rem; border-collapse: collapse;">
<tr style="border-bottom: 1px solid #2a2a3d;">
  <th style="text-align:left; padding: 6px 10px; color: #ff6b35;">Operador</th>
  <th style="text-align:left; padding: 6px 10px; color: #ff6b35;">Descripción</th>
  <th style="text-align:left; padding: 6px 10px; color: #ff6b35;">Ejemplo de valor</th>
</tr>
<tr style="border-bottom:1px solid #1a1a26;"><td style="padding:5px 10px;">==</td><td style="padding:5px 10px;">Igual a</td><td style="padding:5px 10px;color:#f7c59f;">activo</td></tr>
<tr style="border-bottom:1px solid #1a1a26;"><td style="padding:5px 10px;">!=</td><td style="padding:5px 10px;">Diferente de</td><td style="padding:5px 10px;color:#f7c59f;">eliminado</td></tr>
<tr style="border-bottom:1px solid #1a1a26;"><td style="padding:5px 10px;">&lt;  &lt;=  &gt;  &gt;=</td><td style="padding:5px 10px;">Comparación numérica / string</td><td style="padding:5px 10px;color:#f7c59f;">18</td></tr>
<tr style="border-bottom:1px solid #1a1a26;"><td style="padding:5px 10px;">in</td><td style="padding:5px 10px;">El campo está dentro del array dado (máx 10 valores)</td><td style="padding:5px 10px;color:#f7c59f;">["MX","PE","CO"]</td></tr>
<tr style="border-bottom:1px solid #1a1a26;"><td style="padding:5px 10px;">not-in</td><td style="padding:5px 10px;">El campo NO está en el array (máx 10 valores)</td><td style="padding:5px 10px;color:#f7c59f;">["borrador","eliminado"]</td></tr>
<tr style="border-bottom:1px solid #1a1a26;"><td style="padding:5px 10px;">array_contains</td><td style="padding:5px 10px;">El array del doc contiene exactamente este valor</td><td style="padding:5px 10px;color:#f7c59f;">admin</td></tr>
<tr><td style="padding:5px 10px;">array_contains_any</td><td style="padding:5px 10px;">El array contiene alguno de los valores dados</td><td style="padding:5px 10px;color:#f7c59f;">["admin","editor"]</td></tr>
</table>
<br>
<b>Tipos de valores aceptados en el campo Valor:</b><br>
• String simple: <code>activo</code> &nbsp;(sin comillas)<br>
• String con espacios: <code>"mi valor"</code> &nbsp;(con comillas dobles)<br>
• Número entero: <code>18</code><br>
• Número decimal: <code>3.14</code><br>
• Booleano: <code>true</code> o <code>false</code><br>
• Nulo: <code>null</code><br>
• Array: <code>["a","b","c"]</code> &nbsp;(JSON válido)<br>
• Objeto JSON: <code>{"id": 1, "nombre": "X"}</code>
</div>
""", unsafe_allow_html=True)

elif menu == "Consultas":
    st.markdown("## 🔍 Consultas")

    if not st.session_state.projects:
        st.markdown('<div class="error-msg">⚠ No hay proyectos. Ve a Proyectos para agregar uno.</div>', unsafe_allow_html=True)
        st.stop()

    project_names = list(st.session_state.projects.keys())

    with st.sidebar:
        st.markdown("---")
        st.markdown("**Proyecto activo**")
        if st.session_state.active_project not in project_names:
            st.session_state.active_project = project_names[0]
        active = st.selectbox(
            "Proyecto",
            project_names,
            index=project_names.index(st.session_state.active_project),
            label_visibility="collapsed"
        )
        st.session_state.active_project = active

    tabs = st.tabs(["🔵 SELECT", "🟢 INSERT", "🟡 UPDATE", "🔴 DELETE", "🟣 COPIAR"])

    with tabs[0]:
        st.markdown("### SELECT — Consultar documentos")
        col1, col2 = st.columns([2, 1])
        collection = col1.text_input("Colección", placeholder="usuarios", key="sel_col")
        limit = col2.number_input("Límite", 1, 5000, 100, key="sel_limit")
        st.markdown("**WHERE** (opcional)")
        where_clauses = render_where_builder("sel")
        order_col = st.text_input("Ordenar por campo (opcional)", key="sel_order")

        if st.button("▶ Ejecutar SELECT"):
            if collection:
                db = get_db(st.session_state.active_project, st.session_state.projects)
                if db:
                    try:
                        query = db.collection(collection)
                        if where_clauses:
                            query = apply_where(query, where_clauses)
                        if order_col.strip():
                            query = query.order_by(order_col.strip())
                        query = query.limit(int(limit))
                        docs = query.stream()
                        results = []
                        for doc in docs:
                            d = serialize_doc(doc)
                            d["_id"] = doc.id
                            results.append(d)
                        st.session_state.query_result = results
                        st.session_state.result_msg = ("success", f"{len(results)} documento(s) encontrado(s)")
                    except Exception as e:
                        st.session_state.result_msg = ("error", str(e))
                        st.session_state.query_result = None
            else:
                st.warning("Indica la colección.")

        if st.session_state.result_msg:
            mtype, mtxt = st.session_state.result_msg
            if mtype == "success":
                st.markdown(f'<div class="success-msg">✓ {mtxt}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-msg">✗ {mtxt}</div>', unsafe_allow_html=True)

        if st.session_state.query_result is not None:
            st.markdown("**Resultados:**")
            result_json = json.dumps(st.session_state.query_result, indent=2, ensure_ascii=False, default=str)
            st.markdown(f'<div class="result-box">{result_json}</div>', unsafe_allow_html=True)
            st.download_button("⬇ Descargar JSON", result_json, file_name="resultado.json", mime="application/json")

    with tabs[1]:
        st.markdown("### INSERT — Insertar documento")
        col1, col2 = st.columns([2, 1])
        ins_col = col1.text_input("Colección", placeholder="usuarios", key="ins_col")
        ins_id = col2.text_input("ID del documento (vacío = autogenerar)", placeholder="doc-id-123", key="ins_id")
        ins_data = st.text_area(
            "Datos JSON",
            height=200,
            placeholder='{\n  "nombre": "Ana",\n  "edad": 30,\n  "roles": ["admin"],\n  "activo": true\n}',
            key="ins_data"
        )

        if st.button("▶ Ejecutar INSERT"):
            if ins_col and ins_data:
                db = get_db(st.session_state.active_project, st.session_state.projects)
                if db:
                    try:
                        data = json.loads(ins_data)
                        if ins_id.strip():
                            db.collection(ins_col).document(ins_id.strip()).set(data)
                            st.markdown(f'<div class="success-msg">✓ Documento insertado con ID: {ins_id.strip()}</div>', unsafe_allow_html=True)
                        else:
                            ref = db.collection(ins_col).add(data)
                            st.markdown(f'<div class="success-msg">✓ Documento insertado. ID autogenerado: {ref[1].id}</div>', unsafe_allow_html=True)
                    except json.JSONDecodeError:
                        st.markdown('<div class="error-msg">✗ JSON inválido</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="error-msg">✗ {e}</div>', unsafe_allow_html=True)
            else:
                st.warning("Indica colección y datos.")

    with tabs[2]:
        st.markdown("### UPDATE — Actualizar documentos")
        upd_col = st.text_input("Colección", placeholder="usuarios", key="upd_col")
        st.markdown("**WHERE** (selecciona qué documentos actualizar)")
        upd_where = render_where_builder("upd")
        upd_data = st.text_area(
            "Datos a actualizar (JSON parcial)",
            height=150,
            placeholder='{\n  "status": "inactivo",\n  "updatedAt": "2025-01-01"\n}',
            key="upd_data"
        )

        if st.button("▶ Ejecutar UPDATE"):
            if upd_col and upd_data:
                db = get_db(st.session_state.active_project, st.session_state.projects)
                if db:
                    try:
                        data = json.loads(upd_data)
                        query = db.collection(upd_col)
                        if upd_where:
                            query = apply_where(query, upd_where)
                        docs = list(query.stream())
                        if not docs:
                            st.markdown('<div class="info-msg">ℹ Sin documentos que coincidan.</div>', unsafe_allow_html=True)
                        else:
                            batch = db.batch()
                            for i, doc in enumerate(docs):
                                batch.update(doc.reference, data)
                                if (i + 1) % 500 == 0:
                                    batch.commit()
                                    batch = db.batch()
                            batch.commit()
                            st.markdown(f'<div class="success-msg">✓ {len(docs)} documento(s) actualizado(s)</div>', unsafe_allow_html=True)
                    except json.JSONDecodeError:
                        st.markdown('<div class="error-msg">✗ JSON inválido</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="error-msg">✗ {e}</div>', unsafe_allow_html=True)
            else:
                st.warning("Indica colección y datos a actualizar.")

    with tabs[3]:
        st.markdown("### DELETE — Eliminar documentos")
        del_col = st.text_input("Colección", placeholder="usuarios", key="del_col")
        st.markdown("**WHERE** (filtra qué eliminar — sin filtro elimina TODO)")
        del_where = render_where_builder("del")
        confirm = st.checkbox("⚠ Confirmo que quiero eliminar los documentos seleccionados", key="del_confirm")

        if st.button("▶ Ejecutar DELETE", type="primary"):
            if del_col and confirm:
                db = get_db(st.session_state.active_project, st.session_state.projects)
                if db:
                    try:
                        query = db.collection(del_col)
                        if del_where:
                            query = apply_where(query, del_where)
                        docs = list(query.stream())
                        if not docs:
                            st.markdown('<div class="info-msg">ℹ Sin documentos que coincidan.</div>', unsafe_allow_html=True)
                        else:
                            batch = db.batch()
                            for i, doc in enumerate(docs):
                                batch.delete(doc.reference)
                                if (i + 1) % 500 == 0:
                                    batch.commit()
                                    batch = db.batch()
                            batch.commit()
                            st.markdown(f'<div class="success-msg">✓ {len(docs)} documento(s) eliminado(s)</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="error-msg">✗ {e}</div>', unsafe_allow_html=True)
            elif not confirm:
                st.warning("Marca la casilla de confirmación.")
            else:
                st.warning("Indica la colección.")

    with tabs[4]:
        st.markdown("### COPIAR — Entre proyectos")

        if len(st.session_state.projects) < 2:
            st.markdown('<div class="info-msg">ℹ Necesitas al menos 2 proyectos registrados para usar esta función.</div>', unsafe_allow_html=True)
        else:
            col1, col2 = st.columns(2)
            src_proj = col1.selectbox("Proyecto origen", project_names, key="copy_src")
            dst_options = [p for p in project_names if p != src_proj]
            dst_proj = col2.selectbox("Proyecto destino", dst_options, key="copy_dst")

            copy_col = st.text_input("Colección a copiar", placeholder="usuarios", key="copy_col")
            st.markdown("**WHERE** (opcional, para copiar subconjunto)")
            copy_where = render_where_builder("copy")

            col3, col4 = st.columns([2, 1])
            dst_col_name = col3.text_input("Nombre colección en destino (vacío = mismo nombre)", key="copy_dst_col")
            copy_limit = col4.number_input("Límite", 1, 5000, 500, key="copy_limit")

            if st.button("▶ Ejecutar COPIA"):
                if copy_col:
                    db_src = get_db(src_proj, st.session_state.projects)
                    db_dst = get_db(dst_proj, st.session_state.projects)
                    if db_src and db_dst:
                        try:
                            query = db_src.collection(copy_col)
                            if copy_where:
                                query = apply_where(query, copy_where)
                            query = query.limit(int(copy_limit))
                            docs = list(query.stream())
                            if not docs:
                                st.markdown('<div class="info-msg">ℹ Sin documentos que coincidan.</div>', unsafe_allow_html=True)
                            else:
                                dst_collection = dst_col_name.strip() or copy_col
                                batch = db_dst.batch()
                                for i, doc in enumerate(docs):
                                    data = serialize_doc(doc)
                                    ref = db_dst.collection(dst_collection).document(doc.id)
                                    batch.set(ref, data)
                                    if (i + 1) % 500 == 0:
                                        batch.commit()
                                        batch = db_dst.batch()
                                batch.commit()
                                st.markdown(f'<div class="success-msg">✓ {len(docs)} documento(s) copiado(s): <b>{src_proj}/{copy_col}</b> → <b>{dst_proj}/{dst_collection}</b></div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.markdown(f'<div class="error-msg">✗ {e}</div>', unsafe_allow_html=True)
                else:
                    st.warning("Indica la colección.")