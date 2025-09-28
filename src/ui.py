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
        
        self._create_menu()
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
        self.last_clicked_index = None
        self.processing_applied = False

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

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

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
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def show_load_view(self):
        self.root.geometry(self.load_view_size)
        self.root.minsize(self.load_view_minsize[0], self.load_view_minsize[1])
        self.root.after(10, self.center_window)
        self.processing_frame.pack_forget()
        self.load_frame.pack(expand=True, fill="both")

    def show_processing_view(self):
        self.root.geometry(self.processing_view_size)
        self.root.minsize(self.processing_view_minsize[0], self.processing_view_minsize[1])
        self.root.after(10, self.center_window)
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
        
        # --- ARREGLO DEL LAYOUT: Los botones de acción se sacan del área de scroll ---
        action_frame = ttk.Frame(control_panel, style='TFrame')
        action_frame.pack(side="bottom", fill="x", pady=(10,0))
        apply_button = ttk.Button(action_frame, text="Aplicar Cambios", command=self._on_apply_processing)
        apply_button.pack(side="left", fill="x", expand=True, padx=2)
        reset_button = ttk.Button(action_frame, text="Restablecer", command=self._on_reset_processing)
        reset_button.pack(side="left", fill="x", expand=True, padx=2)
        export_button = ttk.Button(action_frame, text="Exportar", command=self._on_export)
        export_button.pack(side="right", fill="x", expand=True, padx=2)

        # --- ARREGLO DEL LAYOUT: El resto del contenido va en un frame que SÍ se expande ---
        scrollable_content_frame = ttk.Frame(control_panel, style='TFrame')
        scrollable_content_frame.pack(side="top", fill="both", expand=True)
        
        ttk.Label(scrollable_content_frame, text="1. Elige el tipo de experimento:", font=('Arial', 12, 'bold')).pack(anchor="w", fill="x")
        exp_type_frame = ttk.Frame(scrollable_content_frame, style='TFrame')
        exp_type_frame.pack(fill="x", pady=10)
        uv_vis_button = ttk.Button(exp_type_frame, text="UV-Vis / Absorción", style='Big.TButton', command=lambda: self._show_processing_options('uvvis'))
        uv_vis_button.pack(side="left", fill="x", expand=True, padx=2)
        lumi_button = ttk.Button(exp_type_frame, text="Luminiscencia", style='Big.TButton', command=lambda: self._show_processing_options('lumi'))
        lumi_button.pack(side="right", fill="x", expand=True, padx=2)
        
        self.options_container = ttk.Frame(scrollable_content_frame, style='TFrame')
        self.options_container.pack(fill="x", pady=10)
        
        list_frame = ttk.LabelFrame(scrollable_content_frame, text="2. Selecciona espectros", padding=10)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        self.spectra_list_canvas = tk.Canvas(list_frame, background="#FFFFFF", highlightthickness=0)
        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.spectra_list_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.spectra_list_canvas, style='White.TFrame')
        self.spectra_list_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.spectra_list_canvas.configure(yscrollcommand=list_scrollbar.set)
        list_scrollbar.pack(side="right", fill="y")
        self.spectra_list_canvas.pack(side="left", fill="both", expand=True)
        
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
        if path: self.process_folder(path)

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
        self.processing_applied = False
        self.show_processing_view()

    def _populate_spectra_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.spectra_vars = {}
        self.ordered_filenames = [spec['filename'] for spec in self.loaded_spectra]
        
        for filename in self.ordered_filenames:
            var = tk.BooleanVar(value=True)
            self.spectra_vars[filename] = var
            cb = ttk.Checkbutton(self.scrollable_frame, text=filename, variable=var, style='White.TCheckbutton')
            # Usamos solo .bind() para tener un único punto de control.
            cb.bind("<Button-1>", lambda event, f=filename: self._on_spectrum_click(event, f))
            cb.pack(anchor="w", padx=5, pady=2)
            
        self.scrollable_frame.update_idletasks()
        self.spectra_list_canvas.config(scrollregion=self.spectra_list_canvas.bbox("all"))
        self.last_clicked_index = None

    def _on_spectrum_click(self, event, filename):
        """
        Lógica de selección UNIFICADA Y CORRECTA usando after_idle.
        """
        current_index = self.ordered_filenames.index(filename)

        # Deferir la lógica hasta que el checkbox haya actualizado su variable interna
        def process_click():
            var = self.spectra_vars[filename]
            new_state = var.get()  # Ahora sí, este es el estado final y correcto

            is_shift = (event.state & 0x0001) != 0
            is_ctrl = (event.state & 0x0004) != 0

            if is_shift and self.last_clicked_index is not None:
                # Lógica de Shift-Clic
                start = min(self.last_clicked_index, current_index)
                end = max(self.last_clicked_index, current_index)

                # Aplicar el nuevo estado del ítem clickeado a todo el rango
                for i in range(start, end + 1):
                    fname = self.ordered_filenames[i]
                    self.spectra_vars[fname].set(new_state)

                # Usar la actualización completa y lenta porque hemos modificado un bloque
                self._update_full_plot_visibility()

            elif is_ctrl:
                # Ctrl-Clic: Se respeta el cambio y no se toca el ancla
                self._update_single_line_visibility(filename)

            else:
                # Clic normal: Se respeta el cambio y se establece un nuevo ancla
                self._update_single_line_visibility(filename)
                self.last_clicked_index = current_index

        # Pospone la ejecución de 'process_click' hasta que tkinter esté "libre"
        # (es decir, después de que haya procesado el cambio de estado del checkbox)
        event.widget.after_idle(process_click)
        
    def _update_single_line_visibility(self, filename):
        """Actualización RÁPIDA: solo cambia una línea y redibuja el canvas."""
        if not self.plotter: return
        is_visible = self.spectra_vars[filename].get()
        self.plotter.toggle_spectrum_visibility(filename, is_visible)
        self.plotter.canvas.draw()

    def _update_full_plot_visibility(self):
        """Actualización COMPLETA: cambia todas las líneas y reconstruye la leyenda."""
        if not self.plotter: return
        for filename, var in self.spectra_vars.items():
            self.plotter.toggle_spectrum_visibility(filename, var.get())
        self.plotter.redraw_legend_and_canvas()
    
    def _show_processing_options(self, exp_type):
        if hasattr(self, 'current_exp_type') and self.current_exp_type == exp_type and self.options_container.winfo_children():
            for widget in self.options_container.winfo_children():
                widget.destroy()
            self.current_exp_type = None
            self.status_var.set("Selecciona un tipo de experimento.")
            return

        for widget in self.options_container.winfo_children(): widget.destroy()
        self.status_var.set(f"Modo de procesamiento: {exp_type.upper()}")
        self.current_exp_type = exp_type

        if exp_type == 'lumi':
            options_frame = ttk.LabelFrame(self.options_container, text="Opciones de Procesamiento de Luminiscencia", padding=10)
            options_frame.pack(fill="x")
            self.lumi_normalize = tk.BooleanVar(value=False)
            ttk.Checkbutton(options_frame, text="Normalizar al máximo (0 a 1)", variable=self.lumi_normalize).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
            smoothing_label = ttk.Label(options_frame, text="Método de Suavizado:", font=('Arial', 10, 'bold'))
            smoothing_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))
            self.smoothing_method = tk.StringVar(value="none")
            ttk.Radiobutton(options_frame, text="Sin Suavizado", variable=self.smoothing_method, value="none", command=self._update_options_visibility).grid(row=2, column=0, sticky="w")
            ttk.Radiobutton(options_frame, text="Promedio Móvil", variable=self.smoothing_method, value="moving_average", command=self._update_options_visibility).grid(row=3, column=0, sticky="w")
            ttk.Radiobutton(options_frame, text="Savitzky-Golay", variable=self.smoothing_method, value="savgol", command=self._update_options_visibility).grid(row=4, column=0, sticky="w")
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
            self.ma_params_frame.grid(row=3, column=1, sticky="w")
            self.sg_params_frame.grid(row=4, column=1, sticky="w")

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
            method = self.smoothing_method.get()
            if hasattr(self, 'ma_params_frame'): self.ma_params_frame.grid_remove()
            if hasattr(self, 'sg_params_frame'): self.sg_params_frame.grid_remove()
            if method == 'moving_average': self.ma_params_frame.grid()
            elif method == 'savgol': self.sg_params_frame.grid()
        
        if hasattr(self, 'baseline_method'):
            method = self.baseline_method.get()
            if hasattr(self, 'airpls_params_frame'):
                self.airpls_params_frame.grid_remove()
                if method == 'airpls': self.airpls_params_frame.grid()

    def _on_apply_processing(self):
        if not self.loaded_spectra or self.current_exp_type is None:
            messagebox.showwarning("Sin Selección", "Por favor, carga datos y selecciona un tipo de experimento primero.")
            return

        processing_steps = {}
        try:
            if self.current_exp_type == 'lumi':
                processing_steps['normalize'] = self.lumi_normalize.get()
                method = self.smoothing_method.get()
                if method != 'none':
                    processing_steps['method'] = method
                    if method == 'moving_average':
                        processing_steps['params'] = {'window': self.ma_window.get()}
                    elif method == 'savgol':
                        if self.sg_window.get() <= self.sg_order.get():
                            messagebox.showwarning("Parámetro Inválido", "En Savitzky-Golay, la 'Ventana' debe ser mayor que el 'Orden Pol.'")
                            return
                        processing_steps['params'] = {'window': self.sg_window.get(), 'order': self.sg_order.get()}

            elif self.current_exp_type == 'uvvis':
                method = self.baseline_method.get()
                if method != 'none':
                    processing_steps['method'] = method
                    if method == 'airpls':
                        processing_steps['params'] = {'lam': self.airpls_lam.get(), 'p': self.airpls_p.get()}
        
        except (ValueError, tk.TclError) as e:
            messagebox.showerror("Error de Parámetro", f"Valor de parámetro inválido: {e}")
            return
        
        if not any(processing_steps.values()):
            self._on_reset_processing()
            self.status_var.set("Ningún procesamiento seleccionado.")
            return

        selected_filenames = {filename for filename, var in self.spectra_vars.items() if var.get()}
        if not selected_filenames:
            messagebox.showinfo("Sin Selección", "Ningún espectro está seleccionado para procesar.")
            return

        self.status_var.set(f"Aplicando procesamiento a {len(selected_filenames)} espectros...")
        self.root.update_idletasks()
        
        for spectrum in self.loaded_spectra:
            if spectrum['filename'] in selected_filenames:
                spectrum['processed_dataframe'] = data_processor.process_spectrum(spectrum['dataframe'], processing_steps)
                self.root.update_idletasks() # Mantiene la UI reactiva durante el bucle

        self.plotter.plot_spectra(self.loaded_spectra, use_processed=True)
        self._update_full_plot_visibility()
        self.status_var.set("Procesamiento aplicado con éxito.")
        self.processing_applied = True

    def _on_export(self):
        if not self.loaded_spectra:
            messagebox.showwarning("Sin Datos", "No hay datos cargados para exportar.")
            return False
        
        spectra_to_export = []
        for spectrum in self.loaded_spectra:
            if self.spectra_vars.get(spectrum['filename']) and self.spectra_vars[spectrum['filename']].get():
                spectra_to_export.append(spectrum)

        if not spectra_to_export:
            messagebox.showwarning("Sin Selección", "No has seleccionado ningún espectro para exportar.")
            return False

        file_path = filedialog.asksaveasfilename(
            title="Guardar como (nombre base para los archivos)",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            initialfile="Resultados_Espectros"
        )
        
        if not file_path:
            self.status_var.set("Exportación cancelada.")
            return False

        base_path, _ = os.path.splitext(file_path)
        excel_path = base_path + ".xlsx"
        scidavis_tsv_path = base_path + "_SciDAVis.tsv"

        try:
            self.status_var.set(f"Exportando {len(spectra_to_export)} espectros a Excel...")
            self.root.update_idletasks()
            data_exporter.export_to_excel(spectra_to_export, excel_path)

            self.status_var.set(f"Generando archivo de datos para SciDAVis...")
            self.root.update_idletasks()
            data_exporter.export_to_scidavis(spectra_to_export, scidavis_tsv_path)

            self.status_var.set("¡Exportación completada con éxito!")
            messagebox.showinfo("Éxito", 
                                f"Los {len(spectra_to_export)} espectros seleccionados se han guardado en:\n\n"
                                f"• {os.path.basename(excel_path)}\n"
                                f"• {os.path.basename(scidavis_tsv_path)}")
            
            self.processing_applied = False 
            return True 
        
        except Exception as e:
            self.status_var.set("Error durante la exportación.")
            self.show_error(e)
            return False

    def show_error(self, *args):
        err = traceback.format_exc()
        messagebox.showerror("Error Inesperado", "Ha ocurrido un error inesperado...\n\n" + str(err))

    def _create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar Nueva Carpeta", command=self._return_to_load_view)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de...", command=self._show_about_dialog)

    def _return_to_load_view(self):
        if self.processing_applied:
            if not messagebox.askokcancel("Confirmar", "Hay cambios sin exportar. ¿Seguro que quieres descartarlos y cargar una nueva carpeta?"):
                return

        self.loaded_spectra.clear()
        if self.plotter:
            self.plotter.ax.clear()
            self.plotter.ax.grid(True, linestyle='--', alpha=0.6)
            self.plotter.canvas.draw()
        if hasattr(self, 'scrollable_frame'):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
        if hasattr(self, 'options_container'):
            for widget in self.options_container.winfo_children():
                widget.destroy()
        
        self.status_var.set("Listo para cargar archivos.")
        self.processing_applied = False
        
        self.show_load_view()
        
        self.root.after(100, lambda: self.on_drop_zone_click(None))

    def _show_about_dialog(self):
        messagebox.showinfo(
            "Acerca de Spectra Converter",
            "Spectra Converter v4.0\n\nUna herramienta para facilitar el análisis de espectros.\nCreada con cariño y mucho Python."
        )

    def _on_reset_processing(self):
        for spec in self.loaded_spectra:
            spec['processed_dataframe'] = None
        
        self.plotter.plot_spectra(self.loaded_spectra, use_processed=False)
        self._update_full_plot_visibility()
        self.status_var.set("Procesamiento restablecido a los datos originales.")
        self.processing_applied = False

    def _on_closing(self):
        if not self.processing_applied:
            self.root.destroy()
            return

        response = messagebox.askyesnocancel(
            "Salir",
            "Hay cambios sin exportar. ¿Quieres guardarlos antes de salir?",
            icon='warning'
        )

        if response is True:
            if self._on_export():
                self.root.destroy()
        elif response is False:
            self.root.destroy()