# tabs/tab_salidas.py
# ----------------------------------------------------
# Módulo de pestaña SALIDAS con estilo unificado, paginación visible y resaltado.
# ----------------------------------------------------

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import csv

from database import (
    obtener_entradas,
    obtener_salidas,
    agregar_salida,
    actualizar_salida,
    eliminar_salida,
    calcular_inventario,
)

from ui_utils import (
    create_frame,
    create_label,
    create_entry,
    create_combobox,
    create_button,
    create_search_bar,
    apply_table_style,
)

# --- Tooltip simple para mostrar comentarios largos ---
class Tooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def show(self, text, x, y):
        self.hide()
        if not text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=text, justify='left', background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Segoe UI", 9), wraplength=600)
        label.pack(ipadx=5, ipady=3)
        tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class TabSalidas:
    def __init__(self, master):
        self.master = master
        try:
            self.master.configure(fg_color="#2f2f2f")
        except Exception:
            pass

        # Estados de control
        self.page = 0
        self.items_per_page = 10
        self.sort_by = None
        self.sort_reverse = False
        self.selected_id = None
        self.last_highlighted = None

        self.salidas_full = []
        self.tooltip = Tooltip(self.master)

        self._crear_interfaz()
        self._actualizar_productos()
        self.mostrar_salidas()

    # ---------------------------------------------------
    # INTERFAZ
    # ---------------------------------------------------
    def _crear_interfaz(self):
        top_outer = create_frame(self.master)
        top_outer.pack(fill="x", padx=12, pady=(12, 6))

        # Título principal
        title = ctk.CTkLabel(top_outer, text="Gestión de Salidas de Productos",
                             font=("Segoe UI", 16, "bold"), text_color="white")
        title.pack(pady=(8, 6))

        # Frame del formulario (todo en una línea)
        form_frame = create_frame(top_outer)
        form_frame.pack(fill="x", padx=8, pady=(6, 10))
        for i in range(7):
            form_frame.grid_columnconfigure(i, weight=1)

        # Elementos del formulario (una sola fila)
        create_label(form_frame, "Selecciona un elemento").grid(row=0, column=0, sticky="w", padx=5)
        self.nombre_combo = create_combobox(form_frame, values=[], width=180)
        self.nombre_combo.grid(row=1, column=0, padx=5)

        create_label(form_frame, "Fecha").grid(row=0, column=1, sticky="w", padx=5)
        self.fecha_entry = DateEntry(form_frame, date_pattern="yyyy-mm-dd", width=12)
        self.fecha_entry.set_date(datetime.now())
        self.fecha_entry.grid(row=1, column=1, padx=5)

        create_label(form_frame, "Estado").grid(row=0, column=2, sticky="w", padx=5)
        self.estado_combo = create_combobox(form_frame, values=["Operativo", "No operativo"], width=100)
        self.estado_combo.grid(row=1, column=2, padx=5)

        create_label(form_frame, "Destino").grid(row=0, column=3, sticky="w", padx=5)
        self.destino_entry = create_entry(form_frame, placeholder="Destino", width=160)
        self.destino_entry.grid(row=1, column=3, padx=5)

        create_label(form_frame, "Cantidad").grid(row=0, column=4, sticky="w", padx=5)
        self.cantidad_entry = create_entry(form_frame, placeholder="Cantidad", width=50)
        self.cantidad_entry.grid(row=1, column=4, padx=5)

        create_label(form_frame, "Comentario").grid(row=0, column=5, sticky="w", padx=5)
        self.comentario_entry = create_entry(form_frame, placeholder="Comentario (opcional)", width=200)
        self.comentario_entry.grid(row=1, column=5, padx=5)

        # Botones superiores
        btns_frame = create_frame(top_outer)
        btns_frame.pack(pady=(6, 10))
        btns_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.btn_guardar = create_button(btns_frame, "➕ Agregar", command=self.guardar_o_actualizar, style="primary", width=140)
        self.btn_guardar.grid(row=0, column=0, padx=6, pady=4)

        #self.btn_editar = create_button(btns_frame, "✏️ Editar", command=self.guardar_o_actualizar, style="warning", width=120)
        #self.btn_editar.grid(row=0, column=1, padx=6, pady=4)

        self.btn_eliminar = create_button(btns_frame, "🗑️ Eliminar", command=self.eliminar_seleccion, style="danger", width=120)
        self.btn_eliminar.grid(row=0, column=2, padx=6, pady=4)

        self.btn_limpiar = create_button(btns_frame, "🧹 Limpiar", command=self.limpiar_formulario, style="neutral", width=140)
        self.btn_limpiar.grid(row=0, column=3, padx=6, pady=4)

        self.btn_actualizar = create_button(btns_frame, "🔄 Actualizar", command=self.actualizar_tabla, style="primary", width=140)
        self.btn_actualizar.grid(row=0, column=4, padx=6, pady=4)
        
        # Botón Exportar CSV
        self.btn_exportar = create_button(btns_frame, "💾 Exportar CSV", command=self.exportar_csv, style="success", width=160)
        self.btn_exportar.grid(row=0, column=5, padx=6, pady=4)


        

        # ------------------------------
        # Sección inferior (tabla)
        # ------------------------------
        lower_outer = create_frame(self.master)
        lower_outer.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # Frame búsqueda + paginación
        top_table_controls = create_frame(lower_outer)
        top_table_controls.pack(fill="x", padx=10, pady=(4, 6))

        # barra izquierda: búsqueda
        search_frame, self.search_entry = create_search_bar(top_table_controls, self._on_search)
        search_frame.pack(side="left", fill="x", expand=True)

        # derecha: paginación
        pag_frame = create_frame(top_table_controls)
        pag_frame.pack(side="right", fill="x")
        pag_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.btn_prev = create_button(pag_frame, "⬅", command=self.anterior_pagina, style="primary", width=40)
        self.btn_prev.grid(row=0, column=0, sticky="e", padx=5)
        self.lbl_pagina = create_label(pag_frame, "1 / 1")
        self.lbl_pagina.grid(row=0, column=1, sticky="e")
        self.btn_next = create_button(pag_frame, "➡", command=self.siguiente_pagina, style="primary", width=40)
        self.btn_next.grid(row=0, column=2, sticky="e", padx=5)

        # Tabla principal
        self.tree_frame = create_frame(lower_outer)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=(4, 8))
        columns = ("nombre", "fecha", "estado", "destino", "cantidad", "comentario")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=14)
        apply_table_style(self.tree)

        for col, txt in zip(columns, ["Nombre", "Fecha", "Estado", "Destino", "Cantidad", "Comentario"]):
            self.tree.heading(col, text=txt, command=lambda c=col: self.ordenar_col(c))
        self.tree.column("nombre", width=200, anchor="center")
        self.tree.column("fecha", width=100, anchor="center")
        self.tree.column("estado", width=120, anchor="center")
        self.tree.column("destino", width=180, anchor="center")
        self.tree.column("cantidad", width=90, anchor="center")
        self.tree.column("comentario", width=320, anchor="w")

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda e: self.tooltip.hide())

    # ---------------------------------------------------
    # Datos / Productos
    # ---------------------------------------------------
    def _actualizar_productos(self):
        entradas = obtener_entradas()
        nombres = sorted({row[1] for row in entradas if len(row) > 1 and row[1]})
        self.nombre_combo.configure(values=nombres)
        if not self.nombre_combo.get() and nombres:
            self.nombre_combo.set(nombres[0])

    # ---------------------------------------------------
    # Guardar / Actualizar / Eliminar
    # ---------------------------------------------------
    def guardar_o_actualizar(self):
        nombre = self.nombre_combo.get().strip()
        fecha = self.fecha_entry.get_date().strftime("%Y-%m-%d")
        estado = self.estado_combo.get().strip()
        destino = self.destino_entry.get().strip()
        cantidad = self.cantidad_entry.get().strip()
        comentario = self.comentario_entry.get().strip()

        if not all([nombre, fecha, estado, destino, cantidad]):
            messagebox.showwarning("Campos incompletos", "Completa todos los campos.")
            return
        try:
            cantidad_int = int(cantidad)
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Debe ser un número entero.")
            return

        stock_actual = next((it[3] for it in calcular_inventario() if it[0] == nombre), 0)
        if self.selected_id is None and cantidad_int > stock_actual:
            messagebox.showerror("Sin stock", f"Stock insuficiente para {nombre}. Disponible: {stock_actual}")
            return

        if self.selected_id is None:
            agregar_salida(nombre, fecha, estado, destino, cantidad_int, comentario)
            messagebox.showinfo("Salida registrada", "Salida agregada correctamente.")
        else:
            actualizar_salida(int(self.selected_id), nombre, fecha, estado, destino, cantidad_int, comentario)
            messagebox.showinfo("Actualizado", "Salida actualizada correctamente.")

        self._actualizar_productos()
        self.mostrar_salidas()
        self._highlight_recent()
        self.limpiar_formulario()

    def eliminar_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selecciona", "Selecciona una salida.")
            return
        iid = sel[0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar la salida seleccionada?"):
            return
        eliminar_salida(int(iid))
        messagebox.showinfo("Eliminado", "Salida eliminada correctamente.")
        self.mostrar_salidas()

    # ---------------------------------------------------
    # Mostrar / Paginación / Orden
    # ---------------------------------------------------
    def mostrar_salidas(self):
        self.salidas_full = obtener_salidas() or []
        filtro = (self.search_entry.get() or "").lower()
        filtered = [s for s in self.salidas_full if filtro in str(s[1]).lower() or filtro in str(s[4]).lower()] if filtro else self.salidas_full
        if self.sort_by:
            idx_map = {"nombre": 1, "fecha": 2, "estado": 3, "destino": 4, "cantidad": 5}
            idx = idx_map.get(self.sort_by, 1)
            def key(x):
                v = x[idx]
                if self.sort_by == "fecha":
                    try: return datetime.strptime(v, "%Y-%m-%d")
                    except: return datetime.min
                if self.sort_by == "cantidad":
                    try: return int(v)
                    except: return 0
                return str(v).lower()
            filtered.sort(key=key, reverse=self.sort_reverse)
        self._display_page(filtered)

    def _display_page(self, data):
        for i in self.tree.get_children():
            self.tree.delete(i)
        total = len(data)
        start, end = self.page * self.items_per_page, (self.page + 1) * self.items_per_page
        for row in data[start:end]:
            iid = str(row[0])
            vals = (row[1], row[2], row[3], row[4], row[5], row[6])
            self.tree.insert("", "end", iid=iid, values=vals)
        total_pages = max(1, (total + 9)//10)
        #self.lbl_pagina.configure(text=f"{self.page+1} / {total_pages}")
        self.lbl_pagina.configure(text=f"Página {self.page + 1} de {total_pages}")
        self.btn_prev.configure(state="normal" if self.page > 0 else "disabled")
        self.btn_next.configure(state="normal" if end < total else "disabled")

    def siguiente_pagina(self):
        self.page += 1
        self.mostrar_salidas()

    def anterior_pagina(self):
        if self.page > 0:
            self.page -= 1
        self.mostrar_salidas()

    def ordenar_col(self, col):
        if self.sort_by == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by, self.sort_reverse = col, False
        self.page = 0
        self.mostrar_salidas()

    def actualizar_tabla(self):
        self._actualizar_productos()
        self.mostrar_salidas()
        messagebox.showinfo("Actualizado", "Datos actualizados correctamente.")
        
    # ---------------------------------------------------
    # Exportar tabla a CSV con selector de ruta
    # ---------------------------------------------------
    def exportar_csv(self):
        from tkinter import filedialog

        try:
            salidas = obtener_salidas()
            if not salidas:
                messagebox.showinfo("Sin datos", "No hay datos de salidas para exportar.")
                return

            # Selector de archivo para guardar
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Archivo CSV", "*.csv")],
                title="Guardar archivo CSV como",
                initialfile=f"salidas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if not filename:
                return  # Usuario canceló

            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Encabezados
                writer.writerow(["Nombre", "Fecha", "Operativo/No operativo", "Destino", "Cantidad", "Comentario"])

                # Escribir filas
                for s in salidas:
                    # s = (id, nombre, fecha, estado, destino, cantidad, comentario)
                    writer.writerow([s[1], s[2], s[3], s[4], s[5], s[6]])

            messagebox.showinfo("Exportación exitosa", f"Datos exportados correctamente a:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error al exportar", f"Ocurrió un error al exportar:\n{e}")



    # ---------------------------------------------------
    # Edición y resaltado visual
    # ---------------------------------------------------
    def _on_double_click(self, e):
        rowid = self.tree.identify_row(e.y)
        if not rowid: return
        vals = self.tree.item(rowid, "values")
        self.selected_id = rowid
        self.nombre_combo.set(vals[0])
        try:
            self.fecha_entry.set_date(datetime.strptime(vals[1], "%Y-%m-%d"))
        except:
            self.fecha_entry.set_date(datetime.now())
        self.estado_combo.set(vals[2])
        self.destino_entry.delete(0, "end"); self.destino_entry.insert(0, vals[3])
        self.cantidad_entry.delete(0, "end"); self.cantidad_entry.insert(0, vals[4])
        self.comentario_entry.delete(0, "end"); self.comentario_entry.insert(0, vals[5])
        self.btn_guardar.configure(text="✏️ Guardar cambios")

    def _highlight_recent(self):
        try:
            last = self.tree.get_children()[-1]
            self.tree.item(last, tags=("highlight",))
            self.tree.tag_configure("highlight", background="#4a90e2")
            self.tree.after(1000, lambda: self.tree.tag_configure("highlight", background=""))
        except:
            pass

    # ---------------------------------------------------
    # Tooltip
    # ---------------------------------------------------
    def _on_motion(self, e):
        rowid = self.tree.identify_row(e.y)
        col = self.tree.identify_column(e.x)
        if not rowid or not col:
            self.tooltip.hide()
            return
        if col == "#6":
            vals = self.tree.item(rowid, "values")
            text = vals[5] if len(vals) > 5 else ""
            if text:
                x = self.tree.winfo_rootx() + e.x + 20
                y = self.tree.winfo_rooty() + e.y + 10
                self.tooltip.show(text, x, y)
            else:
                self.tooltip.hide()
        else:
            self.tooltip.hide()

    # ---------------------------------------------------
    # Limpieza
    # ---------------------------------------------------
    def limpiar_formulario(self):
        self.selected_id = None
        self.nombre_combo.set("")
        self.fecha_entry.set_date(datetime.now())
        self.estado_combo.set("Operativo")
        for entry in [self.destino_entry, self.cantidad_entry, self.comentario_entry]:
            entry.delete(0, "end")
        self.btn_guardar.configure(text="➕ Agregar")

    # ---------------------------------------------------
    # Búsqueda
    # ---------------------------------------------------
    def _on_search(self, *args):
        self.page = 0
        self.mostrar_salidas()