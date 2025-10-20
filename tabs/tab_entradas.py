# tabs/tab_entradas.py
# ----------------------------------------------------
# Pestaña Entradas - estilo unificado con ui_utils.py
# ----------------------------------------------------

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import csv

from database import (
    obtener_entradas,
    agregar_entrada,
    eliminar_entrada,
    actualizar_entrada,
    factura_existe
)

from ui_utils import (
    aplicar_estilo_general,
    create_frame,
    create_label,
    create_entry,
    create_combobox,
    create_button,
    create_search_bar,
    apply_table_style,
    COLORES,
)

# Simple tooltip class (Toplevel) to show long comments
class Tooltip:
    def __init__(self, parent):
        self.parent = parent
        self.tw = None

    def show(self, text, x, y):
        self.hide()
        if not text:
            return
        self.tw = tw = tk.Toplevel(self.parent)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        lbl = tk.Label(tw, text=text, justify="left", background="#ffffe0",
                       relief="solid", borderwidth=1, font=("Segoe UI", 9), wraplength=500)
        lbl.pack(ipadx=4, ipady=3)
        tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        if self.tw:
            try:
                self.tw.destroy()
            finally:
                self.tw = None


class TabEntradas:
    def __init__(self, master):
        self.master = master
        aplicar_estilo_general(self.master)

        # state
        self.page = 0
        self.items_per_page = 10
        self.sort_by = None
        self.sort_reverse = False
        self.selected_id = None  # id from DB of selected row
        self.entradas_full = []

        # tooltip helper
        self.tooltip = Tooltip(self.master)

        # build UI
        self._crear_interfaz()
        # load data
        self.actualizar_tabla()

    # ---------- date helpers ----------
    def _to_db_date(self, display_date_str):
        """Converts 'dd-mm-YYYY' or 'YYYY-mm-dd' to 'YYYY-mm-dd' for DB"""
        for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                d = datetime.strptime(display_date_str, fmt)
                return d.strftime("%Y-%m-%d")
            except Exception:
                continue
        return display_date_str

    def _to_display_date(self, db_date_str):
        """Converts 'YYYY-mm-dd' to 'dd-mm-YYYY' for display"""
        try:
            d = datetime.strptime(db_date_str, "%Y-%m-%d")
            return d.strftime("%d-%m-%Y")
        except Exception:
            return db_date_str

    # ---------- UI ----------
    def _crear_interfaz(self):
        # Top outer frame
        top_outer = create_frame(self.master, fg_color=COLORES["recuadro"])
        top_outer.pack(fill="x", padx=12, pady=(12, 6))

        # Title
        title = create_label(top_outer, "Gestión de Entradas de Productos", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(8, 6))

        # Form frame (one-line layout)
        form_frame = create_frame(top_outer, fg_color="transparent")
        form_frame.pack(fill="x", padx=8, pady=(6, 8))

        # grid columns
        for i in range(10):
            form_frame.grid_columnconfigure(i, weight=1)

        # Labels on top row
        lbl_nombre = create_label(form_frame, "Nombre del producto", font=("Segoe UI", 11, "bold"))
        lbl_nombre.grid(row=0, column=0, columnspan=2, sticky="s", pady=(0, 4))
        lbl_fecha = create_label(form_frame, "Fecha", font=("Segoe UI", 11, "bold"))
        lbl_fecha.grid(row=0, column=2, sticky="s", pady=(0, 4))
        lbl_factura = create_label(form_frame, "Factura/Guía", font=("Segoe UI", 11, "bold"))
        lbl_factura.grid(row=0, column=3, sticky="s", pady=(0, 4))
        lbl_cantidad = create_label(form_frame, "Cantidad", font=("Segoe UI", 11, "bold"))
        lbl_cantidad.grid(row=0, column=4, sticky="s", pady=(0, 4))
        lbl_comentario = create_label(form_frame, "Comentario", font=("Segoe UI", 11, "bold"))
        lbl_comentario.grid(row=0, column=5, columnspan=2, sticky="s", pady=(0, 4))

        # Inputs (second row) - widths tuned, date selector for fecha
        self.nombre_entry = create_entry(form_frame, placeholder="Ingresa Nombre", width=320)
        self.nombre_entry.grid(row=1, column=0, columnspan=2, padx=6, sticky="we")

        self.fecha_entry = DateEntry(form_frame, date_pattern="dd-mm-yyyy", width=12)
        self.fecha_entry.set_date(datetime.now())
        self.fecha_entry.grid(row=1, column=2, padx=6)

        self.factura_entry = create_entry(form_frame, placeholder="Numero Factura", width=140)
        self.factura_entry.grid(row=1, column=3, padx=6)

        self.cantidad_entry = create_entry(form_frame, placeholder="0", width=100)
        self.cantidad_entry.grid(row=1, column=4, padx=6)

        self.comentario_entry = create_entry(form_frame, placeholder="Ingresa Comentario", width=300)
        self.comentario_entry.grid(row=1, column=5, columnspan=2, padx=6, sticky="we")

        # Buttons centered below form
        btns_frame = create_frame(top_outer, fg_color="transparent")
        btns_frame.pack(pady=(6, 10))
        for i in range(6):
            btns_frame.grid_columnconfigure(i, weight=1)

        self.btn_agregar = create_button(btns_frame, "➕ Agregar", command=self._guardar_entrada, style="primary", width=160)
        self.btn_agregar.grid(row=0, column=0, padx=8, pady=6)

       # self.btn_guardar_cambios = create_button(btns_frame, "✏️ Guardar cambios", command=self._guardar_entrada, style="warning", width=180)
       # self.btn_guardar_cambios.grid(row=0, column=1, padx=8, pady=6)

        self.btn_eliminar = create_button(btns_frame, "🗑️ Eliminar", command=self._eliminar_entrada, style="danger", width=140)
        self.btn_eliminar.grid(row=0, column=2, padx=8, pady=6)

        self.btn_limpiar = create_button(btns_frame, "🧹 Limpiar", command=self._limpiar_formulario, style="neutral", width=160)
        self.btn_limpiar.grid(row=0, column=3, padx=8, pady=6)

        #self.btn_actualizar = create_button(btns_frame, "🔄 Actualizar", command=self.actualizar_tabla, style="primary", width=160)
        #self.btn_actualizar.grid(row=0, column=4, padx=8, pady=6)

        self.btn_exportar = create_button(btns_frame, "💾 Exportar CSV", command=self._exportar_csv, style="success", width=160)
        self.btn_exportar.grid(row=0, column=5, padx=8, pady=6)

        # ----- Lower section (search + table + pagination) -----
        lower_outer = create_frame(self.master, fg_color=COLORES["recuadro"])
        lower_outer.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # top bar: search (left) and pagination (right)
        top_bar = create_frame(lower_outer, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(8, 4))

        # search
        search_frame, self.search_entry = create_search_bar(top_bar, self._on_search)
        search_frame.pack(side="left", fill="x", expand=True)

        # pagination controls on the right
        pag_frame = create_frame(top_bar, fg_color="transparent")
        pag_frame.pack(side="right")
        pag_frame.grid_columnconfigure((0,1,2), weight=1)

        self.btn_prev = create_button(pag_frame, "⬅", command=self._pagina_anterior, style="primary", width=40)
        self.btn_prev.grid(row=0, column=0, padx=6)
        self.lbl_pagina = create_label(pag_frame, "Página 1", font=("Segoe UI", 12, "bold"))
        self.lbl_pagina.grid(row=0, column=1)
        self.btn_next = create_button(pag_frame, "➡", command=self._pagina_siguiente, style="primary", width=40)
        self.btn_next.grid(row=0, column=2, padx=6)

        # Treeview area
        tree_frame = create_frame(lower_outer, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(6,8))

        cols = ("nombre", "fecha", "factura", "cantidad", "comentario")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=14)
        apply_table_style(self.tree)

        # headings with sorting commands
        self.tree.heading("nombre", text="Nombre", command=lambda: self._ordenar("nombre"))
        self.tree.heading("fecha", text="Fecha", command=lambda: self._ordenar("fecha"))
        self.tree.heading("factura", text="Factura/Guía", command=lambda: self._ordenar("factura"))
        self.tree.heading("cantidad", text="Cantidad", command=lambda: self._ordenar("cantidad"))
        self.tree.heading("comentario", text="Comentario")

        # column widths
        self.tree.column("nombre", width=260, anchor="center", stretch=True)
        self.tree.column("fecha", width=110, anchor="center", stretch=False)
        self.tree.column("factura", width=160, anchor="center", stretch=False)
        self.tree.column("cantidad", width=100, anchor="center", stretch=False)
        self.tree.column("comentario", width=360, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, side="left")

        # bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda e: self.tooltip.hide())

    # ---------- Data load / display ----------
    def actualizar_tabla(self):
        """Fetch all entries from DB and display first page"""
        try:
            self.entradas_full = obtener_entradas()
        except Exception:
            self.entradas_full = []
        self.page = 0
        self._mostrar_pagina()

    def _apply_search_and_sort(self):
        filtro = (self.search_entry.get() or "").strip().lower()
        lista = list(self.entradas_full)
        if filtro:
            lista = [r for r in lista if filtro in str(r[1]).lower() or filtro in str(r[3]).lower() or filtro in str(r[5]).lower()]
        if self.sort_by:
            idx_map = {"nombre": 1, "fecha": 2, "factura": 3, "cantidad": 4}
            idx = idx_map.get(self.sort_by, 1)
            def keyfn(x):
                v = x[idx]
                if self.sort_by == "fecha":
                    try:
                        return datetime.strptime(v, "%Y-%m-%d")
                    except:
                        return datetime.min
                if self.sort_by == "cantidad":
                    try:
                        return int(v)
                    except:
                        return 0
                return str(v).lower() if v is not None else ""
            lista.sort(key=keyfn, reverse=self.sort_reverse)
        return lista

    def _mostrar_pagina(self):
        data = self._apply_search_and_sort()
        total = len(data)
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_items = data[start:end]

        # clear
        for r in self.tree.get_children():
            self.tree.delete(r)

        # insert with iid as DB id
        for row in page_items:
            # row is (id, nombre, fecha, factura, cantidad, comentario) per DB
            iid = str(row[0])
            values = (row[1], self._to_display_date(row[2]), row[3], row[4], row[5])
            self.tree.insert("", "end", iid=iid, values=values)

        total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        self.lbl_pagina.configure(text=f"Página {self.page + 1} de {total_pages}")

        # enable/disable buttons
        self.btn_prev.configure(state="normal" if self.page > 0 else "disabled")
        self.btn_next.configure(state="normal" if end < total else "disabled")

    # ---------- Pagination ----------
    def _pagina_anterior(self):
        if self.page > 0:
            self.page -= 1
            self._mostrar_pagina()

    def _pagina_siguiente(self):
        # calculate total pages to prevent overflow
        total = len(self._apply_search_and_sort())
        max_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        if self.page < max_pages - 1:
            self.page += 1
            self._mostrar_pagina()

    # ---------- Sorting ----------
    def _ordenar(self, columna):
        if self.sort_by == columna:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = columna
            self.sort_reverse = False
        self.page = 0
        self._mostrar_pagina()

    # ---------- Add / Update / Delete ----------
    def _guardar_entrada(self):
        nombre = self.nombre_entry.get().strip()
        fecha_display = self.fecha_entry.get_date().strftime("%d-%m-%Y")
        fecha_db = self._to_db_date(fecha_display)
        factura = self.factura_entry.get().strip()
        cantidad_str = self.cantidad_entry.get().strip()
        comentario = self.comentario_entry.get().strip()

        if not all([nombre, fecha_db, factura, cantidad_str]):
            messagebox.showwarning("Campos incompletos", "Completa todos los campos obligatorios.")
            return

        try:
            cantidad = int(cantidad_str)
        except ValueError:
            messagebox.showerror("Cantidad inválida", "La cantidad debe ser un número entero.")
            return

        # If editing (selected_id set), then update; otherwise add.
        if self.selected_id:
            # When editing, allow same factura as existing; but if user changed factura to one that exists on another id, block.
            if factura_existe(factura):
                # need to ensure it belongs to same record or is unique
                # find entry with same factura
                same = [r for r in self.entradas_full if r[3] == factura]
                if same and str(same[0][0]) != str(self.selected_id):
                    messagebox.showerror("Factura existente", "Otra entrada usa esa factura. Usa otra o elimina la otra entrada.")
                    return
            try:
                actualizar_entrada(int(self.selected_id), nombre, fecha_db, factura, cantidad, comentario)
                messagebox.showinfo("Actualizado", "Entrada actualizada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar: {e}")
        else:
            # adding new -> enforce factura unique
            if factura_existe(factura):
                messagebox.showerror("Factura existente", "Ya existe una entrada con ese número de factura.")
                return
            try:
                agregar_entrada(nombre, fecha_db, factura, cantidad, comentario)
                messagebox.showinfo("Agregado", "Entrada agregada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar: {e}")

        # reload and highlight recently added/edited
        self.actualizar_tabla()
        self._highlight_recent()
        self._limpiar_formulario()

    def _eliminar_entrada(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selecciona", "Selecciona una entrada para eliminar.")
            return
        iid = sel[0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar la entrada seleccionada?"):
            return
        try:
            eliminar_entrada(int(iid))
            messagebox.showinfo("Eliminado", "Entrada eliminada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
        self.actualizar_tabla()

    # ---------- Double click loads into form ----------
    def _on_double_click(self, event):
        rowid = self.tree.identify_row(event.y)
        if not rowid:
            return
        vals = self.tree.item(rowid, "values")
        # row values = (nombre, fecha_display, factura, cantidad, comentario)
        self.selected_id = rowid
        try:
            self.nombre_entry.delete(0, "end"); self.nombre_entry.insert(0, vals[0])
        except: pass
        try:
            # fecha display -> dd-mm-YYYY
            self.fecha_entry.set_date(datetime.strptime(vals[1], "%d-%m-%Y"))
        except:
            self.fecha_entry.set_date(datetime.now())
        try:
            self.factura_entry.delete(0, "end"); self.factura_entry.insert(0, vals[2])
        except: pass
        try:
            self.cantidad_entry.delete(0, "end"); self.cantidad_entry.insert(0, vals[3])
        except: pass
        try:
            self.comentario_entry.delete(0, "end"); self.comentario_entry.insert(0, vals[4])
        except: pass
        # change add button label to indicate update mode
        try:
            self.btn_agregar.configure(text="✏️ Guardar cambios")
        except:
            pass

    # ---------- Highlight recent (last row) ----------
    def _highlight_recent(self):
        try:
            children = self.tree.get_children()
            if not children:
                return
            last = children[-1]
            self.tree.selection_set(last)
            self.tree.see(last)
            self.tree.item(last, tags=("recent",))
            self.tree.tag_configure("recent", background=COLORES["primary"])
            # clear after 1s
            self.tree.after(1000, lambda: self.tree.tag_configure("recent", background=""))
        except Exception:
            pass

    # ---------- Tooltip for comment column ----------
    def _on_motion(self, event):
        rowid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not rowid or not col:
            self.tooltip.hide()
            return
        # comment column is "#5"
        if col == "#5":
            vals = self.tree.item(rowid, "values")
            comment = vals[4] if len(vals) > 4 else ""
            if comment:
                x_root = self.tree.winfo_rootx() + event.x + 20
                y_root = self.tree.winfo_rooty() + event.y + 10
                self.tooltip.show(comment, x_root, y_root)
            else:
                self.tooltip.hide()
        else:
            self.tooltip.hide()

    # ---------- Search wrapper ----------
    def _on_search(self, *args):
        self.page = 0
        self._mostrar_pagina()

    def _limpiar_formulario(self):
        self.selected_id = None
        self.nombre_entry.delete(0, "end")
        self.fecha_entry.set_date(datetime.now())
        self.factura_entry.delete(0, "end")
        self.cantidad_entry.delete(0, "end")
        self.comentario_entry.delete(0, "end")
        try:
            self.btn_agregar.configure(text="➕ Agregar")
        except:
            pass

    # ---------- Export CSV ----------
    def _exportar_csv(self):
        salidas = self._apply_search_and_sort()
        archivo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not archivo:
            return
        try:
            with open(archivo, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Nombre", "Fecha", "Factura", "Cantidad", "Comentario"])
                for row in salidas:
                    # row: (id, nombre, fecha, factura, cantidad, comentario)
                    writer.writerow([row[1], row[2], row[3], row[4], row[5]])
            messagebox.showinfo("Exportado", f"Datos exportados correctamente a:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

# -------------------------------
# FIN TAB ENTRADAS