import customtkinter as ctk
from tabs.tab_entradas import TabEntradas
from tabs.tab_salidas import TabSalidas
from tabs.tab_inventario import TabInventario
from database import crear_tablas

if __name__ == "__main__":
    crear_tablas()
    
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Sistema de Inventario")
app.geometry("1000x700")

# Crear pestañas
tabview = ctk.CTkTabview(app, width=980, height=680)
tabview.pack(padx=10, pady=10)

tab_entradas = tabview.add("Entradas")
tab_salidas = tabview.add("Salidas")
tab_inventario = tabview.add("Inventario")

# Iniciar pestañas
TabEntradas(tab_entradas)
TabSalidas(tab_salidas)
TabInventario(tab_inventario)

app.mainloop()
