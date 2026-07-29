"""Detección de tipo/esquema, normalización a una forma común para el frontend y
cálculo de las mismas métricas que producen los scripts .py de referencia.

Forma normalizada devuelta por `normalizar`:

    {
      "tipo": "FRENOS" | "SUSPENSION",
      "esquema": "viejo" | "nuevo" | "n_a",
      "id_prueba": int | None,
      "fecha": str | None,
      "paneles": [
        {
          "titulo": str,
          "y_label": str,
          "series": [{"nombre": str, "muestras": [...], "valores": [...]}],
          "lineas":  [{"etiqueta": str, "valor": float, "estilo": "promedio|maximo|minimo|auxiliar"}],
          "marcadores": [{"muestra": float, "valor": float, "estilo": str}],
        },
        ...
      ],
      "metricas": { ... },      # eficacias / promedios / etc.
    }
"""

from __future__ import annotations

import statistics
from datetime import datetime

from .config import settings

TipoEsquema = tuple[str, str]


def parsear_fecha(valor) -> datetime | None:
    if not valor or not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


# --------------------------- utilidades base ---------------------------

def _valores(arr: list[dict]) -> list[float]:
    return [item["Valor"] for item in arr]


def _muestras(arr: list[dict]) -> list[float]:
    return [item["NumeroMuestra"] for item in arr]


def promedio(arr: list[dict]) -> float:
    v = _valores(arr)
    return sum(v) / len(v) if v else 0.0


def desviacion(arr: list[dict]) -> float:
    v = _valores(arr)
    return statistics.stdev(v) if len(v) > 1 else 0.0


def fuerza_maxima_abs(arr: list[dict]) -> tuple[float, float]:
    """(valor, muestra) del mayor valor absoluto — como graficar_frenos.py."""
    v = _valores(arr)
    m = _muestras(arr)
    idx = max(range(len(v)), key=lambda i: abs(v[i]))
    return v[idx], m[idx]


def maximo(arr: list[dict]) -> float:
    """Máximo simple — como visor_frenos.py (esquema viejo)."""
    return max(_valores(arr))


def minimo(arr: list[dict]) -> tuple[float, float]:
    """(valor, muestra) del mínimo — peso dinámico mínimo de suspensión."""
    v = _valores(arr)
    m = _muestras(arr)
    idx = min(range(len(v)), key=lambda i: v[i])
    return v[idx], m[idx]


# --------------------------- downsampling (LTTB) ---------------------------

def lttb(muestras: list[float], valores: list[float], umbral: int) -> tuple[list[float], list[float]]:
    """Largest-Triangle-Three-Buckets: reduce a `umbral` puntos conservando la forma."""
    n = len(valores)
    if umbral >= n or umbral < 3:
        return muestras, valores

    out_x = [muestras[0]]
    out_y = [valores[0]]
    every = (n - 2) / (umbral - 2)
    a = 0  # índice del último punto seleccionado

    for i in range(umbral - 2):
        # rango del bucket promedio (el siguiente)
        avg_start = int((i + 1) * every) + 1
        avg_end = int((i + 2) * every) + 1
        avg_end = min(avg_end, n)
        avg_range = avg_end - avg_start
        if avg_range == 0:
            avg_range = 1
            avg_end = min(avg_start + 1, n)
        avg_x = sum(muestras[avg_start:avg_end]) / avg_range
        avg_y = sum(valores[avg_start:avg_end]) / avg_range

        # rango del bucket actual
        range_start = int(i * every) + 1
        range_end = int((i + 1) * every) + 1

        point_ax = muestras[a]
        point_ay = valores[a]

        max_area = -1.0
        best = range_start
        for j in range(range_start, min(range_end, n)):
            area = abs(
                (point_ax - avg_x) * (valores[j] - point_ay)
                - (point_ax - muestras[j]) * (avg_y - point_ay)
            )
            if area > max_area:
                max_area = area
                best = j
        out_x.append(muestras[best])
        out_y.append(valores[best])
        a = best

    out_x.append(muestras[-1])
    out_y.append(valores[-1])
    return out_x, out_y


