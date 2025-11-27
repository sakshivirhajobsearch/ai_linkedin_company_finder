import os
import csv
import json
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import time
import requests
import socket
import ssl
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

# ================= GLOBAL CONFIG =================
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

VALID_TLDS = [
    "com","net","org","in","us","uk","de","fr",
    "cn","jp","io","gov","edu","biz","info",
    "aero","nl","me"
]

# ================= OUTPUT FOLDER + TIMESTAMP =================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT_CSV = os.path.join(OUTPUT_DIR, f"domain_results_{TIMESTAMP}.csv")
STATE_FILE = os.path.join(OUTPUT_DIR, f"state_{TIMESTAMP}.json")

# ================= DOMAIN UTILITIES =================
def is_valid_domain(text):
    if "." not in text:
        return False
    if text.lower().endswith((".png",".jpg",".jpeg",".gif",".html",".htm",".pdf",".zip")):
        return False
    return text.split(".")[-1] in VALID_TLDS

def normalize_url(text):
    return text if text.startswith("http") else "https://" + text

def get_domain(url):
    return url.replace("https://","").replace("http://","").split("/")[0]

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
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code
    except:
        return None

def format_name(name):
    if len(name) > MAX_LENGTH:
        return name[:MAX_LENGTH-3] + "..."
    return name.ljust(MAX_LENGTH)

def format_row(name, dns, ssl_ok, http, status):
    domain = name.ljust(DOMAIN_COL)

    dns_txt = str(dns).ljust(BOOL_COL)
    ssl_txt = str(ssl_ok).ljust(BOOL_COL)

    http_txt = "---" if http is None else str(http)
    http_txt = http_txt.ljust(HTTP_COL)

    status_txt = status.ljust(STATUS_COL)

    return f"{domain} | {dns_txt} | {ssl_txt} | {http_txt} | {status_txt}"

# ================= GUI APP =================
class DomainChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("> DOMAIN STATUS CHECKER")
        self.root.geometry("1200x850")
        self.root.configure(bg=BG)

        self.root.bind("<Control-c>", self.force_exit)
        self.root.bind("<Escape>", self.force_exit)

        self.pause_flag = False
        self.stop_flag = False
        self.executor = None

        self.domains = []
        self.total_items = 0
        self.completed = 0
        self.working = 0
        self.not_working = 0

        self.csv_lock = threading.Lock()
        self.build_ui()

    # ================= UI =================
    def build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = tk.Entry(top, width=70, bg="#101010", fg=FG)
        self.input_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(top, text="BROWSE", command=self.browse, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="START", command=self.start, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="PAUSE", command=self.pause, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="RESUME", command=self.resume, bg=BTN, fg=FG).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="CANCEL", command=self.cancel, bg="#330000", fg=FG).pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            self.root,
            text="Progress: 0% | Working: 0 | Not Working: 0",
            bg=BG, fg=FG, font=("Consolas", 12)
        )
        self.status_label.pack(pady=5)

        self.progress_bar = tk.Canvas(self.root, height=20, bg="#101010")
        self.progress_bar.pack(fill=tk.X, padx=10)

        self.log_box = tk.Text(self.root, bg="#050505", fg=FG, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_box.tag_config("valid", foreground=GREEN)
        self.log_box.tag_config("invalid", foreground=RED)

        header = (
            f"{'DOMAIN'.ljust(DOMAIN_COL)} | "
            f"{'DNS'.ljust(BOOL_COL)} | "
            f"{'SSL'.ljust(BOOL_COL)} | "
            f"{'HTTP'.ljust(HTTP_COL)} | "
            f"{'STATUS'.ljust(STATUS_COL)}\n"
        )
        self.log_box.insert(tk.END, header, "valid")
        self.log_box.insert(tk.END, "-" * 95 + "\n", "valid")

    # ================= CORE =================
    def browse(self):
        path = filedialog.askopenfilename()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)

    def start(self):
        path = self.input_entry.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "File not found")
            return

        with open(path) as f:
            self.domains = [x.strip() for x in f if x.strip()]

        self.total_items = len(self.domains)
        self.completed = 0
        self.working = 0
        self.not_working = 0
        self.pause_flag = False
        self.stop_flag = False

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["Domain", "DNS", "SSL", "HTTP", "Status"])

        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

        for domain in self.domains:
            self.executor.submit(self.process_domain, domain)

    def process_domain(self, domain):
        while self.pause_flag and not self.stop_flag:
            time.sleep(0.2)
        if self.stop_flag:
            return

        display_name = format_name(domain)

        if not is_valid_domain(domain):
            msg = format_row(display_name, False, False, None, "INVALID")
            self.log(msg, False)
            return

        url = normalize_url(domain)
        dom = get_domain(url)

        dns = dns_check(dom)
        ssl_ok = ssl_check(dom)
        http = http_status(url)

        status = "WORKING" if dns and ssl_ok and http and http < 400 else "NOT WORKING"
        msg = format_row(display_name, dns, ssl_ok, http, status)

        self.log(msg, status == "WORKING")

    # ================= OUTPUT =================
    def log(self, msg, is_valid):
        with self.csv_lock:
            with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
                f.write(msg + "\n")
                f.flush()
                os.fsync(f.fileno())

        self.completed += 1
        if is_valid:
            self.working += 1
        else:
            self.not_working += 1

        percent = (self.completed / self.total_items) * 100
        color = Fore.GREEN if is_valid else Fore.RED
        print(color + msg)

        self.root.after(0, self.update_ui, msg, is_valid, percent)

    def save_state_before_exit(self, reason):
        state = {
            "reason": reason,
            "completed": self.completed,
            "total": self.total_items,
            "working": self.working,
            "not_working": self.not_working,
            "remaining": self.domains[self.completed:],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

        print(f"✅ STATE SAVED → {STATE_FILE}")

    def pause(self):
        self.pause_flag = True
        self.save_state_before_exit("PAUSE")

    def resume(self):
        self.pause_flag = False

    def cancel(self):
        self.stop_flag = True
        self.save_state_before_exit("CANCEL")
        if self.executor:
            self.executor.shutdown(wait=False)

    def force_exit(self, event=None):
        self.save_state_before_exit("FORCE EXIT")
        self.stop_flag = True
        if self.executor:
            self.executor.shutdown(wait=False)
        self.root.destroy()
        os._exit(0)

# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = DomainChecker(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.save_state_before_exit("KEYBOARD INTERRUPT")
        if app.executor:
            app.executor.shutdown(wait=False)
        root.destroy()
        os._exit(0)
