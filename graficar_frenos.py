"""
Grafica los datos de frenos en una sola figura 2x2 (fila por eje).

  Fila 1: Eje 1 Izquierdo | Eje 1 Derecho          (solo frenos principales)
  Fila 2: Eje 2 Izquierdo | Eje 2 Derecho           (principal + auxiliar superpuesto)

Leyenda de cada canal:
  - Peso estatico promedio (solo texto, sin linea)
  - Fuerza maxima principal (linea verde punteada)
  - Fuerza maxima auxiliar  (linea naranja punteada, solo Eje 2)

Titulo general incluye peso total, eficacia total y eficacia auxiliar.

    Eficacia total    = (F_max_E1_Izq + F_max_E1_Der + F_max_E2_Izq + F_max_E2_Der) / peso_total
    Eficacia auxiliar = (F_max_Aux_Izq + F_max_Aux_Der) / peso_total
    peso_total        = P_E1_Izq + P_E1_Der + P_E2_Izq + P_E2_Der  (promedios estaticos)

Uso:
    python graficar_frenos.py                       -> abre dialogo para escoger el JSON
    python graficar_frenos.py archivo.json          -> usa ese archivo
    python graficar_frenos.py archivo.json --nogui  -> solo guarda PNG (sin ventana)
"""

import json
import os
import sys
import traceback
from pathlib import Path

_NOGUI = "--nogui" in sys.argv
if _NOGUI:
    sys.argv = [a for a in sys.argv if a != "--nogui"]

import matplotlib
_tiene_display = (
    bool(os.environ.get("DISPLAY"))
    or sys.platform.startswith("win")
    or sys.platform == "darwin"
)
if _NOGUI or not _tiene_display:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ----------------------------- Utilidades -----------------------------

def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[0] if isinstance(data, list) else data


def extraer_valores(arreglo):
    muestras = [item["NumeroMuestra"] for item in arreglo]
    valores  = [item["Valor"]         for item in arreglo]
    return muestras, valores


def promedio(arreglo):
    valores = [item["Valor"] for item in arreglo]
    return sum(valores) / len(valores) if valores else 0.0


def fuerza_maxima(arreglo):
    """Retorna (valor_max, muestra_max) usando el mayor valor absoluto."""
    valores  = [item["Valor"]         for item in arreglo]
    muestras = [item["NumeroMuestra"] for item in arreglo]
    idx = max(range(len(valores)), key=lambda i: abs(valores[i]))
    return valores[idx], muestras[idx]


def seleccionar_archivo_dialogo():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    archivo = filedialog.askopenfilename(
        title="Selecciona el archivo JSON de frenos",
        filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
    )
    root.destroy()
    return Path(archivo) if archivo else None