def _serie(nombre: str, arr: list[dict], reducir: bool = False) -> dict:
    m = _muestras(arr)
    v = _valores(arr)
    if reducir and len(v) > settings.downsample_umbral:
        m, v = lttb(m, v, settings.downsample_umbral)
    return {"nombre": nombre, "muestras": m, "valores": v}


# --------------------------- detección ---------------------------

def detectar(data: dict) -> TipoEsquema:
    """Devuelve (tipo, esquema). Lanza ValueError si no se reconoce."""
    if not isinstance(data, dict):
        raise ValueError("El contenido no es un objeto JSON válido")

    if "SuspensionDinamicaEje1" in data or "SuspensionEstaticaEje1" in data:
        return "SUSPENSION", "n_a"

    if "FuerzasEjes" in data and "PesosEjes" in data:
        fuerzas = data["FuerzasEjes"]
        if "FuerzasEje1_Izq" in fuerzas:
            return "FRENOS", "nuevo"
        if "FuerzasEje1" in fuerzas:
            return "FRENOS", "viejo"

    if "BuffersEjes" in data:
        return "ALINEACION", "n_a"

    if "BufferRuidoMotor" in data:
        return "RUIDOS", "n_a"

    raise ValueError("Esquema no reconocido (no es FRENOS, SUSPENSION, ALINEACION ni RUIDOS)")


# --------------------------- normalización FRENOS ---------------------------

def _frenos_nuevo(data: dict) -> dict:
    pesos = data["PesosEjes"]
    fuerzas = data["FuerzasEjes"]

    p = {
        "e1_izq": promedio(pesos["PesosEje1_Izq"]),
        "e1_der": promedio(pesos["PesosEje1_Der"]),
        "e2_izq": promedio(pesos["PesosEje2_Izq"]),
        "e2_der": promedio(pesos["PesosEje2_Der"]),
    }
    peso_total = sum(p.values())

    def panel_eje1(titulo, arr, peso_est):
        f_max, m_max = fuerza_maxima_abs(arr)
        return {
            "titulo": titulo,
            "y_label": "Fuerza (N)",
            "series": [_serie("Fuerza", arr)],
            "lineas": [
                {"etiqueta": f"Peso estático prom.: {peso_est:.2f} N", "valor": peso_est, "estilo": "promedio"},
                {"etiqueta": f"Fuerza máxima: {f_max:.2f} N", "valor": f_max, "estilo": "maximo"},
            ],
            "marcadores": [{"muestra": m_max, "valor": f_max, "estilo": "maximo"}],
        }, abs(f_max)

    def panel_eje2(titulo, arr_p, arr_a, peso_est):
        f_max_p, m_max_p = fuerza_maxima_abs(arr_p)
        f_max_a, m_max_a = fuerza_maxima_abs(arr_a)
        return {
            "titulo": titulo,
            "y_label": "Fuerza (N)",
            "series": [_serie("Principal", arr_p), _serie("Auxiliar", arr_a)],
            "lineas": [
                {"etiqueta": f"Peso estático prom.: {peso_est:.2f} N", "valor": peso_est, "estilo": "promedio"},
                {"etiqueta": f"Máx principal: {f_max_p:.2f} N", "valor": f_max_p, "estilo": "maximo"},
                {"etiqueta": f"Máx auxiliar: {f_max_a:.2f} N", "valor": f_max_a, "estilo": "auxiliar"},
            ],
            "marcadores": [
                {"muestra": m_max_p, "valor": f_max_p, "estilo": "maximo"},
                {"muestra": m_max_a, "valor": f_max_a, "estilo": "auxiliar"},
            ],
        }, abs(f_max_p), abs(f_max_a)

    pe1i, f_e1_izq = panel_eje1("Frenos Eje 1 - Izquierdo", fuerzas["FuerzasEje1_Izq"], p["e1_izq"])
    pe1d, f_e1_der = panel_eje1("Frenos Eje 1 - Derecho", fuerzas["FuerzasEje1_Der"], p["e1_der"])
    pe2i, f_e2_izq, fa_izq = panel_eje2(
        "Frenos Eje 2 - Izquierdo", fuerzas["FuerzasEje2_Izq"],
        fuerzas["FuerzasAuxiliarEje2_Izq"], p["e2_izq"])
    pe2d, f_e2_der, fa_der = panel_eje2(
        "Frenos Eje 2 - Derecho", fuerzas["FuerzasEje2_Der"],
        fuerzas["FuerzasAuxiliarEje2_Der"], p["e2_der"])

    eficacia_total = (f_e1_izq + f_e1_der + f_e2_izq + f_e2_der) / peso_total * 100 if peso_total else 0.0
    eficacia_aux = (fa_izq + fa_der) / peso_total * 100 if peso_total else 0.0

    return {
        "paneles": [pe1i, pe1d, pe2i, pe2d],
        "metricas": {
            "peso_total": peso_total,
            "peso_e1_izq": p["e1_izq"], "peso_e1_der": p["e1_der"],
            "peso_e2_izq": p["e2_izq"], "peso_e2_der": p["e2_der"],
            "fmax_e1_izq": f_e1_izq, "fmax_e1_der": f_e1_der,
            "fmax_e2_izq": f_e2_izq, "fmax_e2_der": f_e2_der,
            "fmax_aux_izq": fa_izq, "fmax_aux_der": fa_der,
            "eficacia_total": eficacia_total,
            "eficacia_auxiliar": eficacia_aux,
        },
    }


