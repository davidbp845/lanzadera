import html
import json
import os
import signal
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

import actividad
import demo
import github
import graficos
import ram
import textos
import vps
from config import paths
from config.proyectos import cargar as cargar_registro
from config.vps import cargar as cargar_servidores

MENU = ["Lanzadera", "Enlaces", "VPS", "Local"]
# Demo pública de solo lectura (ADR-0010): nada de lo que consulta el sistema se ejecuta;
# cada función que lo haría devuelve los datos de demo.py.
DEMO = paths.demo()
REPO_PUBLICO = "https://github.com/davidbp845/lanzadera"


def _idioma() -> str:
    # El selector del lateral guarda el idioma en session_state; antes de pintarlo, el de por defecto.
    return st.session_state.get("idioma") or paths.idioma()


def t(clave: str, **huecos) -> str:
    return textos.texto(_idioma(), clave, **huecos)


def _numero(texto: str) -> str:
    # Los números se formatean con coma decimal; en inglés, con punto.
    return texto if _idioma() == "es" else texto.replace(",", ".")


# Todas las páginas en ancho: tablas, rejilla del VPS, gráficos y los enlaces completos.
st.set_page_config(page_title=t("pagina.Lanzadera"), page_icon="🏠", layout="wide")

# El registro de proyectos y los enlaces son datos del contenedor (../datos), no
# código (ADR-0001); aquí solo se cargan.
REGISTRO = cargar_registro()
PROYECTOS = REGISTRO["proyectos"]
HERUKA_FLOW = REGISTRO["heruka_flow"]
INTENTOS_ESPERA_NEGOCIOS = REGISTRO["intentos_negocios"]
HERUKA_LIFE_SINGLE = REGISTRO["heruka_life_single"]
# Sin `[negocios]` en el registro no hay filas de negocios ni nada de heruka-flow en el panel.
CON_NEGOCIOS = HERUKA_FLOW is not None
# Carpetas de las que se leen GitHub y la actividad: los proyectos y, si lo hay, heruka-flow.
RUTAS_REPOS = [p["path"] for p in PROYECTOS] + ([HERUKA_FLOW] if CON_NEGOCIOS else [])
ENLACES_CSV = paths.enlaces()
# En la demo, el GitHub de cada proyecto se busca por su slug en demo/estado.toml.
SLUG_POR_RUTA = {str(p["path"]): p["slug"] for p in PROYECTOS} | (
    {str(HERUKA_FLOW): "negocios"} if CON_NEGOCIOS else {}
)


def _puerto_activo(puerto: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    if DEMO:
        return demo.puerto_activo(puerto)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, puerto)) == 0


def esta_activo(proyecto: dict) -> bool:
    return _puerto_activo(proyecto["puerto"])


def _esperar_puerto(puerto: int, activo_esperado: bool, intentos: int = 20, espera: float = 0.5) -> None:
    # Da tiempo a que streamlit termine de arrancar/parar antes de que el
    # siguiente rerun pinte el semáforo; si no, el rerun ve el estado viejo.
    for _ in range(intentos):
        if _puerto_activo(puerto) == activo_esperado:
            return
        time.sleep(espera)


