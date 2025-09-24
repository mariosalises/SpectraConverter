# spectraconverter_v4/src/ui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES
import os
import traceback
from .utils import resource_path
from PIL import Image, ImageTk, ImageEnhance

from . import data_parser
from . import data_plotter
from . import data_processor
from . import data_exporter

class MainAppWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Spectra Converter v4.0")
        self.load_view_size = "800x600"
        self.processing_view_size = "1200x700"
        self.load_view_minsize = (600, 450)
        self.processing_view_minsize = (900, 600)
        self.root.geometry(self.load_view_size)
        self.root.minsize(self.load_view_minsize[0], self.load_view_minsize[1])
        self.root.configure(bg='#E6E6FA')
        self.set_window_icon()
        
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TFrame', background='#E6E6FA')
        style.configure('TLabel', background='#E6E6FA', font=('Arial', 10))
        style.configure('Status.TLabel', font=('Arial', 9), background='#E6E6FA')
        style.configure('Drop.TLabel', background='#FFFFFF', bordercolor='#8A2BE2', foreground='#A9A9A9')
        style.map('Drop.TLabel', background=[('active', '#F0E8FF')], bordercolor=[('active', '#4B0082')], foreground=[('active', '#4B0082')])
        style.configure('TButton', padding=6, font=('Arial', 10))
        style.configure('Big.TButton', font=('Arial', 12, 'bold'), padding=10)
        style.configure('White.TFrame', background='white')
        style.configure('White.TCheckbutton', background='white')
        
        self.original_watermark_img = self.load_original_image('assets/icono.png')
        self.watermark_photo = None
        self.resize_job = None
        self.loaded_spectra = []
        self.plotter = None
        self.current_exp_type = None
        self.status_var = tk.StringVar(value="Listo para cargar archivos.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", padding=5, style='Status.TLabel')
        status_bar.pack(side="bottom", fill="x")
        self.main_container = ttk.Frame(self.root, style='TFrame')
        self.main_container.pack(expand=True, fill="both")
        self.load_frame = ttk.Frame(self.main_container, style='TFrame')
        self.processing_frame = ttk.Frame(self.main_container, style='TFrame')
        self.create_load_widgets()
        self.create_processing_widgets()
        self.show_load_view()

    def set_window_icon(self):
        try:
            icon_path = resource_path('assets/app_icon.ico')
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            print(f"Advertencia: No se pudo encontrar el icono en '{icon_path}'.")

    def load_original_image(self, relative_path):
        try:
            image_path = resource_path(relative_path)
            return Image.open(image_path).convert("RGBA")
        except Exception as e:
            print(f"Advertencia: No se pudo cargar la imagen de marca de agua: {e}")
            return None
    
    def center_window(self):
        """Centra la ventana en la pantalla."""
        # Esta línea es importante: fuerza a Tkinter a procesar cualquier
        # evento pendiente, asegurando que las dimensiones de la ventana
        # son las finales antes de intentar moverla.
        self.root.update_idletasks()
        
        # Obtenemos el tamaño de la ventana
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Obtenemos el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculamos la posición x, y para la esquina superior izquierda
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # --- LÍNEA CLAVE CORREGIDA ---
        # Ahora sí, aplicamos tanto el tamaño como la posición.
        # Esto le recuerda a la ventana sus dimensiones antes de moverla.
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def show_load_view(self):
        """Muestra la vista de carga, ajusta el tamaño y oculta la de procesamiento."""
        self.root.geometry(self.load_view_size)
        self.root.minsize(self.load_view_minsize[0], self.load_view_minsize[1])
        
        # --- CAMBIO IMPORTANTE ---
        # En lugar de centrar inmediatamente, programamos el centrado para
        # que ocurra después de un brevísimo instante (10 ms). Esto le da
        # tiempo a la ventana a dibujarse antes de intentar moverla.
        self.root.after(10, self.center_window)
        
        self.processing_frame.pack_forget()
        self.load_frame.pack(expand=True, fill="both")

    def show_processing_view(self):
        self.root.geometry(self.processing_view_size)
        self.root.minsize(self.processing_view_minsize[0], self.processing_view_minsize[1])
        self.center_window()
        self.load_frame.pack_forget()
        self.processing_frame.pack(expand=True, fill="both")
        self.plotter.plot_spectra(self.loaded_spectra, use_processed=False)
        self._populate_spectra_list()
        
    def create_load_widgets(self):
        main_frame_content = ttk.Frame(self.load_frame, padding="10", style='TFrame')
        main_frame_content.pack(expand=True, fill="both")
        self.drop_zone = ttk.Label(main_frame_content, text="Arrastra una carpeta aquí\no haz clic para seleccionar", font=("Arial", 14, "italic"), relief="solid", padding="20", anchor="center", borderwidth=2, style='Drop.TLabel', compound=tk.CENTER)
        self.drop_zone.pack(expand=True, fill="both", pady=10)
        self.setup_drop_zone_events()

    def create_processing_widgets(self):
        control_panel = ttk.Frame(self.processing_frame, width=350, style='TFrame', padding=10)
        control_panel.pack(side="left", fill="y", padx=(5,0), pady=5)
        control_panel.pack_propagate(False)
        plot_panel = ttk.Frame(self.processing_frame, style='TFrame', padding=10)
        plot_panel.pack(side="right", expand=True, fill="both", padx=(0,5), pady=5)
        ttk.Label(control_panel, text="1. Elige el tipo de experimento:", font=('Arial', 12, 'bold')).pack(anchor="w")
        exp_type_frame = ttk.Frame(control_panel, style='TFrame')
        exp_type_frame.pack(fill="x", pady=10)
        uv_vis_button = ttk.Button(exp_type_frame, text="UV-Vis / Absorción", style='Big.TButton', command=lambda: self._show_processing_options('uvvis'))
        uv_vis_button.pack(side="left", expand=True, padx=5)
        lumi_button = ttk.Button(exp_type_frame, text="Luminiscencia", style='Big.TButton', command=lambda: self._show_processing_options('lumi'))
        lumi_button.pack(side="right", expand=True, padx=5)
        self.options_container = ttk.Frame(control_panel, style='TFrame')
        self.options_container.pack(fill="x", pady=10)
        list_frame = ttk.LabelFrame(control_panel, text="2. Selecciona espectros a mostrar", padding=10)
        list_frame.pack(expand=True, fill="both", pady=10)
        
        self.spectra_list_canvas = tk.Canvas(list_frame, background="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.spectra_list_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.spectra_list_canvas, style='White.TFrame')
        self.spectra_list_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.spectra_list_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.spectra_list_canvas.pack(side="left", fill="both", expand=True)
        
        action_frame = ttk.Frame(control_panel, style='TFrame')
        action_frame.pack(side="bottom", fill="x", pady=10)
        apply_button = ttk.Button(action_frame, text="Aplicar Cambios", command=self._on_apply_processing)
        apply_button.pack(side="left", expand=True, padx=5)
        export_button = ttk.Button(action_frame, text="Exportar Resultados", command=self._on_export)
        export_button.pack(side="right", expand=True, padx=5)
        self.plotter = data_plotter.SpectraPlotter(plot_panel)

    def setup_drop_zone_events(self):
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_zone.bind('<Button-1>', self.on_drop_zone_click)
        self.drop_zone.bind('<Enter>', self.on_enter_drop_zone)
        self.drop_zone.bind('<Leave>', self.on_leave_drop_zone)
        self.drop_zone.bind('<Configure>', self.on_resize_drop_zone)

    def on_resize_drop_zone(self, event):
        if self.resize_job: self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(150, self._perform_resize, event)

    def _perform_resize(self, event):
        if not self.original_watermark_img: return
        widget_width, widget_height = event.width, event.height
        padded_width, padded_height = max(widget_width - 40, 1), max(widget_height - 40, 1)
        if padded_width < 2 or padded_height < 2: return
        img_copy = self.original_watermark_img.copy()
        img_copy.thumbnail((padded_width, padded_height), Image.LANCZOS)
        alpha = img_copy.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.15)
        img_copy.putalpha(alpha)
        self.watermark_photo = ImageTk.PhotoImage(img_copy)
        self.drop_zone.configure(image=self.watermark_photo)
        self.drop_zone.image = self.watermark_photo

    def on_enter_drop_zone(self, event):
        self.drop_zone.configure(text="¡Suelta la carpeta aquí!")
        self.drop_zone.state(['active'])
        
    def on_leave_drop_zone(self, event):
        self.drop_zone.configure(text="Arrastra una carpeta aquí\no haz clic para seleccionar")
        self.drop_zone.state(['!active'])
        
    def on_drop(self, event):
        self.on_leave_drop_zone(event) 
        path = event.data.strip('{}')
        self.process_folder(path)

    def on_drop_zone_click(self, event):
        path = filedialog.askdirectory(title="Selecciona la carpeta con los espectros")
        if path: self.process_folder(path)
            
    def process_folder(self, folder_path):
        self.status_var.set(f"Analizando carpeta: {os.path.basename(folder_path)}...")
        self.root.update_idletasks()
        if not os.path.isdir(folder_path):
            self.status_var.set("Error: La ruta soltada no es una carpeta válida."); return
        
        files_to_process = [f for f in os.listdir(folder_path) if f.lower().endswith(('.txt', '.asc'))]
        if not files_to_process:
            self.status_var.set(f"Aviso: No se encontraron archivos .txt o .asc."); return

        self.loaded_spectra.clear()
        for filename in files_to_process:
            full_path = os.path.join(folder_path, filename)
            self.status_var.set(f"Parseando: {filename}...")
            self.root.update_idletasks()
            df = data_parser.parse_spectrum_file(full_path)
            if df is not None:
                self.loaded_spectra.append({'filename': filename, 'dataframe': df, 'processed_dataframe': None})

        if not self.loaded_spectra:
            self.status_var.set("Proceso finalizado. No se pudieron cargar datos válidos.")
            messagebox.showwarning("Sin datos", "No se pudo extraer ningún espectro válido.")
            return

        self.status_var.set(f"¡Éxito! Se cargaron {len(self.loaded_spectra)} espectros.")
        self.show_processing_view()

    def _populate_spectra_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.spectra_vars = {}
        for spectrum in self.loaded_spectra:
            filename = spectrum['filename']
            var = tk.BooleanVar(value=True)
            self.spectra_vars[filename] = var
            cb = ttk.Checkbutton(self.scrollable_frame, text=filename, variable=var, 
                                 command=lambda f=filename, v=var: self.plotter.toggle_spectrum_visibility(f, v.get()),
                                 style='White.TCheckbutton')
            cb.pack(anchor="w", padx=5, pady=2)
            
        self.scrollable_frame.update_idletasks()
        self.spectra_list_canvas.config(scrollregion=self.spectra_list_canvas.bbox("all"))

    def _show_processing_options(self, exp_type):
        for widget in self.options_container.winfo_children(): widget.destroy()
        self.status_var.set(f"Modo de procesamiento: {exp_type.upper()}")
        self.current_exp_type = exp_type
        if exp_type == 'lumi':
            options_frame = ttk.LabelFrame(self.options_container, text="Opciones de Procesamiento de Luminiscencia", padding=10)
            options_frame.pack(fill="x")
            smoothing_label = ttk.Label(options_frame, text="Método de Suavizado:", font=('Arial', 10, 'bold'))
            smoothing_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
            self.smoothing_method = tk.StringVar(value="none")
            ttk.Radiobutton(options_frame, text="Sin Suavizado", variable=self.smoothing_method, value="none", command=self._update_options_visibility).grid(row=1, column=0, sticky="w")
            ttk.Radiobutton(options_frame, text="Promedio Móvil", variable=self.smoothing_method, value="moving_average", command=self._update_options_visibility).grid(row=2, column=0, sticky="w")
            ttk.Radiobutton(options_frame, text="Savitzky-Golay", variable=self.smoothing_method, value="savgol", command=self._update_options_visibility).grid(row=3, column=0, sticky="w")
            self.ma_params_frame = ttk.Frame(options_frame, style='TFrame')
            ttk.Label(self.ma_params_frame, text="Tamaño Ventana:").pack(side="left", padx=(10, 5))
            self.ma_window = tk.IntVar(value=5)
            ttk.Spinbox(self.ma_params_frame, from_=3, to=101, increment=2, textvariable=self.ma_window, width=5).pack(side="left")
            self.sg_params_frame = ttk.Frame(options_frame, style='TFrame')
            ttk.Label(self.sg_params_frame, text="Ventana:").pack(side="left", padx=(10, 5))
            self.sg_window = tk.IntVar(value=11)
            ttk.Spinbox(self.sg_params_frame, from_=5, to=101, increment=2, textvariable=self.sg_window, width=5).pack(side="left")
            ttk.Label(self.sg_params_frame, text="Orden Pol.:").pack(side="left", padx=(10, 5))
            self.sg_order = tk.IntVar(value=2)
            ttk.Spinbox(self.sg_params_frame, from_=1, to=10, textvariable=self.sg_order, width=5).pack(side="left")
            self.ma_params_frame.grid(row=2, column=1, sticky="w")
            self.sg_params_frame.grid(row=3, column=1, sticky="w")
        elif exp_type == 'uvvis':
            options_frame = ttk.LabelFrame(self.options_container, text="Opciones de Corrección de Línea Base", padding=10)
            options_frame.pack(fill="x")
            self.baseline_method = tk.StringVar(value="none")
            ttk.Radiobutton(options_frame, text="Sin Corrección", variable=self.baseline_method, value="none", command=self._update_options_visibility).grid(row=1, column=0, sticky="w")
            ttk.Radiobutton(options_frame, text="Restar Mínimo", variable=self.baseline_method, value="min", command=self._update_options_visibility).grid(row=2, column=0, sticky="w")
            ttk.Radiobutton(options_frame, text="airPLS Automático", variable=self.baseline_method, value="airpls", command=self._update_options_visibility).grid(row=3, column=0, sticky="w")
            self.airpls_params_frame = ttk.Frame(options_frame, style='TFrame')
            ttk.Label(self.airpls_params_frame, text="Suavidad (λ):").pack(side="left", padx=(10, 5))
            self.airpls_lam = tk.DoubleVar(value=1e7)
            ttk.Entry(self.airpls_params_frame, textvariable=self.airpls_lam, width=8).pack(side="left")
            ttk.Label(self.airpls_params_frame, text="Asimetría (p):").pack(side="left", padx=(10, 5))
            self.airpls_p = tk.DoubleVar(value=0.01)
            ttk.Entry(self.airpls_params_frame, textvariable=self.airpls_p, width=8).pack(side="left")
            self.airpls_params_frame.grid(row=3, column=1, sticky="w")
        self._update_options_visibility()

    def _update_options_visibility(self):
        if hasattr(self, 'smoothing_method'):
            selected_smoothing = self.smoothing_method.get()
            if selected_smoothing == 'moving_average': self.ma_params_frame.grid()
            else: self.ma_params_frame.grid_remove()
            if selected_smoothing == 'savgol': self.sg_params_frame.grid()
            else: self.sg_params_frame.grid_remove()
        if hasattr(self, 'baseline_method'):
            selected_baseline = self.baseline_method.get()
            if selected_baseline == 'airpls': self.airpls_params_frame.grid()
            else: self.airpls_params_frame.grid_remove()

    def _on_apply_processing(self):
        if not self.loaded_spectra or self.current_exp_type is None:
            messagebox.showwarning("Sin Selección", "Por favor, carga datos y selecciona un tipo de experimento primero.")
            return
        method, params = 'none', {}
        if self.current_exp_type == 'uvvis':
            method = self.baseline_method.get()
            if method == 'airpls': params = {'lam': self.airpls_lam.get(), 'p': self.airpls_p.get()}
        elif self.current_exp_type == 'lumi':
            method = self.smoothing_method.get()
            if method == 'moving_average': params = {'window': self.ma_window.get()}
            elif method == 'savgol': params = {'window': self.sg_window.get(), 'order': self.sg_order.get()}
        if method == 'none':
            for spec in self.loaded_spectra: spec['processed_dataframe'] = None
            self.plotter.plot_spectra(self.loaded_spectra, use_processed=False)
            self.status_var.set("Mostrando datos crudos originales.")
            return
        self.status_var.set(f"Aplicando '{method}' a {len(self.loaded_spectra)} espectros...")
        self.root.update_idletasks()
        for spectrum in self.loaded_spectra:
            spectrum['processed_dataframe'] = data_processor.process_spectrum(spectrum['dataframe'], method, params)
        self.plotter.plot_spectra(self.loaded_spectra, use_processed=True)
        for filename, var in self.spectra_vars.items(): self.plotter.toggle_spectrum_visibility(filename, var.get())
        self.status_var.set(f"Procesamiento '{method}' aplicado con éxito.")

    def _on_export(self):
        """
        Se ejecuta al pulsar 'Exportar Resultados'.
        Genera archivo Excel y archivo de datos TSV para SciDAVis.
        """
        if not self.loaded_spectra:
            messagebox.showwarning("Sin Datos", "No hay datos cargados para exportar.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Guardar como (nombre base para los archivos)",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            initialfile="Resultados_Espectros"
        )
        
        if not file_path:
            self.status_var.set("Exportación cancelada.")
            return

        base_path, _ = os.path.splitext(file_path)
        excel_path = base_path + ".xlsx"
        scidavis_tsv_path = base_path + "_SciDAVis.tsv" # Nombre más claro

        try:
            self.status_var.set(f"Exportando a Excel...")
            self.root.update_idletasks()
            data_exporter.export_to_excel(self.loaded_spectra, excel_path)

            self.status_var.set(f"Generando archivo de datos para SciDAVis...")
            self.root.update_idletasks()
            data_exporter.export_to_scidavis(self.loaded_spectra, scidavis_tsv_path)

            self.status_var.set("¡Exportación completada con éxito!")
            messagebox.showinfo("Éxito", 
                                f"Los resultados se han guardado correctamente en:\n\n"
                                f"• {os.path.basename(excel_path)}\n"
                                f"• {os.path.basename(scidavis_tsv_path)}")
        
        except Exception as e:
            self.status_var.set("Error durante la exportación.")
            self.show_error(e)

    def show_error(self, *args):
        err = traceback.format_exc()
        messagebox.showerror("Error Inesperado", "Ha ocurrido un error inesperado...\n\n" + str(err))