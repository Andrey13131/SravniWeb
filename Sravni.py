import tkinter as tk
from tkinter import messagebox

class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, width=30, bg="#F1F3F5", highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        
    def redraw(self):
        self.delete("all")
        last_line = self.text_widget.index("end-1c").split(".")[0]
        new_width = max(30, (len(last_line) * 9) + 10)
        self.config(width=new_width)
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            # Рисуем точно по координате y линии
            self.create_text(new_width - 10, y, anchor="ne", text=linenum, fill="#ADB5BD", font=("Segoe UI", 9))
            i = self.text_widget.index("%s+1line" % i)

def get_clean_lines(text_widget):
    raw_text = text_widget.get("1.0", "end-1c")
    return [item.strip() for item in raw_text.splitlines() if item.strip()]

def update_input_counters(event=None):
    try:
        m_len = len(get_clean_lines(entry_main))
        s_len = len(get_clean_lines(entry_secondary))
        r_len = len(get_clean_lines(result_text))
        label_main.config(text=f"Основная таблица (Окно 1) [{m_len}]:")
        label_secondary.config(text=f"Вторая таблица (Окно 2) [{s_len}]:")
        label_result.config(text=f"Результат (Потери) [{r_len}]:")
        ln1.redraw()
        ln2.redraw()
        ln3.redraw()
    except: pass

def show_context_menu(event):
    w = event.widget
    w.focus_set()
    m = tk.Menu(root, tearoff=0, font=("Segoe UI", 10))
    m.add_command(label="📋 Вставить", command=lambda: (w.tk.call('tk_textPaste', w._w), update_input_counters()))
    m.add_command(label="📄 Копировать", command=lambda: w.tk.call('tk_textCopy', w._w))
    m.add_separator()
    m.add_command(label="🔍 Выделить всё", command=lambda: w.tag_add("sel", "1.0", "end"))
    if "disabled" not in str(w.cget("state")):
        m.add_command(label="🗑️ Очистить", command=lambda: (w.delete("1.0", tk.END), update_input_counters()))
    m.post(event.x_root, event.y_root)

def handle_paste(event):
    event.widget.tk.call('tk_textPaste', event.widget._w)
    root.after(10, update_input_counters)
    return "break"

def handle_copy(event):
    event.widget.tk.call('tk_textCopy', event.widget._w)
    return "break"

def find_losses():
    main_data = get_clean_lines(entry_main)
    secondary_set_lower = set(item.lower() for item in get_clean_lines(entry_secondary))
    losses = [item for item in main_data if item.lower() not in secondary_set_lower]
    
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    if losses:
        result_text.insert(tk.END, "\n".join(losses))
    else:
        result_text.insert(tk.END, "Потерь не найдено.")
    result_text.config(state=tk.DISABLED)
    update_input_counters()

def copy_for_sql():
    data = get_clean_lines(entry_main)
    if not data:
        messagebox.showwarning("Внимание", "Окно 1 пустое!")
        return
    sql_formatted = ",\n".join([f"'{item}'" for item in data])
    root.clipboard_clear()
    root.clipboard_append(sql_formatted)
    messagebox.showinfo("SQL", f"Формат SQL скопирован ({len(data)} строк)")

def clear_all():
    entry_main.delete("1.0", tk.END)
    entry_secondary.delete("1.0", tk.END)
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    result_text.config(state=tk.DISABLED)
    update_input_counters()

def copy_result():
    text = result_text.get("1.0", "end-1c").strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("Успех", "Результаты скопированы!")