def iniciar(proyecto: dict) -> None:
    # Los interruptores ya salen deshabilitados en la demo; esto es por si un fallo de la UI llegara aquí.
    if DEMO:
        return
    # "env" es un override puntual (p. ej. un CONFIG_PATH propio) sobre el
    # entorno heredado, no un reemplazo — igual que dotenv, que nunca pisa
    # una variable ya presente en el proceso.
    env = {**os.environ, **proyecto.get("env", {})}
    subprocess.Popen(
        proyecto["cmd"],
        cwd=proyecto["path"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    # Por defecto _esperar_puerto espera como mucho 10s (intentos=20 x
    # espera=0.5s) — de sobra para la mayoría, pero Heruka Consola tarda
    # ~14s en que el backend LangGraph termine de importar el grafo (ver
    # comentario en su entrada de PROYECTOS). Sin este override, el toggle
    # vuelve a "parado" antes de que el puerto responda de verdad.
    intentos = proyecto.get("intentos_espera_inicio", 20)
    _esperar_puerto(proyecto["puerto"], activo_esperado=True, intentos=intentos)
    # Proyectos multi-servicio (p. ej. Heruka Life) listan cada puerto en
    # "enlaces" para mostrar varios enlaces en la UI — pero eso no
    # garantiza que "puerto" sea el último en estar listo: el panel de
    # Heruka Life abre su puerto casi al instante mientras frontend/backend
    # tardan bastante más (visto en logs/{frontend,backend}.log: ~12s y
    # ~36s respectivamente, el backend por el import pesado de
    # sentence-transformers para los embeddings del RAG). Sin esto, el
    # toggle se pone verde y los enlaces aparecen antes de que frontend/
    # backend respondan de verdad.
    for _etiqueta, puerto_enlace, *_resto in proyecto.get("enlaces", []):
        if puerto_enlace != proyecto["puerto"]:
            _esperar_puerto(puerto_enlace, activo_esperado=True, intentos=intentos)


def detener(proyecto: dict) -> None:
    if DEMO:
        return
    cmd_detener = proyecto.get("cmd_detener")
    if cmd_detener is not None:
        # Proyectos con su propio script de parada (p. ej. dev_down.sh de
        # Heruka Life, pensado para el caso de varios procesos arrancados
        # en background): se le delega la parada en vez de matar por puerto.
        subprocess.run(
            cmd_detener,
            check=False,
            cwd=proyecto["path"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _esperar_puerto(proyecto["puerto"], activo_esperado=False)
        return

    pid = ram.pid_en_puerto(proyecto["puerto"])
    if pid is None:
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    _esperar_puerto(proyecto["puerto"], activo_esperado=False)


def cargar_enlaces() -> pd.DataFrame:
    if not ENLACES_CSV.exists():
        return pd.DataFrame(columns=["descripcion", "enlace", "etiquetas"])
    df = pd.read_csv(ENLACES_CSV).fillna("")
    if "etiquetas" not in df.columns:
        df["etiquetas"] = ""
    return df


# Proyecto · puerto · estado · enlaces · GitHub · interruptor (cabecera y filas).
# GitHub, la más ancha: repositorio · tablero y cinco pastillas tienen que caber en una línea.
COLUMNAS_LANZADERA = [2.4, 0.8, 1.2, 1.6, 4, 0.6]


@st.cache_data(ttl=3600)
def _github(path: str) -> tuple[str | None, tuple[str, int] | None]:
    # Leer git y CLAUDE.md de cada proyecto en cada rerun (cada interruptor) sobra: cambian muy poco.
    if DEMO:
        return demo.repositorio_y_tablero(SLUG_POR_RUTA.get(path, ""))
    return github.repositorio(Path(path)), github.tablero_id(Path(path), paths.raiz_data())


@st.cache_data(ttl=600, show_spinner=False)
def _recuentos_en_cache(tableros: tuple[tuple[str, int], ...]) -> dict[tuple[str, int], dict[str, int] | None]:
    # Una consulta por tablero, todas a la vez (~0,6 s cada una); el buscador no las repite.
    consultar = demo.recuento if DEMO else github.recuento
    with ThreadPoolExecutor() as hilos:
        return dict(zip(tableros, hilos.map(lambda tablero: consultar(*tablero), tableros), strict=True))


def _recuentos(tableros: tuple[tuple[str, int], ...]) -> dict[tuple[str, int], dict[str, int] | None]:
    recuentos = _recuentos_en_cache(tableros)
    # Un fallo de `gh` (sin red al arrancar) no se guarda: el siguiente rerun vuelve a consultar.
    if None in recuentos.values():
        _recuentos_en_cache.clear(tableros)
    return recuentos


def _tableros() -> tuple[tuple[str, int], ...]:
    return tuple(sorted({t for ruta in RUTAS_REPOS if (t := _github(str(ruta))[1])}))


# Color de cada estado del tablero, en el orden de github.ESTADOS, el mismo que el del
# gráfico de issues; un cero va en gris.
COLORES_ESTADO = graficos.COLORES_ESTADO
GRIS_ESTADO = "#8a8a8a"


def _pastillas(cuenta: dict[str, int]) -> str:
    # HTML propio: las pastillas de markdown (:color-badge[]) no dejan cambiar tamaño ni ancho.
    # Texto oscuro sobre el color: amarillo y aqua no llegan a 3:1 como color de texto.
    return "".join(
        f'<span title="{estado}" style="display:inline-block;min-width:2.1em;margin-left:0.3em;'
        f"padding:0.1em 0.45em;border-radius:0.6em;text-align:center;font-weight:600;"
        f'font-variant-numeric:tabular-nums;color:{texto};background:{fondo}">{cuenta[estado]}</span>'
        for estado, color in zip(github.ESTADOS, COLORES_ESTADO, strict=True)
        for texto, fondo in [("#31333F", f"{color}4d") if cuenta[estado] else (GRIS_ESTADO, "#8a8a8a1a")]
    )


# st.text_input solo avisa al pulsar Intro o salir del campo; este buscador manda el
# texto mientras se escribe (con una pausa corta para no repintar en cada tecla), como
# el de Enlaces, que filtra en el navegador pero no puede alojar los st.toggle.
_BUSCADOR = st.components.v2.component(
    "buscador_lanzadera",
    html="""
<input type="search" autocomplete="off" />
""",
    css="""
input {
  box-sizing: border-box;
  width: 100%;
  height: 2.5rem;
  padding: 0 0.75rem;
  font: inherit;
  color: var(--st-text-color);
  background: var(--st-secondary-background-color);
  border: 1px solid transparent;
  border-radius: var(--st-base-radius);
  outline: none;
}
input:focus {
  border-color: var(--st-primary-color);
}
""",
    js="""
export default function (component) {
  const { data, parentElement, setStateValue } = component
  const input = parentElement.querySelector("input")
  if (!input) return
  input.placeholder = data.placeholder
  // Solo se reescribe si cambia desde Python, para no pelear con el cursor.
  if (document.activeElement !== input && input.value !== data.value) input.value = data.value
  let espera
  input.oninput = () => {
    clearTimeout(espera)
    espera = setTimeout(() => setStateValue("value", input.value), 250)
  }
  return () => clearTimeout(espera)
}
""",
)


def _buscar(key: str, placeholder: str) -> str:
    valor = st.session_state.get(key, {}).get("value", "")
    resultado = _BUSCADOR(
        key=key,
        data={"value": valor, "placeholder": placeholder},
        default={"value": valor},
        on_value_change=lambda: None,
    )
    return resultado.value or ""


ESTADOS = ["activo", "parado"]
# Píldora de tipo: solo las filas de heruka-flow multi-tenant o single (ADR-0009).
NEGOCIOS = "Negocios"


def _sin_enlace(texto: str, explicacion: str) -> str:
    # En la demo, los enlaces a localhost o a tableros ficticios no llevarían a ningún sitio.
    return (
        f'<span title="{html.escape(explicacion)}" style="color:#9a9ca8;border-bottom:1px dotted #9a9ca8">'
        f"{html.escape(texto)}</span>"
    )


def _pintar_github(columna, path: Path) -> None:
    repo, tablero = _github(str(path))
    if DEMO:
        partes = [_sin_enlace(t("repositorio"), t("demo.github")) if repo else None]
        if tablero:
            partes.append(_sin_enlace(t("tablero"), t("demo.github")))
    else:
        partes = [f'<a href="{html.escape(repo)}" target="_blank">{t("repositorio")}</a>' if repo else None]
        if tablero:
            url = f"https://github.com/users/{tablero[0]}/projects/{tablero[1]}"
            partes.append(f'<a href="{url}" target="_blank">{t("tablero")}</a>')
    if not any(partes):
        columna.markdown(":gray[—]")
        return
    # Enlaces y pastillas, cada uno sin partir: en una línea si caben y, si no, las
    # pastillas bajan enteras en vez de pisar el interruptor.
    texto = f'<span style="white-space:nowrap">{" · ".join(p for p in partes if p)}</span>'
    if tablero and (cuenta := _recuentos(_tableros()).get(tablero)):
        texto += f'<span style="white-space:nowrap">{_pastillas(cuenta)}</span>'
    columna.markdown(f"<div>{texto}</div>", unsafe_allow_html=True)


def _colorear_pastillas(tipos: list[str]) -> None:
    # st.pills no admite un color por opción: CSS por posición sobre los botones del grupo.
    # Las de tipo (carpetas y Negocios) van con la paleta de Enlaces; las de estado, sin tocar.
    reglas = []
    for i, color in enumerate(PALETA_CATEGORIAS[: len(tipos)], start=1):
        boton = f".st-key-filtros_lanzadera button:nth-child({i})"
        reglas.append(f"{boton} {{ color: {color}; border-color: {color}; background: {color}14; }}")
        # aria-pressed en las de selección múltiple, aria-checked en las de una sola.
        reglas.append(
            f'{boton}[aria-pressed="true"], {boton}[aria-checked="true"] {{ color: #fff; background: {color}; }}'
        )
    # Las de orden, con el color de su estado en las pastillas del recuento y, como ellas,
    # texto oscuro: amarillo y aqua no se leen como color de texto.
    for i, color in enumerate(COLORES_ESTADO, start=1):
        boton = f".st-key-orden_lanzadera button:nth-child({i})"
        reglas.append(f"{boton} {{ color: #31333F; border-color: {color}; background: {color}1f; }}")
        # aria-pressed en las de selección múltiple, aria-checked en las de una sola.
        reglas.append(
            f'{boton}[aria-pressed="true"], {boton}[aria-checked="true"] {{ background: {color}80; font-weight: 600; }}'
        )
    st.html("<style>\n" + "\n".join(reglas) + "\n</style>")


def _carpeta_raiz(proyecto: dict) -> str:
    return proyecto["ruta"].split("/", 1)[0]


def _pintar_enlaces(columna, enlaces: list[tuple[str, str]]) -> None:
    if DEMO:
        columna.markdown(" · ".join(_sin_enlace(e, t("demo.enlace")) for e, _url in enlaces), unsafe_allow_html=True)
    else:
        columna.markdown(" · ".join(f"[{etiqueta}]({url})" for etiqueta, url in enlaces))


def _interruptor(key: str, on_change, **valor) -> None:
    st.toggle(
        "activo",
        key=key,
        on_change=on_change,
        label_visibility="collapsed",
        disabled=DEMO,
        help=t("demo.deshabilitado") if DEMO else None,
        **valor,
    )


def _render_proyecto(proyecto: dict, activo: bool) -> None:
    nombre, puerto, estado, enlaces, enlaces_github, interruptor = st.columns(
        COLUMNAS_LANZADERA, vertical_alignment="center"
    )
    nombre.markdown(f"**{proyecto['nombre']}**")
    puerto.markdown(str(proyecto["puerto"]))

    if proyecto["cmd"] is None:
        estado.markdown(t("estado.activa"))
    else:
        estado.markdown(t("estado.activo") if activo else t("estado.parado"))

    if activo and proyecto["cmd"] is not None:
        lista = proyecto.get("enlaces", [(t("enlace.abrir"), proyecto["puerto"])])
        _pintar_enlaces(
            enlaces,
            [
                (etiqueta, f"http://localhost:{puerto_enlace}{resto[0] if resto else ''}")
                for etiqueta, puerto_enlace, *resto in lista
            ],
        )

    _pintar_github(enlaces_github, proyecto["path"])

    with interruptor:
        if proyecto["cmd"] is None:
            st.caption(t("esta_app"))
        else:
            key = f"switch_{proyecto['slug']}"

            def _on_change(proyecto=proyecto, key=key):
                if st.session_state[key]:
                    iniciar(proyecto)
                else:
                    detener(proyecto)

            _interruptor(key, _on_change, value=activo)


# El buscador de la Lanzadera relanza la página tras cada pausa al escribir y --listar
# puede tardar segundos; se invalida al arrancar o parar negocios (ADR-0009).
@st.cache_data(ttl=60, show_spinner=False)
def listar_negocios() -> list[dict]:
    if DEMO:
        return demo.listar_negocios()
    try:
        salida = subprocess.run(
            ["./scripts/dev_up.sh", "--listar"],
            cwd=HERUKA_FLOW,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    negocios = []
    for linea in salida.splitlines():
        partes = linea.split("\t")
        if len(partes) == 4:
            negocio_id, front, panel, api = partes
            negocios.append({"id": negocio_id, "front": int(front), "panel": int(panel), "api": int(api)})
    return negocios


def _puertos_negocio(negocio: dict) -> list[int]:
    return [negocio["front"], negocio["panel"], negocio["api"]]


def negocio_activo(negocio: dict) -> bool:
    return any(_puerto_activo(p) for p in _puertos_negocio(negocio))


def detener_negocios(negocios: list[dict]) -> None:
    if DEMO:
        return
    # Un solo backend (:8000) sirve a todos los negocios arrancados: parar
    # uno implica parar el stack entero y volver a levantar los demás.
    subprocess.run(
        ["./scripts/dev_down.sh"],
        cwd=HERUKA_FLOW,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for negocio in negocios:
        for puerto in _puertos_negocio(negocio):
            _esperar_puerto(puerto, activo_esperado=False)


def iniciar_negocios(seleccion: list[dict], todos: list[dict]) -> None:
    if DEMO:
        return
    listar_negocios.clear()
    detener_negocios(todos)
    if not seleccion:
        return
    subprocess.Popen(
        ["./scripts/dev_up.sh", "--skip-checks", "--negocios", ",".join(n["id"] for n in seleccion)],
        cwd=HERUKA_FLOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for negocio in seleccion:
        for puerto in _puertos_negocio(negocio):
            _esperar_puerto(puerto, activo_esperado=True, intentos=INTENTOS_ESPERA_NEGOCIOS)


def _render_negocios_todos(negocios: list[dict], activos: list[dict]) -> None:
    nombre, _puerto, estado, enlaces, enlaces_github, interruptor = st.columns(
        COLUMNAS_LANZADERA, vertical_alignment="center"
    )
    nombre.markdown(f"**{t('todos_negocios')}**")
    estado.markdown(t("estado.activo") if activos else t("estado.parado"))
    enlaces.markdown(", ".join(n["id"] for n in activos))
    _pintar_github(enlaces_github, HERUKA_FLOW)
    with interruptor:
        key = "switch_negocios_todos"
        st.session_state[key] = len(activos) == len(negocios)

        def _on_change():
            iniciar_negocios(negocios if st.session_state[key] else [], negocios)

        _interruptor(key, _on_change)


def _render_negocio(negocio: dict, negocios: list[dict], activos: list[dict]) -> None:
    activo = negocio in activos
    nombre, puerto, estado, enlaces, enlaces_github, interruptor = st.columns(
        COLUMNAS_LANZADERA, vertical_alignment="center"
    )
    nombre.markdown(f"**{t('negocio', id=negocio['id'])}**")
    puerto.markdown(str(negocio["panel"]))
    estado.markdown(t("estado.activo") if activo else t("estado.parado"))
    if activo:
        _pintar_enlaces(
            enlaces,
            [
                ("Frontend", f"http://localhost:{negocio['front']}"),
                ("Panel", f"http://localhost:{negocio['panel']}"),
                ("API", f"http://localhost:{negocio['api']}/health"),
            ],
        )
    _pintar_github(enlaces_github, HERUKA_FLOW)
    with interruptor:
        key = f"switch_negocio_{negocio['id']}"
        st.session_state[key] = activo

        # Un solo backend para todos: cambiar uno relanza el stack con la nueva selección (ADR-0005).
        def _on_change():
            if st.session_state[key]:
                iniciar_negocios(activos + [negocio], negocios)
            else:
                iniciar_negocios([n for n in activos if n["id"] != negocio["id"]], negocios)

        _interruptor(key, _on_change)


def _filas_lanzadera() -> list[dict]:
    """Proyectos y negocios con lo que necesitan el filtro (texto, carpeta, estado, tipo) y la tabla."""
    filas = []
    for proyecto in PROYECTOS:
        activo = esta_activo(proyecto)
        filas.append(
            {
                "texto": f"{proyecto['nombre']} {proyecto['ruta']} {proyecto['puerto']}",
                "carpeta": _carpeta_raiz(proyecto),
                "activo": activo,
                "negocio": False,
                "tablero": _github(str(proyecto["path"]))[1],
                "pintar": lambda proyecto=proyecto, activo=activo: _render_proyecto(proyecto, activo),
            }
        )
    if not CON_NEGOCIOS:
        return filas

    carpeta = _carpeta_raiz(HERUKA_LIFE_SINGLE)
    negocios = listar_negocios()
    if not negocios:
        # heruka-flow sin NEGOCIOS_MULTITENANT: un único negocio, que se arranca como un proyecto.
        activo = esta_activo(HERUKA_LIFE_SINGLE)
        filas.append(
            {
                "texto": f"{HERUKA_LIFE_SINGLE['nombre']} {HERUKA_LIFE_SINGLE['ruta']} {HERUKA_LIFE_SINGLE['puerto']}",
                "carpeta": carpeta,
                "activo": activo,
                "negocio": True,
                "tablero": _github(str(HERUKA_LIFE_SINGLE["path"]))[1],
                "pintar": lambda: _render_proyecto(HERUKA_LIFE_SINGLE, activo),
            }
        )
        return filas

    activos = [n for n in negocios if negocio_activo(n)]
    filas.append(
        {
            "texto": f"{t('todos_negocios')} " + " ".join(n["id"] for n in negocios),
            "carpeta": carpeta,
            "activo": bool(activos),
            "negocio": True,
            "tablero": _github(str(HERUKA_FLOW))[1],
            "pintar": lambda: _render_negocios_todos(negocios, activos),
        }
    )
    for negocio in negocios:
        filas.append(
            {
                "texto": f"{t('negocio', id=negocio['id'])} {HERUKA_LIFE_SINGLE['ruta']} {negocio['panel']}",
                "carpeta": carpeta,
                "activo": negocio in activos,
                "negocio": True,
                "tablero": _github(str(HERUKA_FLOW))[1],
                "pintar": lambda negocio=negocio: _render_negocio(negocio, negocios, activos),
            }
        )
    return filas


def _aviso_demo() -> None:
    if DEMO:
        st.info(t("demo.aviso"), icon=":material/info:")


def _titulo_tarjeta(texto: str) -> None:
    # HTML y no "**negrita**": la tabla de proyectos reconoce sus nombres por la negrita.
    st.markdown(f'<span style="font-size:1.05rem;font-weight:600">{html.escape(texto)}</span>', unsafe_allow_html=True)


SEMANAS_ACTIVIDAD = 26


@st.cache_data(ttl=3600, show_spinner=False)
def _actividad(hasta: date) -> tuple[dict[date, int], int]:
    """Commits por día de las últimas semanas, de lunes a `hasta`, y cuántos repositorios suman."""
    desde = hasta - timedelta(days=hasta.weekday() + 7 * (SEMANAS_ACTIVIDAD - 1))
    if DEMO:
        return demo.actividad(desde, hasta), len(PROYECTOS)
    repos = actividad.repositorios(RUTAS_REPOS)
    return actividad.commits_por_dia(repos, desde, hasta), len(repos)


def _issues_por_proyecto() -> list[tuple[list[str], dict[str, int]]]:
    """`(nombres, cuenta)` por tablero: cada tablero cuenta una vez, con todos los proyectos que lo comparten."""
    recuentos = _recuentos(_tableros())
    por_tablero: dict[tuple[str, int], list[str]] = {}
    nombres_y_rutas = [(p["nombre"], p["path"]) for p in PROYECTOS]
    if CON_NEGOCIOS:
        nombres_y_rutas.append((HERUKA_LIFE_SINGLE["nombre"], HERUKA_FLOW))
    for nombre, ruta in nombres_y_rutas:
        tablero = _github(str(ruta))[1]
        if tablero and recuentos.get(tablero):
            por_tablero.setdefault(tablero, []).append(nombre)
    return [(nombres, recuentos[tablero]) for tablero, nombres in por_tablero.items()]


def _grafico_issues(issues: list[tuple[list[str], dict[str, int]]], ejes: dict[str, str]) -> None:
    st.html(graficos.leyenda(github.ESTADOS[:4], graficos.COLORES_ESTADO[:4]))
    st.altair_chart(graficos.issues_por_estado(issues, ejes), width="stretch")


def _alternar_graficos() -> None:
    st.session_state["graficos_lanzadera"] = not st.session_state["graficos_lanzadera"]


def _graficos_lanzadera() -> None:
    # Clave propia, no de un widget: Streamlit borra el estado de los widgets de las páginas que
    # no se pintan, y lo plegado tiene que seguir así al volver de otra página.
    visibles = st.session_state.setdefault("graficos_lanzadera", True)
    issues = _issues_por_proyecto()
    abiertos = sum(cuenta[e] for _nombre, cuenta in issues for e in github.ESTADOS[:4])
    commits, repos = _actividad(date.today())
    total_commits = sum(commits.values())
    ejes = {
        "proyecto": t("eje.proyecto"),
        "estado": t("eje.estado"),
        "issues": t("eje.issues"),
        "dia": t("actividad.dia"),
        "commits": t("actividad.commits"),
    }

    tarjetas = [
        (
            "issues",
            t("issues.titulo"),
            t("issues.sub") if issues else t("issues.vacio"),
            t("issues.resumen", n=abiertos, tableros=len(issues)),
            (lambda: _grafico_issues(issues, ejes)) if issues else None,
        ),
        (
            "actividad",
            t("actividad.titulo"),
            t("actividad.sub", n=total_commits, repos=repos, semanas=SEMANAS_ACTIVIDAD),
            t("actividad.resumen", n=total_commits, semanas=SEMANAS_ACTIVIDAD),
            lambda: st.altair_chart(graficos.actividad(commits, _idioma(), ejes), width="stretch"),
        ),
    ]
    # Un botón en cada tarjeta, pero las dos se pliegan y despliegan a la vez.
    for columna, (clave, titulo, subtitulo, resumen, pintar) in zip(st.columns(2), tarjetas, strict=True):
        with columna, st.container(border=True, height="stretch"):
            with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
                _titulo_tarjeta(titulo)
                st.button(
                    "",
                    icon=":material/expand_less:" if visibles else ":material/expand_more:",
                    help=t("graficos.ocultar") if visibles else t("graficos.mostrar"),
                    key=f"plegar_{clave}",
                    type="tertiary",
                    on_click=_alternar_graficos,
                )
            if not visibles:
                st.caption(resumen)
                continue
            st.caption(subtitulo)
            if pintar:
                pintar()


def render_proyectos() -> None:
    st.title(t("pagina.Lanzadera"))
    _aviso_demo()

    filas = _filas_lanzadera()
    if _tableros():
        with st.spinner(t("consultando_tableros")):
            _recuentos(_tableros())
    _graficos_lanzadera()

    tipos = [*sorted({f["carpeta"] for f in filas}), *([NEGOCIOS] if CON_NEGOCIOS else [])]
    _colorear_pastillas(tipos)
    barra = st.container(horizontal=True, vertical_alignment="center", key="barra_lanzadera")
    with barra:
        texto = _buscar("buscar_proyecto", t("buscar.proyecto"))
        # Un solo grupo de píldoras, para que queden todas a la misma distancia; el filtro
        # separa carpetas y estados: OR dentro de cada tipo, AND entre tipos y con el buscador.
        seleccion = st.pills(
            "Filtros",
            [*tipos, *ESTADOS],
            selection_mode="multi",
            format_func=lambda o: t(f"filtro.{o}") if o == NEGOCIOS or o in ESTADOS else o,
            label_visibility="collapsed",
            key="filtros_lanzadera",
            width="content",
        )
    estados = [o for o in seleccion if o in ESTADOS]
    carpetas = [o for o in seleccion if o not in ESTADOS and o != NEGOCIOS]

    buscado = texto.strip().lower()
    visibles = [
        f
        for f in filas
        if (not buscado or buscado in f["texto"].lower())
        and (not carpetas or f["carpeta"] in carpetas)
        and (not estados or ("activo" if f["activo"] else "parado") in estados)
        and (NEGOCIOS not in seleccion or f["negocio"])
    ]
    with barra:
        if _tableros():
            # on_click y no "if st.button": el callback vacía la caché antes del rerun; si no,
            # los gráficos, que se pintan antes que este botón, saldrían con los recuentos viejos.
            st.button(
                t("actualizar_tableros"),
                icon=":material/refresh:",
                key="actualizar_tableros",
                on_click=_recuentos_en_cache.clear,
            )
    # Contador y orden en su propia línea, que separa la barra de filtros de la tabla.
    with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
        contador = st.empty()
        orden = None
        if _tableros():
            orden = st.pills(
                "Ordenar por issues en",
                [f"↓ {estado}" for estado in github.ESTADOS],
                selection_mode="single",
                label_visibility="collapsed",
                key="orden_lanzadera",
                width="content",
            )
    if orden:
        # Ordenar por un estado del tablero solo tiene sentido en las apps que tienen tablero.
        estado = orden.removeprefix("↓ ")
        recuentos = _recuentos(_tableros())
        visibles = sorted(
            (f for f in visibles if recuentos.get(f["tablero"])),
            key=lambda f: recuentos[f["tablero"]][estado],
            reverse=True,
        )
    contador.caption(t("contador", n=len(visibles), total=len(filas)))

    # Streamlit no tiene tablas con widgets dentro: cada fila es un contenedor con key, y
    # su clase st-key-<key> permite el fondo de cabecera y el efecto cebra (tema claro fijo).
    st.html(
        """<style>
.st-key-cabecera_lanzadera, [class*="st-key-fila_par_"], [class*="st-key-fila_impar_"] {
  padding: 0.55rem 0.6rem;
  border-radius: 0.4rem;
  gap: 0;
}
/* Streamlit compensa el margen del párrafo con un margin-bottom negativo; en la celda de
   GitHub (HTML, sin párrafo) eso descuadra el centrado y la saca del fondo de la fila. */
.st-key-cabecera_lanzadera [data-testid="stMarkdownContainer"],
[class*="st-key-fila_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0; }
.st-key-cabecera_lanzadera [data-testid="stMarkdownContainer"] p,
[class*="st-key-fila_"] [data-testid="stMarkdownContainer"] p { margin: 0; }
/* Sin hueco entre filas: si no, las blancas parecen más altas que las de la cebra. */
.st-key-tabla_lanzadera { gap: 0; }
/* Puerto, estado e interruptor no se parten en pantallas estrechas ("850" / "1"). */
[class*="st-key-fila_"] [data-testid="stColumn"]:nth-child(2),
[class*="st-key-fila_"] [data-testid="stColumn"]:nth-child(3),
[class*="st-key-fila_"] [data-testid="stColumn"]:nth-child(6),
.st-key-cabecera_lanzadera [data-testid="stColumn"] { white-space: nowrap; }
.st-key-cabecera_lanzadera { background: rgba(246, 51, 102, 0.12); }
[class*="st-key-fila_impar_"] { background: rgba(49, 51, 63, 0.05); }
</style>"""
    )
    with st.container(key="tabla_lanzadera"):
        with st.container(key="cabecera_lanzadera"):
            for columna, titulo in zip(
                st.columns(COLUMNAS_LANZADERA),
                [t("col.proyecto"), t("col.puerto"), t("col.estado"), t("col.enlaces"), t("col.github"), ""],
                strict=True,
            ):
                columna.markdown(f"**{titulo}**" if titulo else "")
        for i, fila in enumerate(visibles):
            with st.container(key=f"fila_{'impar' if i % 2 else 'par'}_{i}"):
                fila["pintar"]()


# Paleta categórica validada (orden fijo, ver skill dataviz / references/palette.md).
PALETA_CATEGORIAS = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]


def _parse_etiquetas(categoria: str) -> list[str]:
    # Varias etiquetas se separan con ";" en la misma celda del CSV; se
    # recortan espacios para no duplicar etiquetas por errores de tecleo
    # (p. ej. "Canal" y " Canal" deben contar como la misma etiqueta).
    return [e.strip() for e in categoria.split(";") if e.strip()]


def render_enlaces() -> None:
    st.title(t("pagina.Enlaces"))
    _aviso_demo()

    df = cargar_enlaces()
    if df.empty:
        st.info(t("enlaces.vacio", fichero=ENLACES_CSV.name))
        return

    etiquetas_por_fila = [_parse_etiquetas(c) for c in df["etiquetas"]]
    etiquetas = sorted({e for fila in etiquetas_por_fila for e in fila})
    color_etiqueta = {e: PALETA_CATEGORIAS[i % len(PALETA_CATEGORIAS)] for i, e in enumerate(etiquetas)}

    botones_etiqueta_html = "".join(
        f'<button class="filtro-categoria" data-categoria="{html.escape(e)}" '
        f'style="--color:{color_etiqueta[e]}">{html.escape(e)}</button>'
        for e in etiquetas
    )

    def fila_html(descripcion: str, enlace: str, etiquetas_fila: list[str]) -> str:
        descripcion_e = html.escape(descripcion)
        enlace_e = html.escape(enlace, quote=True)
        badges = "".join(
            f'<span class="badge" style="background:{color_etiqueta[e]}">{html.escape(e)}</span>'
            for e in etiquetas_fila
        )
        data_categorias = html.escape("|".join(etiquetas_fila))
        return (
            f'<tr data-categorias="{data_categorias}">'
            f'<td class="col-descripcion" title="{descripcion_e}">{descripcion_e}</td>'
            f'<td class="col-enlace">🔗 <a href="{enlace_e}" target="_blank" rel="noopener noreferrer" title="{enlace_e}">{enlace_e}</a></td>'
            f'<td class="col-categoria">{badges}</td>'
            "</tr>"
        )

    filas_html = "".join(
        fila_html(fila["descripcion"], fila["enlace"], etiquetas_fila)
        for (_, fila), etiquetas_fila in zip(df.iterrows(), etiquetas_por_fila)
    )

    pagina = f"""
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; }}
  #filtro {{
    width: 100%; padding: 10px; margin-bottom: 12px; font-size: 15px;
    box-sizing: border-box; border: 1px solid #ccc; border-radius: 6px;
  }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; table-layout: fixed; }}
  th, td {{
    border: 1px solid #ddd; padding: 6px 10px; text-align: left;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  th {{ background: #f3f4f6; position: sticky; top: 0; cursor: default; }}
  td a {{ text-decoration: none; }}
  .col-descripcion {{ width: 30%; }}
  .col-enlace {{ width: 52%; }}
  .col-categoria {{ width: 18%; }}
  tr:nth-child(even) {{ background: #fafafa; }}
  tr:hover {{ background: #eef2ff; }}
  .badge {{ color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; display: inline-block; margin: 1px 4px 1px 0; }}
  #contador {{ font-size: 13px; color: #666; margin-bottom: 6px; }}
  .filtros-fila {{ margin-bottom: 8px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }}
  .filtros-fila .etiqueta {{ font-size: 12px; color: #888; margin-right: 2px; }}
  .filtro-categoria {{
    --color: #6b7280;
    border: 1.5px solid var(--color); background: white; color: var(--color);
    padding: 4px 10px; border-radius: 12px; font-size: 13px; cursor: pointer;
    font-weight: 500; transition: all 0.1s ease-in-out;
  }}
  .filtro-categoria.activo {{ background: var(--color); color: white; }}
</style>

<input type="text" id="filtro" placeholder="{html.escape(t("enlaces.buscar"))}">
<div class="filtros-fila"><span class="etiqueta">{html.escape(t("enlaces.etiquetas"))}</span>{botones_etiqueta_html}</div>
<div id="contador"></div>
<div style="overflow:auto; max-height: 70vh;">
<table id="tabla">
  <thead><tr><th class="col-descripcion">{html.escape(t("enlaces.descripcion"))}</th><th class="col-enlace">{html.escape(t("enlaces.enlace"))}</th><th class="col-categoria">{html.escape(t("enlaces.etiquetas").rstrip(":"))}</th></tr></thead>
  <tbody>{filas_html}</tbody>
</table>
</div>

<script>
(function() {{
  // st.html con unsafe_allow_javascript inserta este bloque de código en el
  // documento principal de la app (no en un iframe aislado), y ese documento
  // persiste al navegar entre páginas del launcher. Sin esta IIFE, al volver
  // a "Enlaces" el bloque se reinyecta y trata de redeclarar
  // categoriasActivas en el mismo ámbito global, lo que lanza un SyntaxError
  // y aborta toda la ejecución (incluido el addEventListener de los botones
  // de categoría) hasta recargar la página entera.
  const categoriasActivas = new Set();

  function actualizarBotones() {{
    document.querySelectorAll('.filtro-categoria').forEach(btn => {{
      btn.classList.toggle('activo', categoriasActivas.has(btn.dataset.categoria));
    }});
  }}

  document.querySelectorAll('.filtro-categoria').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const valor = btn.dataset.categoria;
      if (categoriasActivas.has(valor)) {{
        categoriasActivas.delete(valor);
      }} else {{
        categoriasActivas.add(valor);
      }}
      actualizarBotones();
      filtrar();
    }});
  }});
  document.getElementById('filtro').addEventListener('input', filtrar);

  function filtrar() {{
    const texto = document.getElementById('filtro').value.toLowerCase();
    const filas = document.querySelectorAll('#tabla tbody tr');
    let visibles = 0;
    filas.forEach(fila => {{
      const etiquetasFila = fila.dataset.categorias ? fila.dataset.categorias.split('|') : [];
      const coincideTexto = fila.textContent.toLowerCase().includes(texto);
      const coincideCategoria = categoriasActivas.size === 0 || etiquetasFila.some(e => categoriasActivas.has(e));
      const visible = coincideTexto && coincideCategoria;
      fila.style.display = visible ? '' : 'none';
      if (visible) visibles++;
    }});
    document.getElementById('contador').textContent = {json.dumps(t("enlaces.contador"))}
      .replace('{{n}}', visibles).replace('{{total}}', filas.length);
  }}
  actualizarBotones();
  filtrar();
}})();
</script>
"""

    st.html(pagina, unsafe_allow_javascript=True)


def _segundos(duracion: float) -> str:
    return _numero(f"{duracion:.1f} s".replace(".", ","))


def _bytes(valor: float) -> str:
    for unidad, factor in [("TiB", 2**40), ("GiB", 2**30), ("MiB", 2**20)]:
        if valor >= factor:
            return _numero(f"{valor / factor:.1f} {unidad}".replace(".", ","))
    return f"{valor:.0f} B"


def _porcentaje(pct: float) -> str:
    return f"{pct:.0f} %" if _idioma() == "es" else f"{pct:.0f}%"


def _medidores_vps(secciones: list[tuple[str, str]]) -> None:
    """Indicadores de memoria, disco, carga y fallos, leídos de las mismas secciones de debajo."""
    medidas = vps.medidores(secciones)
    tarjetas = []
    if medidas["memoria"]:
        usado, total, disponible = medidas["memoria"]
        pct = usado / total * 100
        detalle = t("vps.memoria_detalle", usado=_bytes(usado), disponible=_bytes(disponible or 0))
        tarjetas.append(graficos.tarjeta(t("vps.memoria"), _porcentaje(pct), detalle, pct, t("vps.alto")))
    if medidas["disco"]:
        pct, usado, total = medidas["disco"]
        detalle = t("vps.disco_detalle", usado=usado, total=total)
        tarjetas.append(graficos.tarjeta(t("vps.disco"), _porcentaje(pct), detalle, pct, t("vps.alto")))
    if medidas["carga"]:
        carga, cpus = medidas["carga"]
        pct = carga / cpus * 100
        detalle = t("vps.carga_detalle", pct=f"{pct:.0f}", cpus=cpus)
        tarjetas.append(graficos.tarjeta(t("vps.carga"), _numero(f"{carga:.2f}"), detalle, pct, t("vps.alto")))
    if medidas["fallos"] is not None:
        fallos = medidas["fallos"]
        detalle = t("vps.fallos_ninguno") if fallos == 0 else t("vps.fallos_alguno")
        tarjetas.append(graficos.tarjeta(t("vps.fallos"), str(fallos), detalle))
    for columna, tarjeta in zip(st.columns(len(tarjetas)) if tarjetas else [], tarjetas, strict=True):
        with columna:
            st.html(tarjeta)


def render_vps() -> None:
    st.title(t("pagina.VPS"))
    _aviso_demo()

    servidores = cargar_servidores()
    if not servidores:
        st.info(t("vps.sin_servidores", fichero=paths.vps().name))
        st.code('[[vps]]\nnombre = "VPS"\nhost = "vps"', language="toml")
        return
    if len(servidores) == 1:
        servidor = servidores[0]
    else:
        servidor = st.selectbox(t("vps.servidor"), servidores, format_func=lambda s: s["nombre"])
    host = servidor["host"]

    # Se guarda por servidor para que los reruns de Streamlit no repitan la
    # llamada SSH: solo se consulta al entrar por primera vez y al refrescar.
    # "buena" conserva la última consulta sin error para enseñarla si la nueva falla.
    consultas = st.session_state.setdefault("vps", {})

    col_estado, col_boton = st.columns([4, 1], vertical_alignment="center")
    # Pegado al borde derecho, alineado con las tarjetas de debajo.
    with col_boton, st.container(horizontal=True, horizontal_alignment="right"):
        refrescar = st.button(t("refrescar"), icon=":material/refresh:", key=f"refrescar_{host}")
    if refrescar or host not in consultas:
        with col_estado, st.spinner(t("vps.consultando", host=host)):
            resultado = demo.consultar_vps(host) if DEMO else vps.consultar(host)
        anterior = consultas.get(host, {}).get("buena")
        consultas[host] = {"ultima": resultado, "buena": anterior if resultado["error"] else resultado}

    ultima, buena = consultas[host]["ultima"], consultas[host]["buena"]
    with col_estado:
        momento = f"{ultima['hora']:%H:%M:%S} ({_segundos(ultima['duracion'])})"
        if ultima["error"]:
            st.markdown(t("vps.sin_conexion", host=host, momento=momento))
        else:
            st.markdown(t("vps.conectado", host=host, momento=momento))

    if ultima["error"]:
        st.error(f"{t('vps.error')}\n\n```\n{ultima['error']}\n```")
        if buena is None:
            return
        st.warning(t("vps.antiguos", hora=f"{buena['hora']:%H:%M:%S}"), icon=":material/schedule:")
    if not buena["secciones"]:
        st.warning(t("vps.vacio"))
    _medidores_vps(buena["secciones"])
    for fila in vps.repartir(buena["secciones"]):
        for columna, seccion in zip(st.columns(len(fila)), fila):
            if seccion is None:
                continue
            titulo, texto = seccion
            with columna:
                # Negrita en vez de st.subheader: cada línea cuenta para que quepa sin scroll.
                clave = f"seccion.{titulo}"
                st.markdown(f"**{t(clave) if clave in textos.TEXTOS['es'] else titulo}**")
                # Partir líneas en vez de scroll horizontal: lo que no cabe en la columna se ve igual.
                st.code(texto or t("vps.sin_salida"), language=None, wrap_lines=True)


def _ram(kb: int) -> str:
    return _numero(ram.formatear(kb))


def _puertos_registro() -> list[tuple[int, str, bool]]:
    """`(puerto, nombre, escucha)` de cada puerto del registro: el principal y los de sus enlaces."""
    puertos = {}
    for p in PROYECTOS:
        puertos[p["puerto"]] = p["nombre"]
        for etiqueta, puerto, *_resto in p.get("enlaces", []):
            puertos.setdefault(puerto, f"{p['nombre']} · {etiqueta}")
    if CON_NEGOCIOS:
        if negocios := listar_negocios():
            for n in negocios:
                for parte in ("front", "panel", "api"):
                    puertos.setdefault(n[parte], t("negocio", id=n["id"]))
        else:
            puertos.setdefault(HERUKA_LIFE_SINGLE["puerto"], HERUKA_LIFE_SINGLE["nombre"])
    return [(puerto, nombre, _puerto_activo(puerto)) for puerto, nombre in puertos.items()]


def render_local() -> None:
    st.title(t("pagina.Local"))
    _aviso_demo()

    # Igual que VPS: se mide al entrar por primera vez y al recalcular, no en cada rerun.
    col_estado, col_boton = st.columns([4, 1], vertical_alignment="center")
    with col_boton, st.container(horizontal=True, horizontal_alignment="right"):
        recalcular = st.button(t("recalcular"), icon=":material/refresh:", key="recalcular_ram")
    medibles = [*PROYECTOS, *([HERUKA_LIFE_SINGLE] if CON_NEGOCIOS else [])]
    if recalcular or "ram" not in st.session_state:
        with col_estado, st.spinner(t("local.midiendo")):
            st.session_state["ram"] = demo.ram(medibles) if DEMO else ram.consultar(medibles)
    consulta = st.session_state["ram"]
    with col_estado:
        st.markdown(t("local.cabecera", hora=f"{consulta['hora']:%H:%M:%S}"))

    if consulta["error"]:
        st.error(f"{t('local.error')}\n\n```\n{consulta['error']}\n```")
        return
    medicion = consulta["medicion"]
    if not medicion["proyectos"]:
        st.info(t("local.ninguno"))
        return
    for a, b in medicion["compartidos"]:
        st.warning(t("local.compartidos", a=a, b=b))
    ocultos = [m["nombre"] for m in medicion["proyectos"] if m["kb"] is None]
    if ocultos:
        st.info(t("local.ocultos", nombres=", ".join(ocultos)))

    visibles = [m for m in medicion["proyectos"] if m["kb"] is not None]
    total = sum(m["kb"] for m in visibles)
    maquina = demo.memoria_total_kb() if DEMO else ram.memoria_total_kb()
    tarjetas = [
        graficos.tarjeta(
            t("local.total"),
            _ram(total),
            t("local.total_detalle", total=_ram(maquina)) if maquina else "",
            total / maquina * 100 if maquina else None,
        ),
        graficos.tarjeta(
            t("local.activos"),
            t("local.activos_valor", n=len(medicion["proyectos"]), total=len(medibles)),
            t("local.activos_detalle"),
        ),
    ]
    if visibles:
        mayor = visibles[0]
        pct = f"{mayor['kb'] / total * 100:.0f}" if total else "0"
        tarjetas.append(
            graficos.tarjeta(
                t("local.mayor"), mayor["nombre"], t("local.mayor_detalle", ram=_ram(mayor["kb"]), pct=pct)
            )
        )
    for columna, tarjeta in zip(st.columns(len(tarjetas)), tarjetas, strict=True):
        with columna:
            st.html(tarjeta)

    col_grafico, col_puertos = st.columns([2, 1])
    with col_grafico, st.container(border=True, height="stretch"):
        _titulo_tarjeta(t("local.grafico"))
        st.caption(t("local.grafico_sub"))
        if visibles:
            ejes = {"proyecto": t("eje.proyecto"), "servicio": t("col.servicio"), "ram": t("col.ram")}
            st.altair_chart(graficos.ram_por_proyecto(visibles, ejes, _ram), width="stretch")
    with col_puertos, st.container(border=True, height="stretch"):
        _titulo_tarjeta(t("local.puertos"))
        st.caption(t("local.puertos_sub"))
        st.html(graficos.puertos(_puertos_registro()))

    with st.expander(t("local.tabla")):
        filas = [
            {
                t("col.proyecto"): m["nombre"],
                t("col.puerto"): str(m["puerto"]),
                t("col.ram"): t("local.no_visible") if m["kb"] is None else _ram(m["kb"]),
            }
            for m in medicion["proyectos"]
        ]
        filas.append({t("col.proyecto"): t("local.total_fila"), t("col.puerto"): "", t("col.ram"): _ram(total)})
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")

        for m in medicion["proyectos"]:
            if m["desglose"]:
                _titulo_tarjeta(t("local.por_servicio", nombre=m["nombre"]))
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                t("col.servicio"): t("script_arranque")
                                if etiqueta == ram.SCRIPT_ARRANQUE
                                else etiqueta,
                                t("col.puerto"): "" if puerto is None else str(puerto),
                                t("col.ram"): _ram(kb),
                            }
                            for etiqueta, puerto, kb in m["desglose"]
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )


with st.sidebar:
    pagina = st.radio(t("menu"), MENU, key="pagina", format_func=lambda p: t(f"pagina.{p}"))
    st.segmented_control(
        t("idioma"),
        list(paths.IDIOMAS),
        default=paths.idioma(),
        required=True,
        format_func=str.upper,
        key="idioma",
    )
    if DEMO:
        st.caption(t("demo.repo", url=REPO_PUBLICO))

if pagina == "Lanzadera":
    render_proyectos()
elif pagina == "Enlaces":
    render_enlaces()
elif pagina == "VPS":
    render_vps()
else:
    render_local()
