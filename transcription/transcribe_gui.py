#!/usr/bin/env python3
"""
Минимальный GUI для запуска transcribe_to_obsidian.py (tkinter, без pip-зависимостей).
Выбор папок, флаги --recursive, --overwrite, пауза между файлами (снижение нагрузки на GPU/диск).
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def main() -> None:
    root = tk.Tk()
    root.title("Транскрибация → Obsidian 00_inbox")
    root.minsize(520, 380)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_py = os.path.join(script_dir, "transcribe_to_obsidian.py")

    var_in = tk.StringVar()
    var_out = tk.StringVar()
    var_recursive = tk.BooleanVar(value=False)
    var_overwrite = tk.BooleanVar(value=False)
    var_sleep = tk.StringVar(value="0")
    var_manifest = tk.StringVar()

    def browse_in() -> None:
        p = filedialog.askdirectory(title="Папка с mp3")
        if p:
            var_in.set(p)

    def browse_out() -> None:
        p = filedialog.askdirectory(title="Папка вывода (00_inbox vault)")
        if p:
            var_out.set(p)

    def browse_manifest() -> None:
        p = filedialog.asksaveasfilename(
            title="Файл манифеста CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
        )
        if p:
            var_manifest.set(p)

    def run() -> None:
        inp = var_in.get().strip()
        out = var_out.get().strip()
        if not inp or not out:
            messagebox.showwarning("Нужны пути", "Укажите папку с mp3 и папку 00_inbox.")
            return
        if not os.path.isfile(script_py):
            messagebox.showerror("Ошибка", f"Не найден скрипт: {script_py}")
            return

        cmd = [sys.executable, script_py, inp, out]
        if var_recursive.get():
            cmd.append("--recursive")
        if var_overwrite.get():
            cmd.append("--overwrite")
        man = var_manifest.get().strip()
        if man:
            cmd.extend(["--manifest", man])
        try:
            sleep_sec = max(0.0, float(var_sleep.get().replace(",", ".")))
        except ValueError:
            messagebox.showwarning("Пауза", "Пауза между файлами: укажите число секунд (например 0 или 2).")
            return
        if sleep_sec > 0:
            cmd.extend(["--sleep-between-seconds", str(sleep_sec)])

        log.delete("1.0", tk.END)
        log.insert(tk.END, "Команда:\n" + subprocess.list2cmdline(cmd) + "\n\n")
        root.update()

        try:
            proc = subprocess.run(
                cmd,
                cwd=script_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            log.insert(tk.END, proc.stdout or "")
            if proc.stderr:
                log.insert(tk.END, "\n--- stderr ---\n" + proc.stderr)
            log.insert(tk.END, f"\nКод выхода: {proc.returncode}\n")
            if proc.returncode != 0:
                messagebox.showerror("Ошибка", f"Процесс завершился с кодом {proc.returncode}. См. лог ниже.")
            else:
                messagebox.showinfo("Готово", "Транскрибация завершена без ошибки (код 0).")
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    frm = ttk.Frame(root, padding=10)
    frm.pack(fill=tk.BOTH, expand=True)

    r = 0
    ttk.Label(frm, text="Папка с mp3:").grid(row=r, column=0, sticky=tk.W)
    ttk.Entry(frm, textvariable=var_in, width=50).grid(row=r, column=1, sticky=tk.EW, padx=4)
    ttk.Button(frm, text="Обзор…", command=browse_in).grid(row=r, column=2)
    r += 1
    ttk.Label(frm, text="Папка 00_inbox:").grid(row=r, column=0, sticky=tk.W)
    ttk.Entry(frm, textvariable=var_out, width=50).grid(row=r, column=1, sticky=tk.EW, padx=4)
    ttk.Button(frm, text="Обзор…", command=browse_out).grid(row=r, column=2)
    r += 1

    ttk.Checkbutton(frm, text="Рекурсивно (--recursive)", variable=var_recursive).grid(
        row=r, column=1, sticky=tk.W
    )
    r += 1
    ttk.Checkbutton(frm, text="Перезаписывать существующие .md (--overwrite)", variable=var_overwrite).grid(
        row=r, column=1, sticky=tk.W
    )
    r += 1

    ttk.Label(frm, text="Манифест CSV (необязательно):").grid(row=r, column=0, sticky=tk.W)
    ttk.Entry(frm, textvariable=var_manifest, width=50).grid(row=r, column=1, sticky=tk.EW, padx=4)
    ttk.Button(frm, text="Сохранить как…", command=browse_manifest).grid(row=r, column=2)
    r += 1

    ttk.Label(frm, text="Пауза между файлами (сек, 0 = без паузы):").grid(row=r, column=0, sticky=tk.W)
    ttk.Entry(frm, textvariable=var_sleep, width=10).grid(row=r, column=1, sticky=tk.W, padx=4)
    r += 1

    ttk.Button(frm, text="Запустить транскрибацию", command=run).grid(row=r, column=1, pady=10, sticky=tk.W)
    r += 1

    ttk.Label(frm, text="Лог:").grid(row=r, column=0, sticky=tk.NW)
    log = tk.Text(frm, height=12, wrap=tk.WORD)
    log.grid(row=r, column=1, columnspan=2, sticky=tk.NSEW, pady=4)
    sb = ttk.Scrollbar(frm, command=log.yview)
    sb.grid(row=r, column=3, sticky=tk.NS)
    log["yscrollcommand"] = sb.set

    frm.columnconfigure(1, weight=1)
    frm.rowconfigure(r, weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
