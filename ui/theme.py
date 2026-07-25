import customtkinter as ctk

class Theme:
    # --- PALETA BASE ---
    # Tuplas: (Modo Claro, Modo Oscuro)
    
    # Fondos (Azul Pizarra para Modo Oscuro en todas las vistas)
    BG_GENERAL = ("#F8FAFC", "#0F172A")
    BG_CARD    = ("#FFFFFF", "#1E293B")
    
    # Textos
    TEXT_MAIN  = ("#0F172A", "#F8FAFC")
    TEXT_MUTED = ("#64748B", "#94A3B8")
    
    # Bordes y Divisores
    BORDER     = ("#E2E8F0", "#334155")
    
    # --- COLORES SEMÁNTICOS (Para Botones e Indicadores) ---
    # Se busca que el contraste sea apto en ambos modos.
    PRIMARY         = ("#2563EB", "#3B82F6") # Azul principal
    PRIMARY_HOVER   = ("#1D4ED8", "#2563EB")
    
    SUCCESS         = ("#10B981", "#059669") # Verde éxito/entradas
    SUCCESS_HOVER   = ("#059669", "#047857")
    
    WARNING         = ("#F59E0B", "#D97706") # Naranja salidas/poco stock
    WARNING_HOVER   = ("#D97706", "#B45309")
    
    DANGER          = ("#EF4444", "#DC2626") # Rojo alertas/agotado
    DANGER_HOVER    = ("#DC2626", "#B91C1C")
    
    # Colores Especiales
    PURPLE          = ("#8B5CF6", "#7C3AED") # Para Mensajería
    PURPLE_HOVER    = ("#7C3AED", "#6D28D9")
    
    # Elementos Transparentes o Especiales
    TRANSPARENT_HOVER = ("#F1F5F9", "#334155")

    @classmethod
    def apply_tabview_style(cls, tabview):
        modo_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        tabview.configure(
            fg_color="transparent",
            segmented_button_fg_color=cls.BG_CARD[modo_idx],
            segmented_button_selected_color=cls.PRIMARY[modo_idx],
            segmented_button_selected_hover_color=cls.PRIMARY_HOVER[modo_idx],
            segmented_button_unselected_color=cls.BORDER[modo_idx],
            segmented_button_unselected_hover_color=cls.TRANSPARENT_HOVER[modo_idx],
            text_color=cls.TEXT_MAIN[modo_idx]
        )
        try:
            tabview._segmented_button.configure(font=("Segoe UI", 15, "bold"))
        except: pass

    @classmethod
    def apply_segmented_button_style(cls, seg_btn):
        modo_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        seg_btn.configure(
            fg_color=cls.BG_CARD[modo_idx],
            selected_color=cls.PRIMARY[modo_idx],
            selected_hover_color=cls.PRIMARY_HOVER[modo_idx],
            unselected_color=cls.BORDER[modo_idx],
            unselected_hover_color=cls.TRANSPARENT_HOVER[modo_idx],
            text_color=cls.TEXT_MAIN[modo_idx],
            corner_radius=8,
            font=("Segoe UI", 14, "bold")
        )

    @staticmethod
    def apply_fade_in(window, start_alpha=0.0):
        window.attributes("-alpha", start_alpha)
        
        def _fade(current_alpha):
            try:
                current_alpha += 0.1
                if current_alpha <= 1.0:
                    window.attributes("-alpha", current_alpha)
                    window.after(15, lambda: _fade(current_alpha))
                else:
                    window.attributes("-alpha", 1.0)
            except Exception:
                pass
                
        window.after(10, lambda: _fade(start_alpha))

# --- MONKEY PATCH PARA FADE-IN GLOBAL ---
original_toplevel_init = ctk.CTkToplevel.__init__

def toplevel_init_with_fade_in(self, *args, **kwargs):
    original_toplevel_init(self, *args, **kwargs)
    
    # Hacerlo invisible inmediatamente para evitar el parpadeo inicial
    self.attributes("-alpha", 0.0)
    
    # Evitar aplicar a tooltips o ventanas sin bordes
    def _check_and_fade():
        if not self.winfo_exists(): return
        # overriedredirect returns True/False or string "1"/"0"
        if str(self.overrideredirect()) not in ["1", "True", True]:
            Theme.apply_fade_in(self, start_alpha=0.0)
        else:
            self.attributes("-alpha", 1.0)
            
    self.after(10, _check_and_fade)

ctk.CTkToplevel.__init__ = toplevel_init_with_fade_in
