import os
import re
import json
import threading
import time
from queue import Queue
from tkinter import Tk, filedialog, Text, Button, Label, END, Scrollbar, RIGHT, Y, LEFT, BOTH, Frame, messagebox, StringVar, OptionMenu
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import simpledialog
from tqdm import tqdm

# --- Sequence detection regex ---
SEQUENCE_REGEX = re.compile(r'^(.*?)(\d+)(\.[^.]*)$')

# --- Spanning tree scan for large directories ---
def scan_folders_spanning_tree(folders, progress_callback=None):
    results = []
    sequence_map = set()
    q = Queue()
    for folder in folders:
        q.put(folder)
    count = 0
    while not q.empty():
        current = q.get()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    count += 1
                    if progress_callback:
                        progress_callback(entry.path, count)
                    if entry.is_dir(follow_symlinks=False):
                        results.append({'Path': entry.path, 'File': entry.name})
                        q.put(entry.path)
                    else:
                        m = SEQUENCE_REGEX.match(entry.name)
                        if m:
                            prefix, digits, ext = m.groups()
                            seq_key = f"{prefix}####{ext}"
                            seq_path = os.path.join(os.path.dirname(entry.path), seq_key)
                            sequence_map.add((seq_path, seq_key))
                        else:
                            results.append({'Path': entry.path, 'File': entry.name})
        except Exception as e:
            pass  # Ignore permission errors etc.
    # Add sequence entries
    for seq_path, seq_key in sequence_map:
        results.append({'Path': seq_path, 'File': seq_key})
    return results

