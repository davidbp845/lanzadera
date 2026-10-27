"""Gráficos e indicadores del panel: Altair para los gráficos y HTML propio para las tarjetas.

Colores de la paleta validada de la skill dataviz (references/palette.md); los de estado
del tablero son sus cinco primeros huecos en orden, que pasan el validador como vecinos.
"""

import html
from datetime import date, timedelta

import altair as alt
import pandas as pd

import github

# Backlog · Ready · In progress · In review · Done.
COLORES_ESTADO = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
# Rampa secuencial azul (100 → 600) para el mapa de actividad; el cero va en gris.
AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]
VACIO = "#ebedf0"
CATEGORIAS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
# Estados del medidor; a partir de 80 % avisa con color, icono y texto, nunca solo con color.
PISTA, NORMAL, SERIO, CRITICO = "#cde2fb", "#2a78d6", "#ec835a", "#d03b3b"
TEXTO_SUAVE = "#5F6272"
MESES = {
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}
DIAS = {"es": ["L", "", "X", "", "V", "", ""], "en": ["Mon", "", "Wed", "", "Fri", "", ""]}


def _ejes(chart: alt.Chart) -> alt.Chart:
    return chart.configure_view(stroke=None).configure_axis(
        grid=False, domain=False, ticks=False, labelColor=TEXTO_SUAVE, labelFontSize=13
    )


# Caracteres que caben en la etiqueta de una barra (labelLimit de 260 px a 13 px de letra).
LARGO_ETIQUETA = 36


def _corto(nombre: str) -> str:
    # "Acme Studio (acme)" -> "acme": el alias entre paréntesis del registro.
    return nombre[nombre.rindex("(") + 1 : -1] if nombre.endswith(")") and "(" in nombre else nombre


def etiqueta_tablero(nombres: list[str], maximo: int = LARGO_ETIQUETA) -> str:
    """Nombres de los proyectos de un tablero, " · " entre ellos, resumidos hasta caber en `maximo`.

    De más a menos texto: los nombres completos, los alias entre paréntesis, los primeros alias
    con "+N" por los que no caben, y el primero cortado con "…".
    """
    completo = " · ".join(nombres)
    if len(completo) <= maximo:
        return completo
    cortos = [_corto(n) for n in nombres]
    for cuantos in range(len(cortos), 0, -1):
        resto = f" +{len(cortos) - cuantos}" if cuantos < len(cortos) else ""
        if len(texto := " · ".join(cortos[:cuantos]) + resto) <= maximo:
            return texto
    resto = f" +{len(cortos) - 1}" if len(cortos) > 1 else ""
    return cortos[0][: maximo - len(resto) - 1] + "…" + resto


def issues_por_estado(recuentos: list[tuple[list[str], dict[str, int]]], ejes: dict[str, str]) -> alt.Chart:
    """Barra apilada por tablero con sus items abiertos (sin Done), de más a menos.

    Cada tablero llega con los nombres de sus proyectos: la etiqueta los resume si no caben
    y el tooltip los da completos.
    """
    abiertos = github.ESTADOS[:4]
    filas = [
        {
            "proyecto": etiqueta_tablero(nombres),
            "proyectos": " · ".join(nombres),
            "estado": estado,
            "n": cuenta[estado],
            "orden": i,
        }
        for nombres, cuenta in recuentos
        for i, estado in enumerate(abiertos)
        if cuenta[estado]
    ]
    df = pd.DataFrame(filas, columns=["proyecto", "proyectos", "estado", "n", "orden"])
    totales_por = {etiqueta_tablero(nombres): sum(cuenta[e] for e in abiertos) for nombres, cuenta in recuentos}
    orden = sorted(totales_por, key=lambda etiqueta: -totales_por[etiqueta])
    total = df.groupby("proyecto", as_index=False)["n"].sum()
    y = alt.Y("proyecto:N", sort=orden, title=None, axis=alt.Axis(labelLimit=260))
    barras = (
        alt.Chart(df)
        .mark_bar(height=16, stroke="white", strokeWidth=2, cornerRadius=2)
        .encode(
            x=alt.X("sum(n):Q", title=None, axis=None),
            y=y,
            color=alt.Color(
                "estado:N",
                scale=alt.Scale(domain=abiertos, range=COLORES_ESTADO[:4]),
                # La leyenda va aparte, en HTML (leyenda()): la de Vega se centra sobre el área del
                # gráfico y, con etiquetas largas en el eje, se sale de la tarjeta.
                legend=None,
            ),
            order=alt.Order("orden:Q"),
            tooltip=[
                alt.Tooltip("proyectos:N", title=ejes["proyecto"]),
                alt.Tooltip("estado:N", title=ejes["estado"]),
                alt.Tooltip("n:Q", title=ejes["issues"]),
            ],
        )
    )
    totales = (
        alt.Chart(total).mark_text(align="left", dx=6, color=TEXTO_SUAVE, fontSize=13).encode(x="n:Q", y=y, text="n:Q")
    )
    return _ejes((barras + totales).properties(height=alt.Step(28)))


