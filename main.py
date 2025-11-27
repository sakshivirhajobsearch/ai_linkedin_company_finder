import os
import csv
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import requests
import socket
import ssl
import time
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

# ===== UI CONFIG =====
BG = "#000000"
FG = "#00FF41"
BTN = "#003300"
RED = "#FF3333"
GREEN = "#00FF41"

MAX_THREADS = 8
MAX_LENGTH = 30

DOMAIN_COL = 30
BOOL_COL   = 7
HTTP_COL   = 7
STATUS_COL = 15

# ===== OUTPUT CONFIG =====
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
STATE_FILE = os.path.join(OUTPUT_DIR, f"autosave_{TIMESTAMP}.json")

# ===== VALID TLDS =====
VALID_TLDS = [
    "com","net","org","in","us","uk","de","fr",
    "cn","jp","io","gov","edu","biz","info",
    "aero","nl","me","ai","res"
]

# ===== DOMAIN UTILS =====
def normalize_url(domain):
    if domain.startswith("http"):
        return domain
    return "https://www." + domain if not domain.startswith("www.") else "https://" + domain

def extract_domain(url):
    return url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

def dns_check(domain):
    try:
        socket.setdefaulttimeout(5)
        socket.gethostbyname(domain)
        return True
    except:
        return False

def ssl_check(domain):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain):
                return True
    except:
        return False

def http_status(url):
    try:
        r = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code
    except:
        return None

def format_domain(name):
    if len(name) > MAX_LENGTH:
        return name[:MAX_LENGTH-3] + "..."
    return name.ljust(MAX_LENGTH)

def format_row(name, dns, ssl_ok, http, status):
    domain_txt = format_domain(name)
    dns_txt = str(dns).ljust(BOOL_COL)
    ssl_txt = str(ssl_ok).ljust(BOOL_COL)
    http_txt = ("---" if http is None else str(http)).ljust(HTTP_COL)
    status_txt = status.ljust(STATUS_COL)

    return f"{domain_txt} | {dns_txt} | {ssl_txt} | {http_txt} | {status_txt}"

# ===== GUI APP =====
class WebsiteChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("> WEBSITE STATUS CHECKER")
        self.root.geometry("1200x850")
        self.root.configure(bg=BG)

        self.root.protocol("WM_DELETE_WINDOW", lambda: self.clean_shutdown("WINDOW CLOSED"))
        self.root.bind("<Control-c>", lambda e: self.clean_shutdown("CTRL+C GUI"))
        self.root.bind("<Escape>", lambda e: self.clean_shutdown("ESC KEY"))

        self.websites = []
        self.total = 0
        self.done = 0
        self.valid = 0
        self.invalid = 0

        self.pause = False
        self.stop = False
        self.executor = None

        self.build_ui()

    # ===== UI =====
    def build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = tk.Entry(top, width=70, bg="#101010", fg=FG)
        self.input_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(top, text="BROWSE", command=self.browse, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="START", command=self.start, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="PAUSE", command=self.pause_scan, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="RESUME", command=self.resume_scan, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="CANCEL", command=lambda: self.clean_shutdown("CANCEL"), bg="#330000", fg=FG).pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.root, text="Progress: 0%", bg=BG, fg=FG)
        self.status_label.pack(pady=5)

        self.log_box = tk.Text(self.root, bg="#050505", fg=FG, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_box.tag_config("valid", foreground=GREEN)
        self.log_box.tag_config("invalid", foreground=RED)
        self.log_box.tag_config("info", foreground="#00FFFF")

        header = format_row("DOMAIN", "DNS", "SSL", "HTTP", "STATUS") + "\n"
        self.log_box.insert(tk.END, header, "valid")
        self.log_box.insert(tk.END, "-" * 95 + "\n")

    # ===== CORE =====
    def browse(self):
        path = filedialog.askopenfilename()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def start(self):
        path = self.input_entry.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "Input file not found")
            return

        with open(path) as f:
            self.websites = [x.strip() for x in f if x.strip()]

        self.total = len(self.websites)
        self.done = 0
        self.valid = 0
        self.invalid = 0
        self.stop = False
        self.pause = False

        print("\n▶ SCAN STARTED\n")

        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

        for site in self.websites:
            self.executor.submit(self.process_site, site)

    def process_site(self, site):
        while self.pause and not self.stop:
            time.sleep(0.3)

        if self.stop:
            return

        domain = extract_domain(site)
        formatted_name = format_domain(domain)

        website = normalize_url(site)

        dns = dns_check(domain)
        ssl_ok = ssl_check(domain)
        http = http_status(website)

        status = "WORKING" if dns and ssl_ok and http and http < 400 else "NOT WORKING"

        self.write_result(formatted_name, dns, ssl_ok, http, status)

    # ===== OUTPUT =====
    def write_result(self, formatted_name, dns, ssl_ok, http, status):
        line = format_row(formatted_name, dns, ssl_ok, http, status)

        self.done += 1

        if status == "WORKING":
            self.valid += 1
            color = Fore.GREEN
            tag = "valid"
        else:
            self.invalid += 1
            color = Fore.RED
            tag = "invalid"

        print(color + line)

        self.root.after(0, self.update_ui, line, tag)

    def update_ui(self, line, tag):
        self.log_box.insert(tk.END, line + "\n", tag)
        self.log_box.see(tk.END)

        run_status = "⏸ PAUSED" if self.pause else "▶ RUNNING"

        percent = (self.done / self.total) * 100
        self.status_label.config(
            text=f"Progress: {percent:.2f}% | ✅ WORKING: {self.valid} | ❌ NOT WORKING: {self.invalid} | {run_status}"
        )

        if self.done >= self.total and not self.pause:
            self.clean_shutdown("FINISHED")

    # ===== CONTROLS =====
    def pause_scan(self):
        self.pause = True
        print("\n⏸ PAUSED\n")
        self.log_box.insert(tk.END, "\n⏸ PAUSED\n", "info")
        self.log_box.see(tk.END)

    def resume_scan(self):
        self.pause = False
        print("\n▶ RESUMED\n")
        self.log_box.insert(tk.END, "\n▶ RESUMED\n", "info")
        self.log_box.see(tk.END)

    def clean_shutdown(self, reason):
        print(f"\n[CLEAN EXIT] {reason}")
        self.stop = True

        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)

        self.root.quit()
        self.root.destroy()
        os._exit(0)

# ===== RUN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = WebsiteChecker(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.clean_shutdown("CTRL+C TERMINAL")