# --- UI ---
class FolderScannerApp:
    def __init__(self, master):
        self.master = master
        master.title("AI Folder Structure Scanner")
        master.configure(bg="#222222")
        # Center the window on the screen
        master.update_idletasks()
        width = 800
        height = 400
        x = (master.winfo_screenwidth() // 2) - (width // 2)
        y = (master.winfo_screenheight() // 2) - (height // 2)
        master.geometry(f"{width}x{height}+{x}+{y}")
        self.folders = set()
        # Style
        fg = "#f0f0f0"
        bg = "#222222"
        entry_bg = "#333333"
        btn_bg = "#444444"
        btn_fg = "#f0f0f0"
        # Main frame
        self.frame = Frame(master, bg=bg)
        self.frame.pack(fill=BOTH, expand=True)
        self.progress_label = Label(self.frame, text="Drop folders, browse, or paste paths below:", bg=bg, fg=fg)
        self.progress_label.pack(pady=(10, 0))
        self.text = Text(self.frame, height=6, width=80, bg=entry_bg, fg=fg, insertbackground=fg, highlightbackground=bg, highlightcolor=fg)
        self.text.pack(fill=BOTH, expand=True, padx=10, pady=(5, 0))
        self.text.drop_target_register(DND_FILES)
        self.text.dnd_bind('<<Drop>>', self.on_drop)
        self.text.bind('<Control-v>', self.on_paste)
        # Buttons frame at bottom
        self.button_frame = Frame(self.frame, bg=bg)
        self.button_frame.pack(side="bottom", fill="x", pady=(10, 0))
        self.browse_button = Button(self.button_frame, text="Browse Folders", command=self.browse_folders, bg=btn_bg, fg=btn_fg, activebackground="#666666", activeforeground=fg)
        self.browse_button.pack(side="left", padx=10, pady=5)
        self.scan_button = Button(self.button_frame, text="Scan and Export JSON", command=self.start_scan, bg=btn_bg, fg=btn_fg, activebackground="#666666", activeforeground=fg)
        self.scan_button.pack(side="left", padx=10, pady=5)
        # Append/Overwrite option
        self.save_mode_var = StringVar(value="overwrite")
        self.save_mode_dropdown = OptionMenu(self.button_frame, self.save_mode_var, "overwrite", "append")
        self.save_mode_dropdown.config(bg=btn_bg, fg=btn_fg, activebackground="#666666", activeforeground=fg, highlightbackground=bg)
        self.save_mode_dropdown.pack(side="left", padx=10, pady=5)
        # Progress bar below buttons
        self.progress_var = 0
        self.progress_bar = Frame(self.frame, bg="#444444", height=20)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_fill = Frame(self.progress_bar, bg="#00c853", height=20, width=0)
        self.progress_fill.place(x=0, y=0, relheight=1)
        self.progress_text = Label(self.progress_bar, text="", bg="#444444", fg=fg)
        self.progress_text.place(relx=0.5, rely=0.5, anchor="center")
        # Scrollbar
        self.scrollbar = Scrollbar(self.text, command=self.text.yview)
        self.text['yscrollcommand'] = self.scrollbar.set
        self.scrollbar.pack_forget()  # Hide default scrollbar

    def update_progress(self, percent, text):
        bar_width = self.progress_bar.winfo_width()
        fill_width = int(bar_width * percent)
        self.progress_fill.config(width=fill_width)
        self.progress_text.config(text=text)
        self.frame.update_idletasks()

    def on_drop(self, event):
        paths = self.master.tk.splitlist(event.data)
        for p in paths:
            if os.path.isdir(p):
                self.folders.add(p)
                self.text.insert(END, p + '\n')

    def on_paste(self, event):
        try:
            pasted = self.master.clipboard_get()
            for line in pasted.splitlines():
                line = line.strip('"')
                if os.path.isdir(line):
                    self.folders.add(line)
                    self.text.insert(END, line + '\n')
        except Exception:
            pass
        return 'break'

    def browse_folders(self):
        dirs = filedialog.askdirectory(mustexist=True, title="Select Folder(s)")
        if dirs:
            if isinstance(dirs, str):
                self.folders.add(dirs)
                self.text.insert(END, dirs + '\n')
            else:
                for d in dirs:
                    self.folders.add(d)
                    self.text.insert(END, d + '\n')

    def start_scan(self):
        self.folders.update([line.strip() for line in self.text.get('1.0', END).splitlines() if os.path.isdir(line.strip())])
        if not self.folders:
            messagebox.showerror("No folders", "Please add at least one folder.")
            return
        # Use dropdown value for append/overwrite
        self.append_mode = (self.save_mode_var.get().strip().lower() == 'append')
        self.update_progress(0, "Counting items...")
        self.frame.update()
        threading.Thread(target=self.scan_and_export_with_count, daemon=True).start()

    def scan_and_export_with_count(self):
        start_time = time.time()
        # Count total items for progress bar in background using BFS queue
        from queue import Queue
        total_count = [0]
        def count_items_bfs(folders):
            q = Queue()
            for folder in folders:
                q.put(folder)
            while not q.empty():
                current = q.get()
                try:
                    with os.scandir(current) as it:
                        for entry in it:
                            total_count[0] += 1
                            if total_count[0] % 100 == 0:
                                self.update_progress(0, f"Counting: {total_count[0]} items...")
                            if entry.is_dir(follow_symlinks=False):
                                q.put(entry.path)
                except Exception:
                    pass
        count_items_bfs(self.folders)
        scanned = [0]
        def progress_callback(path, count):
            scanned[0] = count
            percent = min(1.0, scanned[0] / max(1, total_count[0]))
            # Layout: left: 'Scanning', center: filename, right: count
            bar_width = self.progress_bar.winfo_width() or 1
            left_text = "Scanning"
            right_text = f"{scanned[0]:>7} / {total_count[0]:<7} files"
            base_name = os.path.basename(path)
            max_name_len = 32
            if len(base_name) > max_name_len:
                base_name = base_name[:max_name_len-3] + '...'
            # Calculate padding for center
            left_width = 90  # px, adjust as needed
            right_width = 150  # px, adjust as needed
            center_width = bar_width - left_width - right_width
            # Set label positions
            self.progress_text.place_forget()
            # Left label
            if not hasattr(self, 'progress_left'):
                self.progress_left = Label(self.progress_bar, text=left_text, bg="#444444", fg="#f0f0f0", anchor="w")
                self.progress_left.place(x=5, rely=0.5, anchor="w")
            else:
                self.progress_left.config(text=left_text)
            # Center label
            if not hasattr(self, 'progress_center'):
                self.progress_center = Label(self.progress_bar, text=base_name, bg="#444444", fg="#f0f0f0", anchor="center")
                self.progress_center.place(relx=0.5, rely=0.5, anchor="center")
            else:
                self.progress_center.config(text=base_name)
            # Right label
            if not hasattr(self, 'progress_right'):
                self.progress_right = Label(self.progress_bar, text=right_text, bg="#444444", fg="#f0f0f0", anchor="e")
                self.progress_right.place(relx=1.0, x=-5, rely=0.5, anchor="e")
            else:
                self.progress_right.config(text=right_text)
            self.update_progress(percent, "")
        results = scan_folders_spanning_tree(list(self.folders), progress_callback)
        results = sorted(results, key=lambda x: x['Path'])
        # Append or overwrite logic
        output_path = "ai_folder_structure.json"
        if getattr(self, 'append_mode', False) and os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # Avoid duplicates by using a set of (Path, File)
                existing_set = set((item['Path'], item['File']) for item in existing)
                new_results = [item for item in results if (item['Path'], item['File']) not in existing_set]
                results = existing + new_results
            except Exception:
                pass  # If error, just use new results
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        elapsed = time.time() - start_time
        self.update_progress(1.0, f"Done. {len(results)} entries saved to ai_folder_structure.json.")
        messagebox.showinfo("Done", f"Scan complete. {len(results)} entries saved to ai_folder_structure.json.\nElapsed time: {elapsed:.2f} seconds.")

if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD
    except ImportError:
        print("Please install tkinterdnd2: pip install tkinterdnd2")
        exit(1)
    root = TkinterDnD.Tk()
    app = FolderScannerApp(root)
    root.mainloop()