def _frenos_viejo(data: dict) -> dict:
    pesos = data["PesosEjes"]
    fuerzas = data["FuerzasEjes"]

    prom = {e: promedio(pesos[e]) for e in ("PesosEje1", "PesosEje2")}
    desv = {e: desviacion(pesos[e]) for e in ("PesosEje1", "PesosEje2")}
    fmax = {e: maximo(fuerzas[e]) for e in ("FuerzasEje1", "FuerzasEje2")}

    suma_pesos = sum(prom.values())
    suma_fuerzas = sum(fmax.values())
    eficacia_total = (suma_fuerzas / suma_pesos * 100) if suma_pesos else 0.0

    def panel_peso(titulo, eje):
        return {
            "titulo": titulo,
            "y_label": "Peso",
            "series": [_serie("Peso", pesos[eje])],
            "lineas": [{"etiqueta": f"Promedio: {prom[eje]:.2f}", "valor": prom[eje], "estilo": "promedio"}],
            "marcadores": [],
        }

    def panel_fuerza(titulo, eje):
        _, m_max = fuerza_maxima_abs(fuerzas[eje])
        return {
            "titulo": titulo,
            "y_label": "Fuerza",
            "series": [_serie("Fuerza", fuerzas[eje])],
            "lineas": [{"etiqueta": f"Máximo: {fmax[eje]:.2f}", "valor": fmax[eje], "estilo": "maximo"}],
            "marcadores": [{"muestra": m_max, "valor": fmax[eje], "estilo": "maximo"}],
        }

    return {
        "paneles": [
            panel_peso("Pesos Eje 1", "PesosEje1"),
            panel_peso("Pesos Eje 2", "PesosEje2"),
            panel_fuerza("Fuerzas Eje 1", "FuerzasEje1"),
            panel_fuerza("Fuerzas Eje 2", "FuerzasEje2"),
        ],
        "metricas": {
            "peso_e1_promedio": prom["PesosEje1"], "peso_e1_desviacion": desv["PesosEje1"],
            "peso_e2_promedio": prom["PesosEje2"], "peso_e2_desviacion": desv["PesosEje2"],
            "fuerza_e1_maximo": fmax["FuerzasEje1"], "fuerza_e2_maximo": fmax["FuerzasEje2"],
            "eficacia_total": eficacia_total,
        },
    }


# --------------------------- normalización SUSPENSION ---------------------------

