# ui_utils.py
# ----------------------------------------------------
# Funciones de utilidad para UI unificada
# Entradas, Salidas e Inventario
# ----------------------------------------------------

import customtkinter as ctk
from tkinter import ttk, StringVar, Entry, Frame, Label, Button

# -------------------------------
# COLORES UNIFICADOS
# -------------------------------
COLORES = {
    "fondo_principal": "#2f2f2f",
    "recuadro": "#3a3a3a",
    "input_bg": "#ffffff",
    "input_border": "#222222",
    "texto": "#ffffff",
    "primary": "#3a7ff6",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "neutral": "#888888",
}

# -------------------------------
# FUNCIÓN GLOBAL DE ESTILO
# -------------------------------
def aplicar_estilo_general(ventana):
    """Aplica los colores y configuración general a una ventana o frame principal."""
    ventana.configure(fg_color=COLORES["fondo_principal"])
    ctk.set_default_color_theme("dark-blue")
    ctk.set_appearance_mode("dark")

# -------------------------------
# FRAMES
# -------------------------------
def create_frame(parent, fg_color=None):
    color = fg_color if fg_color else COLORES["recuadro"]
    return ctk.CTkFrame(parent, fg_color=color, corner_radius=8)

# -------------------------------
# LABELS
# -------------------------------
def create_label(parent, text, font=("Arial", 12), text_color=None):
    color = text_color if text_color else COLORES["texto"]
    return ctk.CTkLabel(parent, text=text, font=font, text_color=color)

# -------------------------------
# ENTRIES
# -------------------------------
def create_entry(parent, placeholder="", width=150):
    return ctk.CTkEntry(
        parent,
        width=width,
        placeholder_text=placeholder,
        fg_color=COLORES["input_bg"],
        border_width=2,
        border_color=COLORES["input_border"],
        text_color="#000000",
    )

# -------------------------------
# COMBOBOX
# -------------------------------
def create_combobox(parent, values=[], width=150):
    combo = ctk.CTkComboBox(parent, values=values, width=width)
    combo.set("")  # Inicial vacío
    return combo

# -------------------------------
# BOTONES
# -------------------------------
def create_button(parent, text, command=None, style="primary", width=120):
    fg_color = COLORES.get(style, COLORES["primary"])
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        fg_color=fg_color,
        hover_color=_ajustar_color_hover(fg_color),
        text_color="#ffffff",
        corner_radius=6
    )

def _ajustar_color_hover(hex_color):
    """Oscurece un color hex para el efecto hover"""
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "#000000"
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        factor = 0.85
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return "#000000"

# -------------------------------
# BARRA DE BUSQUEDA
# -------------------------------
def create_search_bar(parent, callback):
    frame = create_frame(parent, fg_color="transparent")
    entry = ctk.CTkEntry(frame, placeholder_text="Buscar...", width=250)
    entry.pack(side="left", padx=5)
    btn = create_button(frame, "Buscar", command=lambda: callback(), style="primary", width=80)
    btn.pack(side="left", padx=5)
    return frame, entry

# -------------------------------
# ESTILO DE TABLA
# -------------------------------
def apply_table_style(tabla):
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview",
        background=COLORES["recuadro"],
        foreground=COLORES["texto"],
        rowheight=25,
        fieldbackground=COLORES["recuadro"],
        font=("Segoe UI", 11),
        bordercolor=COLORES["recuadro"],
        borderwidth=0
    )
    style.map("Treeview", background=[("selected", COLORES["primary"])], foreground=[("selected", "#ffffff")])
    style.configure(
        "Treeview.Heading",
        background=COLORES["recuadro"],
        foreground=COLORES["texto"],
        font=("Segoe UI", 11, "bold"),
        relief="flat"
    )
    style.map("Treeview.Heading", background=[("active", COLORES["primary"])])