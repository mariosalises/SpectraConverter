# spectraconverter_v4/src/data_plotter.py

import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

class SpectraPlotter:
    def __init__(self, parent_frame):
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        
        # Empaquetamos el widget del lienzo para que llene el frame contenedor
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, parent_frame)
        self.toolbar.update()
        
        self.plotted_lines = {}

    def plot_spectra(self, spectra_data, use_processed=False):
        """
        Dibuja los espectros. Esta es la función que se encarga del renderizado final.
        """
        self.ax.clear()
        self.plotted_lines.clear()

        y_label = "Intensidad (procesado)" if use_processed else "Intensidad (crudo)"

        for spectrum in spectra_data:
            filename = spectrum['filename']
            df_to_plot = spectrum['processed_dataframe'] if use_processed and spectrum['processed_dataframe'] is not None else spectrum['dataframe']
            y_col_name = 'intensity'
            
            line, = self.ax.plot(df_to_plot['wavelength'], df_to_plot[y_col_name], label=filename)
            self.plotted_lines[filename] = line
        
        self.ax.set_xlabel("Longitud de onda (nm)")
        self.ax.set_ylabel(y_label)
        self.ax.legend()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        # Llamamos a tight_layout() justo ANTES de dibujar
        try:
            self.fig.tight_layout()
        except Exception as e:
            print(f"Advertencia de Matplotlib: No se pudo aplicar tight_layout. {e}")

        self.canvas.draw()

    def toggle_spectrum_visibility(self, filename, is_visible):
        if filename in self.plotted_lines:
            line = self.plotted_lines[filename]
            line.set_visible(is_visible)
            
            # La forma más segura es recrear la leyenda
            self.ax.legend()
            
            self.canvas.draw()