def _suspension(data: dict) -> dict:
    canales = [
        ("Suspensión Dinámica Eje 1 - Izquierdo", "SuspensionEstaticaEje1", "SuspensionDinamicaEje1", "Izquierdo"),
        ("Suspensión Dinámica Eje 1 - Derecho", "SuspensionEstaticaEje1", "SuspensionDinamicaEje1", "Derecho"),
        ("Suspensión Dinámica Eje 2 - Izquierdo", "SuspensionEstaticaEje2", "SuspensionDinamicaEje2", "Izquierdo"),
        ("Suspensión Dinámica Eje 2 - Derecho", "SuspensionEstaticaEje2", "SuspensionDinamicaEje2", "Derecho"),
    ]

    paneles = []
    metricas = {}
    for titulo, k_est, k_din, lado in canales:
        est = promedio(data[k_est][lado])
        dinamico = data[k_din][lado]
        v_min, m_min = minimo(dinamico)
        clave = f"{k_din}_{lado}".lower()
        metricas[f"{clave}_estatico_prom"] = est
        metricas[f"{clave}_dinamico_min"] = v_min

        paneles.append({
            "titulo": titulo,
            "y_label": "Valor",
            "series": [_serie("Dinámica", dinamico, reducir=True)],
            "lineas": [
                {"etiqueta": f"Peso estático prom.: {est:.2f}", "valor": est, "estilo": "promedio"},
                {"etiqueta": f"Peso dinámico mín.: {v_min:.2f}", "valor": v_min, "estilo": "minimo"},
            ],
            "marcadores": [{"muestra": m_min, "valor": v_min, "estilo": "minimo"}],
        })

    # Escalares de porcentaje (strings tipo "100,0")
    for k in ("IzqDelantera", "DerDelantera", "IzqTrasera", "DerTrasera"):
        if k in data:
            metricas[k.lower()] = data[k]

    return {"paneles": paneles, "metricas": metricas}


# --------------------------- normalización ALINEACION ---------------------------

def _alineacion(data: dict) -> dict:
    buffers = data["BuffersEjes"]
    paneles = []
    metricas = {}
    for eje, clave in (("Eje 1", "BufferAlineacionEje1"), ("Eje 2", "BufferAlineacionEje2")):
        arr = buffers.get(clave)
        if not arr:
            continue
        prom = promedio(arr)
        metricas[f"{clave.lower()}_promedio"] = prom
        paneles.append({
            "titulo": f"Alineación {eje}",
            "y_label": "Valor",
            "series": [_serie("Alineación", arr)],
            "lineas": [{"etiqueta": f"Promedio: {prom:.2f}", "valor": prom, "estilo": "promedio"}],
            "marcadores": [],
        })
    return {"paneles": paneles, "metricas": metricas}


# --------------------------- normalización RUIDOS ---------------------------

def _ruidos(data: dict) -> dict:
    arr = data["BufferRuidoMotor"]
    prom = promedio(arr)
    v_max, m_max = fuerza_maxima_abs(arr)
    return {
        "paneles": [{
            "titulo": "Ruido de motor",
            "y_label": "Nivel (dB)",
            "series": [_serie("Ruido motor", arr)],
            "lineas": [{"etiqueta": f"Promedio: {prom:.2f} dB", "valor": prom, "estilo": "promedio"}],
            "marcadores": [{"muestra": m_max, "valor": v_max, "estilo": "maximo"}],
        }],
        "metricas": {"ruido_promedio": prom, "ruido_maximo": v_max},
    }


# --------------------------- entrada pública ---------------------------

def normalizar(data: dict) -> dict:
    tipo, esquema = detectar(data)
    if tipo == "SUSPENSION":
        cuerpo = _suspension(data)
    elif tipo == "ALINEACION":
        cuerpo = _alineacion(data)
    elif tipo == "RUIDOS":
        cuerpo = _ruidos(data)
    elif esquema == "nuevo":
        cuerpo = _frenos_nuevo(data)
    else:
        cuerpo = _frenos_viejo(data)

    return {
        "tipo": tipo,
        "esquema": esquema,
        "id_prueba": data.get("IdPrueba"),
        "fecha": data.get("Fecha"),
        **cuerpo,
    }
