# tabs/tab_inventario.py
# ----------------------------------------------------
# Módulo de pestaña INVENTARIO con estilo unificado, exportación CSV/PDF
# y resaltado de stock bajo o agotado
# ----------------------------------------------------

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except ImportError:
    messagebox.showerror(
        "Falta dependencia",
        "El módulo 'reportlab' no está instalado.\n\nEjecuta en la terminal:\n\npip install reportlab"
    )

from database import calcular_inventario
from ui_utils import (
    create_frame,
    create_label,
    create_button,
    create_search_bar,
    apply_table_style
)


class TabInventario:
    def __init__(self, master):
        self.master = master
        try:
            self.master.configure(fg_color="#2f2f2f")
        except Exception:
            pass

        # Control de páginas
        self.page = 0
        self.items_per_page = 10
        self.inventario_full = []
        self.sort_by = None
        self.sort_reverse = False

        self._crear_interfaz()
        self.mostrar_inventario()

    # ---------------------------------------------------
    # Interfaz
    # ---------------------------------------------------
    def _crear_interfaz(self):
        top_outer = create_frame(self.master)
        top_outer.pack(fill="x", padx=12, pady=(12, 6))

        # Título
        title = ctk.CTkLabel(
            top_outer, text="Gestión de Inventario",
            font=("Segoe UI", 16, "bold"), text_color="white"
        )
        title.pack(pady=(8, 6))

        # Botones superiores
        btns_frame = create_frame(top_outer)
        btns_frame.pack(pady=(6, 10))
        btns_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_actualizar = create_button(
            btns_frame, "🔄 Actualizar", command=self.actualizar_tabla, style="primary", width=160
        )
        self.btn_actualizar.grid(row=0, column=0, padx=6, pady=4)

        self.btn_exportar_csv = create_button(
            btns_frame, "💾 Exportar CSV", command=self.exportar_csv, style="success", width=160
        )
        self.btn_exportar_csv.grid(row=0, column=1, padx=6, pady=4)

        self.btn_exportar_pdf = create_button(
            btns_frame, "📄 Exportar PDF", command=self.exportar_pdf, style="warning", width=160
        )
        self.btn_exportar_pdf.grid(row=0, column=2, padx=6, pady=4)

        # ---------------------------------------------------
        # Sección inferior con búsqueda y tabla
        # ---------------------------------------------------
        lower_outer = create_frame(self.master)
        lower_outer.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # Búsqueda + paginación
        top_table_controls = create_frame(lower_outer)
        top_table_controls.pack(fill="x", padx=10, pady=(4, 6))

        # Búsqueda (izquierda)
        search_frame, self.search_entry = create_search_bar(top_table_controls, self._on_search)
        search_frame.pack(side="left", fill="x", expand=True)

        # Paginación (derecha)
        pag_frame = create_frame(top_table_controls)
        pag_frame.pack(side="right")
        pag_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.btn_prev = create_button(pag_frame, "⬅", command=self.anterior_pagina, style="primary", width=40)
        self.btn_prev.grid(row=0, column=0, sticky="e", padx=5)
        self.lbl_pagina = create_label(pag_frame, "Página 1 de 1")
        self.lbl_pagina.grid(row=0, column=1, sticky="e")
        self.btn_next = create_button(pag_frame, "➡", command=self.siguiente_pagina, style="primary", width=40)
        self.btn_next.grid(row=0, column=2, sticky="e", padx=5)

        # ---------------------------------------------------
        # Tabla principal
        # ---------------------------------------------------
        self.tree_frame = create_frame(lower_outer)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=(4, 8))

        columns = ("nombre", "entradas", "salidas", "stock")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=14)
        apply_table_style(self.tree)

        for col, txt in zip(columns, ["Producto", "Entradas", "Salidas", "Stock disponible"]):
            self.tree.heading(col, text=txt, command=lambda c=col: self.ordenar_col(c))

        self.tree.column("nombre", width=260, anchor="center")
        self.tree.column("entradas", width=120, anchor="center")
        self.tree.column("salidas", width=120, anchor="center")
        self.tree.column("stock", width=140, anchor="center")

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, side="left")

    # ---------------------------------------------------
    # Lógica de datos
    # ---------------------------------------------------
    def mostrar_inventario(self):
        self.inventario_full = calcular_inventario() or []
        filtro = (self.search_entry.get() or "").lower()
        filtered = [i for i in self.inventario_full if filtro in str(i[0]).lower()] if filtro else self.inventario_full
        if self.sort_by:
            idx_map = {"nombre": 0, "entradas": 1, "salidas": 2, "stock": 3}
            idx = idx_map.get(self.sort_by, 0)
            def key(x):
                try:
                    return int(x[idx]) if idx > 0 else str(x[idx]).lower()
                except:
                    return 0
            filtered.sort(key=key, reverse=self.sort_reverse)
        self._display_page(filtered)

    def _display_page(self, data):
        for i in self.tree.get_children():
            self.tree.delete(i)

        total = len(data)
        start, end = self.page * self.items_per_page, (self.page + 1) * self.items_per_page
        for row in data[start:end]:
            iid = str(row[0])
            stock = int(row[3])
            self.tree.insert("", "end", values=row)

            # Colorear según stock
            if stock == 0:
                self.tree.item(self.tree.get_children()[-1], tags=("agotado",))
            elif stock <= 3:
                self.tree.item(self.tree.get_children()[-1], tags=("bajo",))

        # Configurar colores
        self.tree.tag_configure("agotado", background="#e05a5a")   # rojo
        self.tree.tag_configure("bajo", background="#e6b85c")      # ámbar

        total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        self.lbl_pagina.configure(text=f"Página {self.page + 1} de {total_pages}")
        self.btn_prev.configure(state="normal" if self.page > 0 else "disabled")
        self.btn_next.configure(state="normal" if end < total else "disabled")

    def siguiente_pagina(self):
        self.page += 1
        self.mostrar_inventario()

    def anterior_pagina(self):
        if self.page > 0:
            self.page -= 1
        self.mostrar_inventario()

    def ordenar_col(self, col):
        if self.sort_by == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by, self.sort_reverse = col, False
        self.page = 0
        self.mostrar_inventario()

    def actualizar_tabla(self):
        self.mostrar_inventario()
        messagebox.showinfo("Actualizado", "Inventario actualizado correctamente.")

    # ---------------------------------------------------
    # Exportar CSV
    # ---------------------------------------------------
    def exportar_csv(self):
        try:
            inventario = calcular_inventario()
            if not inventario:
                messagebox.showinfo("Sin datos", "No hay datos para exportar.")
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Archivo CSV", "*.csv")],
                title="Guardar archivo CSV como",
                initialfile=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if not filename:
                return

            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Producto", "Entradas", "Salidas", "Stock disponible"])
                for row in inventario:
                    writer.writerow(row)

            messagebox.showinfo("Exportación exitosa", f"Datos exportados a:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al exportar:\n{e}")

    # ---------------------------------------------------
    # Exportar PDF
    # ---------------------------------------------------
    def exportar_pdf(self):
        try:
            inventario = calcular_inventario()
            if not inventario:
                messagebox.showinfo("Sin datos", "No hay datos para exportar.")
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivo PDF", "*.pdf")],
                title="Guardar archivo PDF como",
                initialfile=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            if not filename:
                return

            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            pdf = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Título
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(180, height - 60, "📦 Reporte de Inventario")
            pdf.setFont("Helvetica", 10)

            # Encabezados
            headers = ["Producto", "Entradas", "Salidas", "Stock disponible"]
            x_positions = [50, 250, 350, 460]
            y = height - 100

            pdf.setFont("Helvetica-Bold", 11)
            for i, h in enumerate(headers):
                pdf.drawString(x_positions[i], y, h)
            pdf.setFont("Helvetica", 10)
            y -= 18

            # Filas de datos
            for row in inventario:
                nombre, entradas, salidas, stock = row
                stock_int = int(stock)

                # Color según nivel de stock
                if stock_int == 0:
                    pdf.setFillColor(colors.red)
                elif stock_int <= 3:
                    pdf.setFillColor(colors.darkorange)
                else:
                    pdf.setFillColor(colors.black)

                # Escribir fila
                pdf.drawString(x_positions[0], y, str(nombre))
                pdf.drawString(x_positions[1], y, str(entradas))
                pdf.drawString(x_positions[2], y, str(salidas))
                pdf.drawString(x_positions[3], y, str(stock))

                # Restaurar color y bajar línea
                pdf.setFillColor(colors.black)
                y -= 18

                # Salto de página
                if y < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 10)
                    y = height - 50

            pdf.save()
            messagebox.showinfo("PDF generado", f"Archivo guardado en:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al exportar PDF:\n{e}")


    # ---------------------------------------------------
    # Búsqueda
    # ---------------------------------------------------
    def _on_search(self, *args):
        self.page = 0
        self.mostrar_inventario()
