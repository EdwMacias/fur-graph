import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import statistics


class VisorFrenosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visor de Datos de Frenos")
        self.root.geometry("1400x900")
        
        self.datos = None
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Frame superior para botones
        frame_superior = ttk.Frame(self.root, padding="10")
        frame_superior.pack(fill=tk.X)
        
        # Botón para cargar archivo
        btn_cargar = ttk.Button(
            frame_superior, 
            text="Cargar JSON", 
            command=self.cargar_archivo
        )
        btn_cargar.pack(side=tk.LEFT, padx=5)
        
        # Label para mostrar archivo cargado
        self.label_archivo = ttk.Label(frame_superior, text="No hay archivo cargado")
        self.label_archivo.pack(side=tk.LEFT, padx=20)
        
        # Frame para controles de límites de ejes
        frame_limites = ttk.LabelFrame(self.root, text="Límites de Ejes Y", padding="10")
        frame_limites.pack(fill=tk.X, padx=10, pady=5)
        
        # Controles para Pesos
        ttk.Label(frame_limites, text="Pesos:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        ttk.Label(frame_limites, text="Mín:").grid(row=0, column=1, padx=5, pady=5)
        self.peso_min = ttk.Entry(frame_limites, width=10)
        self.peso_min.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(frame_limites, text="Máx:").grid(row=0, column=3, padx=5, pady=5)
        self.peso_max = ttk.Entry(frame_limites, width=10)
        self.peso_max.grid(row=0, column=4, padx=5, pady=5)
        
        # Controles para Fuerzas
        ttk.Label(frame_limites, text="Fuerzas:", font=('Arial', 9, 'bold')).grid(
            row=0, column=5, padx=(20, 5), pady=5, sticky='w'
        )
        ttk.Label(frame_limites, text="Mín:").grid(row=0, column=6, padx=5, pady=5)
        self.fuerza_min = ttk.Entry(frame_limites, width=10)
        self.fuerza_min.grid(row=0, column=7, padx=5, pady=5)
        
        ttk.Label(frame_limites, text="Máx:").grid(row=0, column=8, padx=5, pady=5)
        self.fuerza_max = ttk.Entry(frame_limites, width=10)
        self.fuerza_max.grid(row=0, column=9, padx=5, pady=5)
        
        # Botones para aplicar y restablecer
        btn_aplicar = ttk.Button(
            frame_limites, 
            text="Aplicar Límites", 
            command=self.aplicar_limites
        )
        btn_aplicar.grid(row=0, column=10, padx=10, pady=5)
        
        btn_restablecer = ttk.Button(
            frame_limites, 
            text="Restablecer", 
            command=self.restablecer_limites
        )
        btn_restablecer.grid(row=0, column=11, padx=5, pady=5)
        
        # Frame para estadísticas
        self.frame_stats = ttk.LabelFrame(self.root, text="Estadísticas", padding="10")
        self.frame_stats.pack(fill=tk.X, padx=10, pady=5)
        
        # Frame para gráficas
        self.frame_graficas = ttk.Frame(self.root)
        self.frame_graficas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def aplicar_limites(self):
        """Aplica los límites personalizados a las gráficas"""
        if not self.datos:
            messagebox.showwarning("Advertencia", "Primero carga un archivo JSON")
            return
        
        # Refrescar las gráficas con los nuevos límites
        self.mostrar_datos()
    
    def restablecer_limites(self):
        """Restablece los límites automáticos de las gráficas"""
        self.peso_min.delete(0, tk.END)
        self.peso_max.delete(0, tk.END)
        self.fuerza_min.delete(0, tk.END)
        self.fuerza_max.delete(0, tk.END)
        
        if self.datos:
            self.mostrar_datos()
    
    def cargar_archivo(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo JSON",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    self.datos = json.load(f)
                
                # Verificar que sea una lista con al menos un elemento
                if isinstance(self.datos, list) and len(self.datos) > 0:
                    self.datos = self.datos[0]  # Tomar el primer elemento
                    
                self.label_archivo.config(text=f"Archivo: {archivo.split('/')[-1]}")
                self.mostrar_datos()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar el archivo:\n{str(e)}")
    
    def calcular_estadisticas(self):
        """Calcula las estadísticas de pesos (promedio y desviación estándar) y fuerzas (máximo)"""
        stats = {}
        
        # Estadísticas de Pesos (Promedio y Desviación Estándar)
        suma_pesos = 0
        for eje in ['PesosEje1', 'PesosEje2']:
            if eje in self.datos['PesosEjes']:
                valores = [item['Valor'] for item in self.datos['PesosEjes'][eje]]
                promedio = statistics.mean(valores)
                stats[f'{eje}_promedio'] = promedio
                stats[f'{eje}_desviacion'] = statistics.stdev(valores)
                suma_pesos += promedio
        
        # Estadísticas de Fuerzas (Máximo)
        suma_fuerzas = 0
        for eje in ['FuerzasEje1', 'FuerzasEje2']:
            if eje in self.datos['FuerzasEjes']:
                valores = [item['Valor'] for item in self.datos['FuerzasEjes'][eje]]
                maximo = max(valores)
                stats[f'{eje}_maximo'] = maximo
                suma_fuerzas += maximo
        
        # Calcular Eficacia Total
        # EfiTotal = (suma Fuerzas) / (suma de pesos) * 100
        if suma_pesos > 0:
            stats['eficacia_total'] = (suma_fuerzas / suma_pesos) * 100
        else:
            stats['eficacia_total'] = 0
        
        return stats
    
    def mostrar_estadisticas(self, stats):
        """Muestra las estadísticas en el frame de estadísticas"""
        # Limpiar frame anterior
        for widget in self.frame_stats.winfo_children():
            widget.destroy()
        
        # Crear grid para estadísticas
        row = 0
        
        # Encabezados
        ttk.Label(self.frame_stats, text="Métrica", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, padx=10, pady=5, sticky='w'
        )
        ttk.Label(self.frame_stats, text="Valor", font=('Arial', 10, 'bold')).grid(
            row=row, column=1, padx=10, pady=5, sticky='w'
        )
        
        row += 1
        ttk.Separator(self.frame_stats, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=5
        )
        
        # Pesos Eje 1
        row += 1
        ttk.Label(self.frame_stats, text="Peso Eje 1 (Promedio):").grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['PesosEje1_promedio']:.2f}").grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
        
        # Desviación Estándar Eje 1
        row += 1
        ttk.Label(self.frame_stats, text="Peso Eje 1 (Desviación Estándar):").grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['PesosEje1_desviacion']:.2f}").grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
        
        # Pesos Eje 2
        row += 1
        ttk.Label(self.frame_stats, text="Peso Eje 2 (Promedio):").grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['PesosEje2_promedio']:.2f}").grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
        
        # Desviación Estándar Eje 2
        row += 1
        ttk.Label(self.frame_stats, text="Peso Eje 2 (Desviación Estándar):").grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['PesosEje2_desviacion']:.2f}").grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
        
        row += 1
        ttk.Separator(self.frame_stats, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=5
        )
        
        # Fuerza Eje 1
        row += 1
        ttk.Label(self.frame_stats, text="Fuerza Eje 1 (Máximo):").grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['FuerzasEje1_maximo']:.2f}").grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
        
        # Fuerza Eje 2
        row += 1
        ttk.Label(self.frame_stats, text="Fuerza Eje 2 (Máximo):").grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['FuerzasEje2_maximo']:.2f}").grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
        
        row += 1
        ttk.Separator(self.frame_stats, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=5
        )
        
        # Eficacia Total
        row += 1
        ttk.Label(self.frame_stats, text="Eficacia Total:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, padx=10, pady=3, sticky='w'
        )
        ttk.Label(self.frame_stats, text=f"{stats['eficacia_total']:.2f} %", 
                 font=('Arial', 10, 'bold'), foreground='#0066cc').grid(
            row=row, column=1, padx=10, pady=3, sticky='w'
        )
    
    def mostrar_datos(self):
        """Muestra las gráficas y estadísticas de los datos cargados"""
        if not self.datos:
            return
        
        # Calcular estadísticas
        stats = self.calcular_estadisticas()
        self.mostrar_estadisticas(stats)
        
        # Limpiar frame de gráficas
        for widget in self.frame_graficas.winfo_children():
            widget.destroy()
        
        # Crear figura con subplots
        fig = Figure(figsize=(14, 8))
        
        # Subplot 1: Pesos Eje 1
        ax1 = fig.add_subplot(2, 2, 1)
        self.graficar_datos(
            ax1, 
            self.datos['PesosEjes']['PesosEje1'],
            "Pesos Eje 1",
            "Muestra",
            "Peso",
            stats['PesosEje1_promedio'],
            'promedio'
        )
        
        # Subplot 2: Pesos Eje 2
        ax2 = fig.add_subplot(2, 2, 2)
        self.graficar_datos(
            ax2,
            self.datos['PesosEjes']['PesosEje2'],
            "Pesos Eje 2",
            "Muestra",
            "Peso",
            stats['PesosEje2_promedio'],
            'promedio'
        )
        
        # Subplot 3: Fuerzas Eje 1
        ax3 = fig.add_subplot(2, 2, 3)
        self.graficar_datos(
            ax3,
            self.datos['FuerzasEjes']['FuerzasEje1'],
            "Fuerzas Eje 1",
            "Muestra",
            "Fuerza",
            stats['FuerzasEje1_maximo'],
            'máximo'
        )
        
        # Subplot 4: Fuerzas Eje 2
        ax4 = fig.add_subplot(2, 2, 4)
        self.graficar_datos(
            ax4,
            self.datos['FuerzasEjes']['FuerzasEje2'],
            "Fuerzas Eje 2",
            "Muestra",
            "Fuerza",
            stats['FuerzasEje2_maximo'],
            'máximo'
        )
        
        fig.tight_layout()
        
        # Integrar la figura en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def graficar_datos(self, ax, datos, titulo, xlabel, ylabel, valor_estadistica, tipo_estadistica):
        """Crea una gráfica de líneas con la línea de estadística"""
        # Extraer datos
        muestras = [item['NumeroMuestra'] for item in datos]
        valores = [item['Valor'] for item in datos]
        
        # Gráfica de líneas
        ax.plot(muestras, valores, 'b-', linewidth=2, label='Valores')
        
        # Línea de estadística (promedio o máximo)
        ax.axhline(
            y=valor_estadistica, 
            color='r', 
            linestyle='--', 
            linewidth=2,
            label=f'{tipo_estadistica.capitalize()}: {valor_estadistica:.2f}'
        )
        
        # Configuración de la gráfica
        ax.set_title(titulo, fontsize=12, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Aplicar límites personalizados del eje Y si están definidos
        if ylabel == "Peso":
            try:
                y_min = self.peso_min.get().strip()
                y_max = self.peso_max.get().strip()
                if y_min and y_max:
                    ax.set_ylim(float(y_min), float(y_max))
                elif y_min:
                    ax.set_ylim(bottom=float(y_min))
                elif y_max:
                    ax.set_ylim(top=float(y_max))
            except ValueError:
                pass  # Si hay error en la conversión, usar límites automáticos
        
        elif ylabel == "Fuerza":
            try:
                y_min = self.fuerza_min.get().strip()
                y_max = self.fuerza_max.get().strip()
                if y_min and y_max:
                    ax.set_ylim(float(y_min), float(y_max))
                elif y_min:
                    ax.set_ylim(bottom=float(y_min))
                elif y_max:
                    ax.set_ylim(top=float(y_max))
            except ValueError:
                pass  # Si hay error en la conversión, usar límites automáticos


def main():
    root = tk.Tk()
    app = VisorFrenosApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()