import requests
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import threading
from PIL import Image, ImageTk
import io
import os

def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    res = requests.post(url, json={"usernames": [username]})
    if res.status_code != 200:
        raise Exception(f"Failed to fetch user ID for '{username}'")
    data = res.json().get("data", [])
    if not data:
        raise Exception(f"Username '{username}' not found")
    return data[0]["id"]

def get_all_badges(user_id):
    badges = {}
    cursor = None
    while True:
        url = f"https://badges.roblox.com/v1/users/{user_id}/badges?limit=100&sortOrder=Asc"
        if cursor:
            url += f"&cursor={cursor}"
        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f"Failed to fetch badges for user {user_id}")
        data = res.json()
        for badge in data["data"]:
            badges[badge["id"]] = badge
        cursor = data.get("nextPageCursor")
        if not cursor:
            break
    return badges

def get_badge_info(badge_id):
    url = f"https://badges.roblox.com/v1/badges/{badge_id}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    return res.json()

def fetch_badge_icon(badge_id):
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={badge_id}&format=Png&size=48x48"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            thumb_url = res.json()["data"][0].get("imageUrl")
            if thumb_url:
                img_res = requests.get(thumb_url)
                if img_res.status_code == 200:
                    image = Image.open(io.BytesIO(img_res.content)).resize((48, 48))
                    return ImageTk.PhotoImage(image)
    except:
        return None

def get_badge_game_name(badge_info):
    game_id = badge_info.get("awardingUniverseId")
    if not game_id:
        return "Unknown Game"
    try:
        url = f"https://games.roblox.com/v1/games?universeIds={game_id}"
        res = requests.get(url)
        if res.status_code == 200:
            games = res.json().get("data", [])
            if games:
                return games[0].get("name", "Unknown Game")
    except:
        pass
    return "Unknown Game"

def compare_badges(b1, b2):
    shared = []
    shared_ids = set(b1.keys()) & set(b2.keys())
    for badge_id in shared_ids:
        info = get_badge_info(badge_id)
        if info:
            try:
                created = info.get("created")
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
            except:
                created_dt = None

            shared.append({
                "id": badge_id,
                "name": info.get("name", "Unknown Badge"),
                "description": info.get("description", "No description."),
                "awardedCount": info.get("awardedCount", 0),
                "created": created_dt,
                "game": get_badge_game_name(info)
            })

    return sorted(shared, key=lambda x: x["created"] or datetime.min, reverse=True)

def log(message):
    log_console.insert(tk.END, message + "\n")
    log_console.see(tk.END)
    root.update()

def start_compare_thread():
    threading.Thread(target=start_compare).start()

def start_compare():
    log_console.delete("1.0", tk.END)
    result_panel.config(state="normal")
    result_panel.delete("1.0", tk.END)
    result_panel.config(state="disabled")

    user1 = username1_entry.get().strip()
    user2 = username2_entry.get().strip()

    try:
        log("🔍 Resolving user IDs...")
        uid1 = get_user_id(user1)
        uid2 = get_user_id(user2)

        log("🔄 Fetching badges...")
        badges1 = get_all_badges(uid1)
        log(f"✅ {user1} has {len(badges1)} badges")
        badges2 = get_all_badges(uid2)
        log(f"✅ {user2} has {len(badges2)} badges")

        log("🔍 Comparing shared badges...")
        shared = compare_badges(badges1, badges2)

        result_panel.config(state="normal")
        result_panel.delete("1.0", tk.END)
        result_panel.image_list = []
        result_panel.insert(tk.END, f"Shared Badges (newest first): {len(shared)}\n\n")
        for badge in shared:
            rarity = "🔹 Rare" if badge["awardedCount"] < 1000 else "🔸 Common"
            created_str = badge["created"].strftime("%Y-%m-%d") if badge["created"] else "Unknown"
            img = fetch_badge_icon(badge["id"])
            if img:
                result_panel.image_create(tk.END, image=img)
                result_panel.image_list.append(img)
            result_panel.insert(tk.END, f" 🏅 {badge['name']} ({badge['id']}) — {rarity}\n")
            result_panel.insert(tk.END, f"Game: {badge['game']}\n")
            result_panel.insert(tk.END, f"Description: {badge['description']}\n")
            result_panel.insert(tk.END, f"Created on: {created_str}\n\n")
        result_panel.config(state="disabled")

        log("✅ Comparison complete.")

    except Exception as e:
        log(f"[ERROR] {str(e)}")

root = tk.Tk()
root.title("Roblox Shared Badge Checker")
root.geometry("800x550")
root.configure(bg="#2c2f33")

try:
    icon_image = Image.open("image-removebg-preview.png")
    icon_photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(False, icon_photo)
except Exception as e:
    print(f"Could not load icon: {e}")

style = ttk.Style()
style.theme_use("default")
style.configure("TFrame", background="#2c2f33")
style.configure("TButton", background="#99aab5", foreground="#2c2f33")
style.configure("TEntry", fieldbackground="#23272a", foreground="white")

input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="Roblox Username", bg="#2c2f33", fg="white").grid(row=0, column=0, padx=5)
username1_entry = ttk.Entry(input_frame, width=25)
username1_entry.grid(row=1, column=0, padx=5)

tk.Label(input_frame, text="Second Roblox Username", bg="#2c2f33", fg="white").grid(row=0, column=1, padx=5)
username2_entry = ttk.Entry(input_frame, width=25)
username2_entry.grid(row=1, column=1, padx=5)

compare_btn = ttk.Button(input_frame, text="Compare", command=start_compare_thread)
compare_btn.grid(row=1, column=2, padx=5)

container = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4, bg="#2c2f33")
container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

log_console = scrolledtext.ScrolledText(container, height=10, font=("Courier", 10), bg="#23272a", fg="white", insertbackground="white")
container.add(log_console)

bottom_frame = tk.Frame(container, bg="#2c2f33")
result_panel = scrolledtext.ScrolledText(bottom_frame, font=("Segoe UI", 10), bg="#2c2f33", fg="white", insertbackground="white")
result_panel.pack(fill=tk.BOTH, expand=True)
container.add(bottom_frame)
result_panel.config(state="disabled")
result_panel.image_list = []

root.mainloop()