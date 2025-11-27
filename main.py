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

# ====== APPEARANCE CONFIG ======
BG = "#000000"
FG = "#00FF41"
BTN = "#003300"
RED = "#FF3333"
GREEN = "#00FF41"

MAX_THREADS = 8
MAX_NAME_LEN = 30

DOMAIN_COL = 30
BOOL_COL = 7
HTTP_COL = 7
STATUS_COL = 15

# ====== OUTPUT PATH CONFIG ======
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, f"domain_results_{TIMESTAMP}.csv")
STATE_FILE = os.path.join(OUTPUT_DIR, f"autosave_{TIMESTAMP}.json")

VALID_TLDS = [
    "com","net","org","in","us","uk","de","fr",
    "cn","jp","io","gov","edu","biz","info","aero","nl","me"
]

# ====== DOMAIN UTILITIES ======
def is_valid_domain(text):
    if "." not in text:
        return False
    if text.lower().endswith((".png",".jpg",".jpeg",".gif",".html",".zip",".pdf")):
        return False
    return text.split(".")[-1] in VALID_TLDS

def normalize_url(domain):
    return domain if domain.startswith("http") else "https://" + domain

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

def format_name(name):
    if len(name) > MAX_NAME_LEN:
        return name[:MAX_NAME_LEN-3] + "..."
    return name.ljust(MAX_NAME_LEN)

def format_row(name, dns, ssl_ok, http, status):
    domain = name.ljust(DOMAIN_COL)
    dns_txt = str(dns).ljust(BOOL_COL)
    ssl_txt = str(ssl_ok).ljust(BOOL_COL)
    http_txt = "---" if http is None else str(http)
    http_txt = http_txt.ljust(HTTP_COL)
    status_txt = status.ljust(STATUS_COL)

    return f"{domain} | {dns_txt} | {ssl_txt} | {http_txt} | {status_txt}"

# ====== MAIN GUI CLASS ======
class DomainChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("> DOMAIN STATUS CHECKER")
        self.root.geometry("1200x850")
        self.root.configure(bg=BG)

        self.root.protocol("WM_DELETE_WINDOW", lambda: self.clean_shutdown("WINDOW CLOSED"))
        self.root.bind("<Control-c>", lambda e: self.clean_shutdown("CTRL+C GUI"))
        self.root.bind("<Escape>", lambda e: self.clean_shutdown("ESC KEY"))

        self.domains = []
        self.total = 0
        self.done = 0
        self.working = 0
        self.not_working = 0

        self.pause = False
        self.stop = False
        self.executor = None
        self.lock = threading.Lock()

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
        tk.Button(top, text="CANCEL", command=lambda: self.clean_shutdown("CANCELLED"), bg="#330000", fg=FG).pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.root, text="Progress: 0%", bg=BG, fg=FG, font=("Consolas", 12))
        self.status_label.pack(pady=5)

        self.progress_bar = tk.Canvas(self.root, height=20, bg="#101010")
        self.progress_bar.pack(fill=tk.X, padx=10)

        self.log_box = tk.Text(self.root, bg="#050505", fg=FG, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_box.tag_config("valid", foreground=GREEN)
        self.log_box.tag_config("invalid", foreground=RED)

        header = format_row("DOMAIN", "DNS", "SSL", "HTTP", "STATUS") + "\n"
        self.log_box.insert(tk.END, header, "valid")
        self.log_box.insert(tk.END, "-"*95 + "\n")

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
            self.domains = [x.strip() for x in f if x.strip()]

        self.total = len(self.domains)
        self.done = 0
        self.working = 0
        self.not_working = 0
        self.stop = False
        self.pause = False

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["Domain", "DNS", "SSL", "HTTP", "Status"])

        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

        for item in self.domains:
            self.executor.submit(self.process, item)

    def process(self, domain):
        while self.pause and not self.stop:
            time.sleep(0.2)

        if self.stop:
            return

        display = format_name(domain)

        if not is_valid_domain(domain):
            self.output(display, False, False, None, "INVALID")
            return

        url = normalize_url(domain)

        dns = dns_check(domain)
        ssl_ok = ssl_check(domain)
        http = http_status(url)

        status = "WORKING" if dns and ssl_ok and http and http < 400 else "NOT WORKING"
        self.output(display, dns, ssl_ok, http, status)

    # ===== OUTPUT =====
    def output(self, name, dns, ssl_ok, http, status):
        msg = format_row(name, dns, ssl_ok, http, status)

        with self.lock:
            with open(OUTPUT_CSV, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

        self.done += 1
        if status == "WORKING":
            self.working += 1
        else:
            self.not_working += 1

        percent = (self.done / self.total) * 100

        color = Fore.GREEN if status == "WORKING" else Fore.RED
        print(color + msg)

        self.root.after(0, self.update_ui, msg, status, percent)

    def update_ui(self, msg, status, percent):
        tag = "valid" if status == "WORKING" else "invalid"
        self.log_box.insert(tk.END, msg + "\n", tag)
        self.log_box.see(tk.END)

        self.status_label.config(
            text=f"Progress: {percent:.2f}% | Working: {self.working} | NOT: {self.not_working}"
        )

        w = self.progress_bar.winfo_width()
        fill = int((self.done / self.total) * w)

        self.progress_bar.delete("all")
        self.progress_bar.create_rectangle(0, 0, w, 20, fill="#002200")
        self.progress_bar.create_rectangle(0, 0, fill, 20, fill=GREEN)

        if self.done == self.total:
            self.clean_shutdown("FINISHED")

    # ===== STATE SAVE =====
    def save_state(self, reason):
        state = {
            "reason": reason,
            "completed": self.done,
            "total": self.total,
            "working": self.working,
            "not_working": self.not_working,
            "remaining": self.domains[self.done:],
            "timestamp": datetime.now().isoformat()
        }

        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        print(f"✅ State saved: {STATE_FILE}")

    # ===== CONTROLS =====
    def pause_scan(self):
        self.pause = True
        self.save_state("PAUSED")

    def resume_scan(self):
        self.pause = False

    def clean_shutdown(self, reason):
        print(f"\n[CLEAN EXIT] {reason}")
        self.save_state(reason)

        self.stop = True

        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)

        self.root.quit()
        self.root.destroy()

        os._exit(0)

# ===== RUN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = DomainChecker(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.clean_shutdown("CTRL+C TERMINAL")
