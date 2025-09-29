import os
import re
import sys
import time
import json
import hashlib
import threading
import tkinter as tk
from tkinter import messagebox
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# --- Configuration -------------------------------------------------
# GitHub repo to check for updates (owner/repo)
GITHUB_REPO = 'cros-mstr/Nested'
# If True, the app will automatically replace the local file with the
# remote file without prompting. Default False -> prompt before updating.
AUTO_UPDATE_FROM_GITHUB = False
# Whether the app should watch this file and automatically update the
# in-file __version__ string whenever you save the script locally.
WATCH_AND_UPDATE_VERSION = True
# Poll interval for file watcher (seconds)
WATCH_POLL_INTERVAL = 1.0
# --------------------------------------------------------------------

# in-file version marker — this will be automatically updated on save
__version__ = '0.0.0'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME = os.path.basename(__file__)
FULL_PATH = os.path.abspath(__file__)

def compute_file_hash(path):
    h = hashlib.sha1()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def replace_version_in_file(path, new_version):
    """Replace the __version__ = '...' line in the file with new_version.
    Returns True if replaced, False otherwise.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        pattern = r"^__version__\s*=\s*['\"][^'\"]*['\"]"
        repl = f"__version__ = '{new_version}'"
        (new_text, count) = re.subn(pattern, repl, text, flags=re.M)
        if count == 0:
            # no existing version line: prepend one
            new_text = repl + '\n' + text
        # Write safely to a temp file then replace
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(new_text)
        os.replace(tmp, path)
        return True
    except Exception as e:
        print('Error updating version in file:', e)
        return False

def read_remote_raw(repo, branch, filename):
    url = f'https://raw.githubusercontent.com/{repo}/{branch}/{filename}'
    try:
        req = Request(url, headers={'User-Agent': 'python-urllib/3'})
        with urlopen(req, timeout=6) as resp:
            return resp.read()
    except (HTTPError, URLError) as e:
        return None

def find_remote_file_variants(repo, filename):
    # Try common branches and filename variants (.py)
    branches = ['main', 'master', 'develop']
    variants = [filename, filename + '.py'] if not filename.endswith('.py') else [filename]
    for branch in branches:
        for v in variants:
            data = read_remote_raw(repo, branch, v)
            if data is not None:
                return (branch, v, data)
    return (None, None, None)

def check_github_for_newer_version(repo, local_path):
    filename = os.path.basename(local_path)
    branch, remote_name, remote_bytes = find_remote_file_variants(repo, filename)
    if not remote_bytes:
        return {'found': False}
    local_bytes = None
    try:
        with open(local_path, 'rb') as f:
            local_bytes = f.read()
    except Exception:
        local_bytes = b''
    same = (hashlib.sha1(remote_bytes).hexdigest() == hashlib.sha1(local_bytes).hexdigest())
    return {
        'found': True,
        'branch': branch,
        'remote_name': remote_name,
        'remote_bytes': remote_bytes,
        'is_same': same
    }

def backup_and_write_local(local_path, new_bytes):
    ts = int(time.time())
    backup_path = local_path + f'.backup.{ts}'
    try:
        if os.path.exists(local_path):
            os.replace(local_path, backup_path)
        with open(local_path, 'wb') as f:
            f.write(new_bytes)
        return backup_path
    except Exception as e:
        print('Error writing update to local file:', e)
        return None

# ----------------- GUI and existing app functionality ----------------

def open_app_store():
    messagebox.showinfo("App Store", "Opening App Store...")

def check_updates():
    messagebox.showinfo("Updates", "Checking for updates...")

def show_installed_apps():
    messagebox.showinfo("Installed Apps", "Listing installed apps...")


root = tk.Tk()
root.title("Windows App Manager")
root.geometry("640x420")

canvas = tk.Canvas(root, highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Background image logic
BG_CANDIDATES = ["background.png", "background.jpg", "background.jpeg", "bg.png"]
bg_image_path = None
for name in BG_CANDIDATES:
    p = os.path.join(BASE_DIR, name)
    if os.path.exists(p):
        bg_image_path = p
        break

orig_bg_image = None
tk_bg_image = None
if bg_image_path and PIL_AVAILABLE:
    try:
        orig_bg_image = Image.open(bg_image_path).convert('RGBA')
    except Exception:
        orig_bg_image = None
elif bg_image_path and not PIL_AVAILABLE:
    try:
        tk_bg_image = tk.PhotoImage(file=bg_image_path)
    except Exception:
        tk_bg_image = None

canvas_bg_id = None

def draw_gradient(w, h):
    canvas.delete('gradient')
    steps = 24
    for i in range(steps):
        r = int(7 + (9 - 7) * (i / (steps-1)))
        g = int(16 + (32 - 16) * (i / (steps-1)))
        b = int(38 + (43 - 38) * (i / (steps-1)))
        color = f'#{r:02x}{g:02x}{b:02x}'
        y0 = int(i * h / steps)
        y1 = int((i + 1) * h / steps)
        canvas.create_rectangle(0, y0, w, y1, fill=color, width=0, tags=('gradient',))

BUTTON_SIZE = 88
BUTTON_SPACING = 12
buttons = []
button_window_ids = []

def make_button(text, command):
    btn = tk.Button(root, text=text, command=command, wraplength=BUTTON_SIZE-12,
                    justify='center', font=("Segoe UI", 9, 'bold'))
    return btn

btn_store = make_button("App\nStore", open_app_store)
btn_updates = make_button("Updates", check_updates)
btn_installed = make_button("Installed\nApps", show_installed_apps)

buttons = [btn_store, btn_updates, btn_installed]

def position_buttons(w, h):
    count = len(buttons)
    total_width = count * BUTTON_SIZE + (count - 1) * BUTTON_SPACING
    start_x = (w - total_width) / 2 + BUTTON_SIZE / 2
    y = h / 2
    for i, btn in enumerate(buttons):
        x = start_x + i * (BUTTON_SIZE + BUTTON_SPACING)
        if i < len(button_window_ids):
            canvas.coords(button_window_ids[i], x, y)
        else:
            wid = canvas.create_window(x, y, window=btn, width=BUTTON_SIZE, height=BUTTON_SIZE)
            button_window_ids.append(wid)


is_fullscreen = False

def toggle_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    try:
        root.attributes('-fullscreen', is_fullscreen)
    except Exception:
        if is_fullscreen:
            root.state('zoomed')
        else:
            root.state('normal')


def on_canvas_configure(event):
    global tk_bg_image, canvas_bg_id
    w = event.width
    h = event.height
    canvas.delete('gradient')

    if orig_bg_image and PIL_AVAILABLE:
        try:
            resized = orig_bg_image.resize((max(1, w), max(1, h)), Image.LANCZOS)
            tk_bg_image = ImageTk.PhotoImage(resized)
            if canvas_bg_id is None:
                canvas_bg_id = canvas.create_image(0, 0, anchor='nw', image=tk_bg_image)
            else:
                canvas.itemconfig(canvas_bg_id, image=tk_bg_image)
        except Exception:
            draw_gradient(w, h)
    elif tk_bg_image:
        try:
            if canvas_bg_id is None:
                canvas_bg_id = canvas.create_image(0, 0, anchor='nw', image=tk_bg_image)
            else:
                canvas.itemconfig(canvas_bg_id, image=tk_bg_image)
        except Exception:
            draw_gradient(w, h)
    else:
        draw_gradient(w, h)

    position_buttons(w, h)


root.bind('<Alt-Return>', toggle_fullscreen)
root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))

canvas.bind('<Configure>', on_canvas_configure)

# Status bar and check button
status_var = tk.StringVar(value=f'Version: {__version__}')
status_label = tk.Label(root, textvariable=status_var, bg='#00000000', fg='#cbd5e1')
status_window = canvas.create_window(12, 12, window=status_label, anchor='nw')

def check_now_and_maybe_update():
    status_var.set('Checking GitHub...')
    root.update_idletasks()
    info = check_github_for_newer_version(GITHUB_REPO, FULL_PATH)
    if not info.get('found'):
        messagebox.showinfo('Update check', 'No matching file found in repository')
        status_var.set(f'Version: {__version__}')
        return
    if info.get('is_same'):
        messagebox.showinfo('Update check', 'Local file is up to date with repo')
        status_var.set(f'Version: {__version__}')
        return
    # remote differs
    if AUTO_UPDATE_FROM_GITHUB:
        backup = backup_and_write_local(FULL_PATH, info['remote_bytes'])
        if backup:
            messagebox.showinfo('Updated', f'File updated from GitHub. Backup: {backup}')
        else:
            messagebox.showerror('Update failed', 'Failed to write updated file')
    else:
        if messagebox.askyesno('Update available', 'A different version exists on GitHub. Replace local file with remote?'):
            backup = backup_and_write_local(FULL_PATH, info['remote_bytes'])
            if backup:
                messagebox.showinfo('Updated', f'File updated from GitHub. Backup: {backup}')
            else:
                messagebox.showerror('Update failed', 'Failed to write updated file')
    status_var.set(f'Version: {__version__}')

check_btn = tk.Button(root, text='Check GitHub', command=check_now_and_maybe_update)
canvas.create_window(12, 44, window=check_btn, anchor='nw')

# File watcher: update __version__ whenever file is saved
_last_write_by_self = 0

def watcher_thread():
    global _last_write_by_self
    try:
        last_mtime = os.path.getmtime(FULL_PATH)
    except Exception:
        last_mtime = None
    while True:
        try:
            time.sleep(WATCH_POLL_INTERVAL)
            m = os.path.getmtime(FULL_PATH)
            if last_mtime is None:
                last_mtime = m
                continue
            if m != last_mtime:
                # ignore changes caused by our own updater within 1s
                if time.time() - _last_write_by_self < 1.0:
                    last_mtime = m
                    continue
                last_mtime = m
                # compute hash and update version in-file
                h = compute_file_hash(FULL_PATH)
                if h:
                    short = h[:10]
                    # Replace __version__ in file
                    success = replace_version_in_file(FULL_PATH, short)
                    if success:
                        # mark that we wrote the file so we don't react to our own write
                        _last_write_by_self = time.time()
                        status_var.set(f'Version: {short} (updated)')
                        print('Version updated to', short)
                else:
                    print('Failed to compute hash for', FULL_PATH)
        except Exception as e:
            print('Watcher error:', e)

if WATCH_AND_UPDATE_VERSION:
    t = threading.Thread(target=watcher_thread, daemon=True)
    t.start()

# initial layout
canvas.update_idletasks()
position_buttons(canvas.winfo_width() or 640, canvas.winfo_height() or 420)

root.mainloop()