def mostrar_error(mensaje):
    print(mensaje, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", mensaje)
        root.destroy()
    except Exception:
        pass


# ----------------------------- Graficado ------------------------------

def graficar_canal_eje1(ax, titulo, arreglo_princ, peso_est):
    """Eje 1: solo fuerza principal."""
    muestras, valores = extraer_valores(arreglo_princ)
    f_max, m_max = fuerza_maxima(arreglo_princ)

    ax.plot(muestras, valores, linewidth=1, color="tab:blue",
            label=f"Peso estatico promedio: {peso_est:.2f} N")
    ax.axhline(f_max, color="tab:green", linestyle=":", linewidth=1.2,
               label=f"Fuerza maxima: {f_max:.2f} N")
    ax.plot(m_max, f_max, "o", color="tab:green", markersize=6)

    ax.set_title(titulo)
    ax.set_xlabel("Numero de muestra")
    ax.set_ylabel("Fuerza (N)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    return abs(f_max)


def graficar_canal_eje2(ax, titulo, arreglo_princ, arreglo_aux, peso_est):
    """Eje 2: fuerza principal + auxiliar superpuestas."""
    m_p, v_p = extraer_valores(arreglo_princ)
    m_a, v_a = extraer_valores(arreglo_aux)
    f_max_p, m_max_p = fuerza_maxima(arreglo_princ)
    f_max_a, m_max_a = fuerza_maxima(arreglo_aux)

    ax.plot(m_p, v_p, linewidth=1, color="tab:blue",  label="Fuerza principal")
    ax.plot(m_a, v_a, linewidth=1, color="tab:orange", label="Fuerza auxiliar")

    ax.axhline(f_max_p, color="tab:green",  linestyle=":", linewidth=1.2,
               label=f"Max principal: {f_max_p:.2f} N")
    ax.plot(m_max_p, f_max_p, "o", color="tab:green", markersize=6)

    ax.axhline(f_max_a, color="tab:red", linestyle=":", linewidth=1.2,
               label=f"Max auxiliar: {f_max_a:.2f} N")
    ax.plot(m_max_a, f_max_a, "s", color="tab:red", markersize=6)

    # Peso estatico solo en leyenda
    ax.plot([], [], " ", label=f"Peso estatico promedio: {peso_est:.2f} N")

    ax.set_title(titulo)
    ax.set_xlabel("Numero de muestra")
    ax.set_ylabel("Fuerza (N)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    return abs(f_max_p), abs(f_max_a)


# ------------------------------- Main ---------------------------------

def main():
    # 1. Localizar archivo JSON
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1])
    else:
        ruta = seleccionar_archivo_dialogo()
        if ruta is None:
            print("No se selecciono ningun archivo. Saliendo.")
            return

    if not ruta.exists():
        mostrar_error(f"No se encontro el archivo:\n{ruta}")
        return

    print(f"Leyendo: {ruta}")
    prueba = cargar_json(ruta)

    # 2. Pesos estaticos promedio
    pesos   = prueba["PesosEjes"]
    fuerzas = prueba["FuerzasEjes"]

    p_e1_izq = promedio(pesos["PesosEje1_Izq"])
    p_e1_der = promedio(pesos["PesosEje1_Der"])
    p_e2_izq = promedio(pesos["PesosEje2_Izq"])
    p_e2_der = promedio(pesos["PesosEje2_Der"])
    peso_total = p_e1_izq + p_e1_der + p_e2_izq + p_e2_der

    print("\n--- Peso estatico promedio ---")
    print(f"Eje 1 Izquierdo : {p_e1_izq:.2f} N")
    print(f"Eje 1 Derecho   : {p_e1_der:.2f} N")
    print(f"Eje 2 Izquierdo : {p_e2_izq:.2f} N")
    print(f"Eje 2 Derecho   : {p_e2_der:.2f} N")
    print(f"Peso total      : {peso_total:.2f} N")

    # 3. Figura unica 2x2
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    (ax_e1_izq, ax_e1_der,
     ax_e2_izq, ax_e2_der) = axes.flat

    # Fila 1 — Eje 1
    print("\n--- Fuerza maxima Eje 1 ---")
    f_e1_izq = graficar_canal_eje1(
        ax_e1_izq, "Frenos Eje 1 - Izquierdo",
        fuerzas["FuerzasEje1_Izq"], p_e1_izq)
    print(f"Eje 1 Izquierdo : {f_e1_izq:.2f} N")

    f_e1_der = graficar_canal_eje1(
        ax_e1_der, "Frenos Eje 1 - Derecho",
        fuerzas["FuerzasEje1_Der"], p_e1_der)
    print(f"Eje 1 Derecho   : {f_e1_der:.2f} N")

    # Fila 2 — Eje 2 (principal + auxiliar)
    print("\n--- Fuerza maxima Eje 2 ---")
    f_e2_izq, fa_e2_izq = graficar_canal_eje2(
        ax_e2_izq, "Frenos Eje 2 - Izquierdo",
        fuerzas["FuerzasEje2_Izq"], fuerzas["FuerzasAuxiliarEje2_Izq"], p_e2_izq)
    print(f"Eje 2 Izquierdo principal : {f_e2_izq:.2f} N")
    print(f"Eje 2 Izquierdo auxiliar  : {fa_e2_izq:.2f} N")

    f_e2_der, fa_e2_der = graficar_canal_eje2(
        ax_e2_der, "Frenos Eje 2 - Derecho",
        fuerzas["FuerzasEje2_Der"], fuerzas["FuerzasAuxiliarEje2_Der"], p_e2_der)
    print(f"Eje 2 Derecho   principal : {f_e2_der:.2f} N")
    print(f"Eje 2 Derecho   auxiliar  : {fa_e2_der:.2f} N")

    # 4. Eficacias
    eficacia_total = (f_e1_izq + f_e1_der + f_e2_izq + f_e2_der) / peso_total * 100
    eficacia_aux   = (fa_e2_izq + fa_e2_der) / peso_total * 100

    print(f"\nEficacia total   : {eficacia_total:.1f}%")
    print(f"Eficacia auxiliar: {eficacia_aux:.1f}%")

    # 5. Titulo y guardado
    fig.suptitle(
        f"Prueba de Frenos - IdPrueba {prueba.get('IdPrueba', '')}\n"
        f"Peso total: {peso_total:.2f} N    |    "
        f"Eficacia total: {eficacia_total:.1f}%    |    "
        f"Eficacia auxiliar: {eficacia_aux:.1f}%",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    salida = Path.cwd() / (Path(ruta).stem + "_graficas.png")
    plt.savefig(salida, dpi=150)
    print(f"\nGrafica guardada en: {salida}")

    if matplotlib.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        mostrar_error(f"Ocurrio un error:\n{e}\n\n{traceback.format_exc()}")
        sys.exit(1)
