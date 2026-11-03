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
    """Barra apilada por tablero con sus items abiertos (sin Done), de más a menos."""
    return por_estado(recuentos, github.ESTADOS[:4], COLORES_ESTADO[:4], ejes, ejes["issues"])


def por_estado(
    recuentos: list[tuple[list[str], dict[str, int]]],
    abiertos: list[str],
    colores: list[str],
    ejes: dict[str, str],
    titulo_n: str,
) -> alt.Chart:
    """Barra apilada por grupo de proyectos, un tramo por estado de `abiertos`, de más a menos.

    Cada grupo (un tablero, una carpeta de ADR) llega con los nombres de sus proyectos: la
    etiqueta los resume si no caben y el tooltip los da completos.
    """
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
                scale=alt.Scale(domain=abiertos, range=colores),
                # La leyenda va aparte, en HTML (leyenda()): la de Vega se centra sobre el área del
                # gráfico y, con etiquetas largas en el eje, se sale de la tarjeta.
                legend=None,
            ),
            order=alt.Order("orden:Q"),
            tooltip=[
                alt.Tooltip("proyectos:N", title=ejes["proyecto"]),
                alt.Tooltip("estado:N", title=ejes["estado"]),
                alt.Tooltip("n:Q", title=titulo_n),
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


# Estados de una ADR (adrs.ESTADOS): huecos de la misma paleta, sin el aqua, que aquí marca
# los issues abiertos. Sin clasificar, en gris.
COLORES_ADR = ["#eb6834", "#2a78d6", "#e87ba4", "#eda100"]
GRIS = "#8a8a8a"
ABIERTO = "#1baf7a"


def _pildora(texto: str, color: str) -> str:
    # Texto oscuro sobre el color aclarado, como las pastillas del tablero.
    return (
        f'<span style="display:inline-block;padding:1px 10px;border-radius:999px;background:{color}4d;'
        f'color:#31333F;font-size:0.8rem;font-weight:600;white-space:nowrap">{html.escape(texto)}</span>'
    )


def _issue(issue: dict, titulos: dict[str, str]) -> str:
    """Enlace a un issue con un punto: relleno si está abierto, hueco si cerrado; sin punto si no se sabe."""
    abierto = issue["abierto"]
    punto = (
        ""
        if abierto is None
        else f'<span style="width:8px;height:8px;border-radius:50%;display:inline-block;'
        f'background:{ABIERTO if abierto else "#ffffff"};border:1px solid {ABIERTO if abierto else TEXTO_SUAVE}"></span>'
    )
    titulo = "" if abierto is None else titulos["abierto" if abierto else "cerrado"]
    return (
        f'<a href="{html.escape(issue["url"])}" target="_blank" title="{html.escape(titulo)}" '
        'style="display:inline-flex;align-items:center;gap:5px;font-size:0.85rem;text-decoration:none;'
        "border:1px solid rgba(49,51,63,0.15);border-radius:999px;padding:0 9px 0 7px;color:#31333F;"
        f'white-space:nowrap">{punto}{html.escape(issue["ref"])}</a>'
    )


# Ordena la tabla en el navegador: sin rerun, y solo reordena las filas ya filtradas.
# st.html inserta el script en el documento principal, que persiste entre páginas y reruns:
# va en una IIFE y solo liga las tablas que aún no tienen el atributo `data-ligada`.
_ORDENAR_ADR = """<script>
(function() {
  document.querySelectorAll('table.tabla-adr:not([data-ligada])').forEach(function(tabla) {
    tabla.dataset.ligada = '1';
    var cuerpo = tabla.tBodies[0];
    var cabeceras = tabla.querySelectorAll('th[data-tipo]');
    var activa = null, sentido = 0;
    function clave(fila, columna, tipo) {
      var valor = fila.cells[columna].dataset.orden;
      return tipo === 'texto' ? valor : Number(valor);
    }
    cabeceras.forEach(function(th) {
      th.querySelector('button').addEventListener('click', function() {
        // Ascendente, descendente y vuelta al orden inicial.
        sentido = activa === th ? (sentido === 1 ? -1 : 0) : 1;
        activa = sentido ? th : null;
        var columna = th.cellIndex, tipo = th.dataset.tipo;
        var filas = Array.prototype.slice.call(cuerpo.rows);
        filas.sort(function(a, b) {
          var d = 0;
          if (sentido) {
            var ka = clave(a, columna, tipo), kb = clave(b, columna, tipo);
            d = tipo === 'texto' ? ka.localeCompare(kb, undefined, {numeric: true, sensitivity: 'base'}) : ka - kb;
          }
          // A igualdad, el orden inicial.
          return d * sentido || a.dataset.i - b.dataset.i;
        });
        filas.forEach(function(f) { cuerpo.appendChild(f); });
        cabeceras.forEach(function(otra) {
          var propia = otra === activa;
          otra.setAttribute('aria-sort', propia ? (sentido === 1 ? 'ascending' : 'descending') : 'none');
          otra.querySelector('.flecha').textContent = propia ? (sentido === 1 ? '\u25b2' : '\u25bc') : '\u2195';
          otra.querySelector('.flecha').style.opacity = propia ? '1' : '0.45';
        });
      });
    });
  });
})();
</script>"""


def tabla_adr(filas: list[dict], textos: dict[str, str], con_proyecto: bool = False) -> str:
    """Tabla de ADR: proyecto (con `con_proyecto`), número (enlace al fichero), decisión, estado,
    implementación e issues. Las columnas ADR, decisión, estado e implementación se ordenan con un
    clic en la cabecera (ascendente, descendente, orden inicial); el inicial es el de `filas`.

    Cada fila: `proyecto`, `numero`, `url`, `titulo`, `estado` (texto ya traducido), `color`,
    `implementacion` (texto ya traducido), `orden_estado` y `orden_implementacion` (enteros por los
    que se ordenan esas columnas), `aviso` e `issues` (`ref`, `url`, `abierto`). `textos` da las cabeceras y los tooltips.
    """
    celda = "padding:8px 12px;vertical-align:top"
    columnas = ("proyecto",) * con_proyecto + ("adr", "decision", "estado", "implementacion", "issues")
    tipos = {"adr": "numero", "decision": "texto", "estado": "numero", "implementacion": "numero"}
    boton = (
        "background:none;border:0;padding:0;margin:0;font:inherit;color:inherit;cursor:pointer;"
        "display:inline-flex;gap:4px;align-items:center;white-space:nowrap"
    )

    def _cabecera(c: str) -> str:
        texto = html.escape(textos[c])
        if c in tipos:
            texto = (
                f'<button type="button" style="{boton}">{texto}'
                '<span class="flecha" aria-hidden="true" style="opacity:0.45">↕</span></button>'
            )
        orden = f' data-tipo="{tipos[c]}" aria-sort="none"' if c in tipos else ""
        # Cabecera fija: la tabla hace scroll dentro de su caja.
        return (
            f'<th scope="col"{orden} style="{celda};font-weight:600;text-align:left;position:sticky;top:0;'
            f'background:#F7F8FA">{texto}</th>'
        )

    cabecera = "".join(_cabecera(c) for c in columnas)
    cuerpo = []
    for i, f in enumerate(filas):
        numero = html.escape(f["numero"])
        if f["url"]:
            numero = f'<a href="{html.escape(f["url"])}" target="_blank">{numero}</a>'
        aviso = f'<div style="color:#8a420b;font-size:0.85rem">⚠ {html.escape(f["aviso"])}</div>' if f["aviso"] else ""
        issues = "".join(_issue(i, textos) for i in f["issues"]) or f'<span style="color:{TEXTO_SUAVE}">—</span>'
        proyecto = f'<td style="{celda}">{html.escape(f["proyecto"])}</td>' if con_proyecto else ""
        cuerpo.append(
            f'<tr data-i="{i}" style="border-top:1px solid rgba(49,51,63,0.1)">'
            f"{proyecto}"
            f'<td data-orden="{int(f["numero"]) if f["numero"].isdigit() else 0}" '
            f"style=\"{celda};font-family:'Source Code Pro',monospace;font-size:0.85rem\">{numero}</td>"
            f'<td data-orden="{html.escape(f["titulo"])}" style="{celda}">{html.escape(f["titulo"])}{aviso}</td>'
            f'<td data-orden="{f["orden_estado"]}" style="{celda}">{_pildora(f["estado"], f["color"])}</td>'
            f'<td data-orden="{f["orden_implementacion"]}" style="{celda};white-space:nowrap">{html.escape(f["implementacion"])}</td>'
            f'<td style="{celda}"><div style="display:flex;flex-wrap:wrap;gap:4px">{issues}</div></td>'
            "</tr>"
        )
    return (
        '<div style="overflow:auto;max-height:60vh;border:1px solid rgba(49,51,63,0.15);border-radius:0.5rem">'
        '<table class="tabla-adr" style="width:100%;min-width:640px;border-collapse:collapse;font-size:0.9rem">'
        f'<thead><tr style="background:#F7F8FA;color:{TEXTO_SUAVE};font-size:0.85rem">{cabecera}</tr></thead>'
        f"<tbody>{''.join(cuerpo)}</tbody></table></div>"
        f"{_ORDENAR_ADR}"
    )


def revisar_adr(avisos: list[tuple[str, str, str, str]]) -> str:
    """Lista de `(proyecto, número, decisión, motivo)` de las ADR cuyo estado no cuadra con sus issues."""
    icono = (
        '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b5570f" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none;margin-top:3px">'
        '<path d="M12 3 2 21h20L12 3z"></path><path d="M12 10v5"></path><path d="M12 18h.01"></path></svg>'
    )
    return (
        '<ul style="margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:8px">'
        + "".join(
            f'<li style="display:flex;gap:8px;font-size:0.9rem;line-height:1.4">{icono}<span>'
            f'<strong style="font-weight:600">{html.escape(proyecto)} · {html.escape(numero)}</strong> '
            f'{html.escape(titulo)}<br><span style="color:{TEXTO_SUAVE};font-size:0.85rem">{html.escape(motivo)}'
            "</span></span></li>"
            for proyecto, numero, titulo, motivo in avisos
        )
        + "</ul>"
    )
