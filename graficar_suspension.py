"""
Grafica los datos de suspension dinamica (Eje1 y Eje2, Izquierdo y Derecho)
y muestra el peso estatico promedio y el peso dinamico minimo de cada arreglo.

Uso:
    python graficar_suspension.py                       -> abre dialogo para escoger el JSON
    python graficar_suspension.py archivo.json          -> usa ese archivo
    python graficar_suspension.py archivo.json --nogui  -> solo guarda PNG (sin ventana)
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
    valores = [item["Valor"] for item in arreglo]
    return muestras, valores


def promedio(arreglo):
    valores = [item["Valor"] for item in arreglo]
    return sum(valores) / len(valores) if valores else 0.0


def seleccionar_archivo_dialogo():
    """Abre un dialogo de tkinter para escoger el JSON. Devuelve Path o None."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    archivo = filedialog.askopenfilename(
        title="Selecciona el archivo JSON de suspension",
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

    # 2. Promedios estaticos
    est_e1_izq = promedio(prueba["SuspensionEstaticaEje1"]["Izquierdo"])
    est_e1_der = promedio(prueba["SuspensionEstaticaEje1"]["Derecho"])
    est_e2_izq = promedio(prueba["SuspensionEstaticaEje2"]["Izquierdo"])
    est_e2_der = promedio(prueba["SuspensionEstaticaEje2"]["Derecho"])

    print("\n--- Peso estatico promedio ---")
    print(f"Eje 1 Izquierdo: {est_e1_izq:.2f}")
    print(f"Eje 1 Derecho  : {est_e1_der:.2f}")
    print(f"Eje 2 Izquierdo: {est_e2_izq:.2f}")
    print(f"Eje 2 Derecho  : {est_e2_der:.2f}")

    # 3. Series dinamicas
    series = {
        "Suspension Dinamica Eje 1 - Izquierdo": (
            prueba["SuspensionDinamicaEje1"]["Izquierdo"], est_e1_izq),
        "Suspension Dinamica Eje 1 - Derecho": (
            prueba["SuspensionDinamicaEje1"]["Derecho"], est_e1_der),
        "Suspension Dinamica Eje 2 - Izquierdo": (
            prueba["SuspensionDinamicaEje2"]["Izquierdo"], est_e2_izq),
        "Suspension Dinamica Eje 2 - Derecho": (
            prueba["SuspensionDinamicaEje2"]["Derecho"], est_e2_der),
    }

    # 4. Figura
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"Prueba de Suspension - IdPrueba {prueba.get('IdPrueba', '')}",
                 fontsize=14, fontweight="bold")

    print("\n--- Peso dinamico minimo ---")
    for ax, (titulo, (arreglo, peso_estatico)) in zip(axes.flat, series.items()):
        muestras, valores = extraer_valores(arreglo)
        idx_min = valores.index(min(valores))
        valor_min = valores[idx_min]
        muestra_min = muestras[idx_min]
        print(f"{titulo}: {valor_min:.2f} (muestra {muestra_min})")

        ax.plot(muestras, valores, linewidth=1, color="tab:blue")
        ax.axhline(peso_estatico, color="tab:red", linestyle="--", linewidth=1.2,
                   label=f"Peso estatico promedio: {peso_estatico:.2f}")
        ax.axhline(valor_min, color="tab:green", linestyle=":", linewidth=1.2,
                   label=f"Peso dinamico minimo: {valor_min:.2f}")
        ax.plot(muestra_min, valor_min, "o", color="tab:green", markersize=6)
        ax.set_title(titulo)
        ax.set_xlabel("Numero de muestra")
        ax.set_ylabel("Valor")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # 5. Guardar PNG
    salida = Path(ruta).resolve().parent / (Path(ruta).stem + "_graficas.png")
    plt.savefig(salida, dpi=150)
    print(f"\nGrafica guardada en: {salida}")

    # 6. Ventana interactiva
    if matplotlib.get_backend().lower() != "agg":
        plt.show()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        mostrar_error(f"Ocurrio un error:\n{e}\n\n{traceback.format_exc()}")
        sys.exit(1)