def leyenda(nombres: list[str], colores: list[str]) -> str:
    """Leyenda de una sola fila que se parte en varias si no cabe, alineada a la izquierda."""
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:4px 14px;font-size:0.8rem;color:#5F6272">'
        + "".join(
            f'<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;'
            f'background:{color}"></span>{html.escape(nombre)}</span>'
            for nombre, color in zip(nombres, colores, strict=True)
        )
        + "</div>"
    )


def cortes(valores: list[int]) -> list[float]:
    """Cinco cortes para la rampa: el 1 (gris por debajo) y los quintiles de los días con commits.

    Relativos a los datos: con cortes fijos, quien hace muchos commits al día lo ve todo en el tono más oscuro.
    """
    con_commits = sorted(v for v in valores if v)
    if not con_commits:
        return [1, 2, 3, 4, 5]
    quintiles = [con_commits[min(len(con_commits) - 1, len(con_commits) * i // 5)] for i in range(1, 5)]
    resultado = [1]
    for q in quintiles:
        # Estrictamente crecientes, o la escala de umbrales se descoloca.
        resultado.append(max(q, resultado[-1] + 1))
    return resultado


def actividad(commits: dict[date, int], idioma: str, ejes: dict[str, str]) -> alt.Chart:
    """Mapa de calor día a día, una columna por semana (de lunes a domingo), como el de GitHub."""
    df = pd.DataFrame(
        [
            {
                "dia": d.isoformat(),
                "semana": (d - timedelta(days=d.weekday())).isoformat(),
                "dia_semana": d.weekday(),
                "commits": n,
            }
            for d, n in sorted(commits.items())
        ]
    )
    meses = str(MESES[idioma])
    dias = str(DIAS[idioma])
    return _ejes(
        alt.Chart(df)
        .mark_rect(cornerRadius=2, stroke="white", strokeWidth=2)
        .encode(
            x=alt.X(
                "semana:O",
                title=None,
                # Solo el nombre del mes en la primera semana que empieza en él.
                axis=alt.Axis(
                    orient="top",
                    labelAngle=0,
                    labelAlign="left",
                    labelExpr=f"date(toDate(datum.value)) <= 7 ? {meses}[month(toDate(datum.value))] : ''",
                ),
            ),
            y=alt.Y("dia_semana:O", title=None, axis=alt.Axis(labelExpr=f"{dias}[datum.value]")),
            color=alt.Color(
                "commits:Q",
                scale=alt.Scale(type="threshold", domain=cortes(list(commits.values())), range=[VACIO, *AZUL[1:]]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("dia:T", title=ejes["dia"], format="%d/%m/%Y"),
                alt.Tooltip("commits:Q", title=ejes["commits"]),
            ],
        )
        # Ancho del contenedor: con celdas de tamaño fijo, 26 semanas se salen de la tarjeta en pantallas medianas.
        .properties(width="container", height=alt.Step(17))
    )


def ram_por_proyecto(proyectos: list[dict], ejes: dict[str, str], formatear) -> alt.Chart:
    """Barra apilada por proyecto, un tramo por servicio; `formatear(kb)` da el texto de la RAM."""
    filas = []
    for m in proyectos:
        servicios = m["desglose"] or [(m["nombre"], m["puerto"], m["kb"])]
        for i, (servicio, _puerto, kb) in enumerate(servicios):
            filas.append(
                {"proyecto": m["nombre"], "servicio": servicio, "mb": kb / 1024, "ram": formatear(kb), "orden": i}
            )
    df = pd.DataFrame(filas)
    total = pd.DataFrame(
        [{"proyecto": m["nombre"], "mb": m["kb"] / 1024, "ram": formatear(m["kb"])} for m in proyectos]
    )
    y = alt.Y("proyecto:N", sort=[m["nombre"] for m in proyectos], title=None, axis=alt.Axis(labelLimit=160))
    barras = (
        alt.Chart(df)
        .mark_bar(height=16, stroke="white", strokeWidth=2, cornerRadius=2)
        .encode(
            x=alt.X("sum(mb):Q", title=None, axis=None),
            y=y,
            color=alt.Color("orden:N", scale=alt.Scale(range=CATEGORIAS), legend=None),
            order=alt.Order("orden:Q"),
            tooltip=[
                alt.Tooltip("proyecto:N", title=ejes["proyecto"]),
                alt.Tooltip("servicio:N", title=ejes["servicio"]),
                alt.Tooltip("ram:N", title=ejes["ram"]),
            ],
        )
    )
    totales = (
        alt.Chart(total)
        .mark_text(align="left", dx=6, color=TEXTO_SUAVE, fontSize=13)
        .encode(x="mb:Q", y=y, text="ram:N")
    )
    return _ejes((barras + totales).properties(height=alt.Step(28)))


def nivel(pct: float) -> str:
    return CRITICO if pct >= 90 else SERIO if pct >= 80 else NORMAL


def tarjeta(titulo: str, valor: str, detalle: str = "", pct: float | None = None, aviso: str = "") -> str:
    """Indicador: título, cifra grande y, si hay `pct`, medidor; desde 80 % se añade `aviso` al detalle."""
    medidor = ""
    if pct is not None:
        color = nivel(pct)
        medidor = (
            f'<div style="height:10px;border-radius:5px;background:{PISTA};margin:8px 0 4px;overflow:hidden">'
            f'<div style="width:{min(max(pct, 0), 100):.0f}%;height:100%;border-radius:5px;background:{color}"></div></div>'
        )
        if pct >= 80 and aviso:
            detalle = f"{aviso} · {detalle}"
    return (
        '<div style="border:1px solid rgba(49,51,63,0.15);border-radius:0.5rem;padding:0.8rem 1rem;height:100%;'
        'box-sizing:border-box">'
        f'<div style="font-size:0.875rem;color:{TEXTO_SUAVE}">{html.escape(titulo)}</div>'
        f'<div style="font-size:2rem;font-weight:600;line-height:1.3;font-variant-numeric:tabular-nums;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{html.escape(valor)}</div>'
        f"{medidor}"
        f'<div style="font-size:0.8rem;color:{TEXTO_SUAVE}">{html.escape(detalle)}</div></div>'
    )


def puertos(estado: list[tuple[int, str, bool]]) -> str:
    """Una etiqueta por puerto `(puerto, nombre, escucha)`, en verde las que escuchan."""
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:6px">'
        + "".join(
            f'<span title="{html.escape(nombre)}" style="font-family:\'Source Code Pro\',monospace;font-size:0.8rem;'
            f"padding:2px 8px;border-radius:6px;border:1px solid "
            f'{"#21A366;background:#21A36614" if activo else "rgba(49,51,63,0.15)"}">{puerto}</span>'
            for puerto, nombre, activo in sorted(estado)
        )
        + "</div>"
    )
