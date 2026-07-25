import customtkinter as ctk

def show_toast(parent_window, mensaje, color_fondo="#1565C0", duration_ms=2000):
    toast = ctk.CTkToplevel(parent_window)
    toast.overrideredirect(True) 
    toast.attributes("-topmost", True)
    
    # Calculate center top position
    x = parent_window.winfo_rootx() + (parent_window.winfo_width() // 2) - 150
    y = parent_window.winfo_rooty() + 50
    toast.geometry(f"300x45+{x}+{y}")
    
    frame = ctk.CTkFrame(toast, fg_color=color_fondo, corner_radius=8)
    frame.pack(fill="both", expand=True)
    ctk.CTkLabel(frame, text=mensaje, text_color="white", font=("Segoe UI", 13, "bold")).pack(pady=10)
    
    def fade_out(alpha=1.0):
        alpha -= 0.05
        if alpha > 0:
            toast.attributes("-alpha", alpha)
            toast.after(30, lambda: fade_out(alpha))
        else:
            toast.destroy()
            
    toast.after(duration_ms, fade_out)
