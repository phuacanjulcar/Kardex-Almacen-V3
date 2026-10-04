import customtkinter as ctk

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(300, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert") or (0,0,0,0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        
        self.tw = ctk.CTkToplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.attributes("-topmost", True)
        
        # Fondo oscuro y texto blanco para alto contraste, independiente del modo
        bg_color = "#1E293B" 
        text_color = "#FFFFFF"
        border_color = "#334155"
        
        self.tw.wm_geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self.tw, fg_color=bg_color, corner_radius=6, border_width=1, border_color=border_color)
        frame.pack(fill="both", expand=True)
        
        label = ctk.CTkLabel(frame, text=self.text, justify='left',
                             font=("Segoe UI", 11), text_color=text_color, wraplength=250)
        label.pack(padx=10, pady=6)
        
    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

def crear_label_con_ayuda(parent, texto_label, texto_ayuda, font=("Segoe UI", 12), text_color=None, **kwargs):
    """
    Crea un frame transparente que contiene un Label normal y un ícono [i] con Tooltip a su derecha.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    
    lbl = ctk.CTkLabel(frame, text=texto_label, font=font, text_color=text_color)
    lbl.pack(side="left")
    
    modo = ctk.get_appearance_mode()
    icon_color = "#64748B" if modo == "Light" else "#94A3B8"
    icon = ctk.CTkLabel(frame, text=" ⓘ", font=("Segoe UI", 12, "bold"), text_color=icon_color, cursor="hand2")
    icon.pack(side="left", padx=(2, 0))
    
    ToolTip(icon, texto_ayuda)
    
    return frame