def create_text_block(parent, height=10, is_input=True):
    container = tk.Frame(parent, bg="white", highlightbackground="#DEE2E6", highlightthickness=1)
    container.pack(fill="both", expand=True, pady=2)
    
    txt = tk.Text(container, height=height, undo=True, font=("Consolas", 10), 
                 relief="flat", padx=10, pady=5, wrap="none", 
                 insertbackground="#0078D7", selectbackground="#CCE5FF")
    
    ln = LineNumbers(container, txt)
    ln.pack(side="left", fill="y")
    
    scrollbar = tk.Scrollbar(container, orient="vertical", command=lambda *args: (txt.yview(*args), ln.redraw()))
    scrollbar.pack(side="right", fill="y")
    txt.config(yscrollcommand=scrollbar.set)
    txt.pack(side="left", fill="both", expand=True)
    
    # Локальные бинды для надежности
    txt.bind("<Button-3>", show_context_menu)
    txt.bind("<MouseWheel>", lambda e: root.after(1, ln.redraw))
    if is_input:
        txt.bind("<KeyRelease>", update_input_counters)
        
    return txt, ln

# --- НАСТРОЙКА ГЛАВНОГО ОКНА ---
root = tk.Tk()
root.title("Sravni v5.6 Premium | Powered by Spood")
root.geometry("1100x850")
root.configure(bg="#F8F9FA")

# Регистрация горячих клавиш (Универсально)
def apply_hotkeys():
    bindings = [
        (['v', 'V', 'Cyrillic_em', 'Cyrillic_EM'], handle_paste),
        (['c', 'C', 'Cyrillic_es', 'Cyrillic_ES'], handle_copy),
        (['a', 'A', 'Cyrillic_ef', 'Cyrillic_EF'], lambda e: (e.widget.tag_add("sel", "1.0", "end"), "break")[1])
    ]
    for keys, func in bindings:
        for k in keys:
            try: root.bind_class("Text", f"<Control-{k}>", func)
            except: continue

apply_hotkeys()

# Интерфейс
main_frame = tk.Frame(root, bg="#F8F9FA", padx=20, pady=20)
main_frame.pack(fill="both", expand=True)

# Окна ввода
top_frame = tk.Frame(main_frame, bg="#F8F9FA")
top_frame.pack(fill="both", expand=True)

# Окно 1
f1 = tk.Frame(top_frame, bg="#F8F9FA")
f1.pack(side="left", fill="both", expand=True, padx=(0, 10))
label_main = tk.Label(f1, text="Окно 1 [0]:", bg="#F8F9FA", font=("Segoe UI", 10, "bold"))
label_main.pack(anchor="w", pady=(0, 5))
entry_main, ln1 = create_text_block(f1)

# Окно 2
f2 = tk.Frame(top_frame, bg="#F8F9FA")
f2.pack(side="right", fill="both", expand=True, padx=(10, 0))
label_secondary = tk.Label(f2, text="Окно 2 [0]:", bg="#F8F9FA", font=("Segoe UI", 10, "bold"))
label_secondary.pack(anchor="w", pady=(0, 5))
entry_secondary, ln2 = create_text_block(f2)

# Кнопки
btn_frame = tk.Frame(main_frame, bg="#F8F9FA")
btn_frame.pack(pady=20)

def create_btn(text, cmd, bg, fg="white", bold=True):
    f = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
    return tk.Button(btn_frame, text=text, command=cmd, bg=bg, fg=fg, font=f, 
                     padx=20, pady=10, relief="flat", cursor="hand2")

create_btn("🔍 Найти потери", find_losses, "#0078D7").pack(side="left", padx=8)
create_btn("💾 Копировать в SQL", copy_for_sql, "#28A745").pack(side="left", padx=8)
create_btn("📋 Копировать результат", copy_result, "#6C757D").pack(side="left", padx=8)
create_btn("🧹 Очистить всё", clear_all, "#E9ECEF", fg="#495057", bold=False).pack(side="left", padx=8)

# Окно результата
res_frame = tk.Frame(main_frame, bg="#F8F9FA")
res_frame.pack(fill="both", expand=True)
label_result = tk.Label(res_frame, text="Результат (Потери) [0]:", bg="#F8F9FA", font=("Segoe UI", 10, "bold"))
label_result.pack(anchor="w", pady=(0, 5))
result_text, ln3 = create_text_block(res_frame, height=8, is_input=False)
result_text.config(state=tk.DISABLED, bg="#F1F3F5")

root.mainloop()
