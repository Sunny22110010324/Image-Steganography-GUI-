import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import pyttsx3
import threading

img = None
img_tk = None
decoded_secret = ""

root = tk.Tk()
root.title("🕵️‍♂️ Steganography Studio")
root.configure(bg="#f0f4ff")

# ===== Heading =====
heading = tk.Label(
    root,
    text="🛡️ Steganography Studio 🛡️",
    font=("Helvetica", 28, "bold"),
    fg="#0a043c",
    bg="#f0f4ff"
)
heading.pack(pady=20)

frame = tk.Frame(root, bg="#f0f4ff")
frame.pack(pady=10, padx=20, fill="x")

# ===== Input Image Button =====
def open_file():
    global img, img_tk
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
    )
    if file_path:
        img_cv = cv2.imread(file_path)
        if img_cv is None:
            img = None
            image_label.config(image='', bg="white")
            return
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_cv = img_cv.astype(np.uint8)
        img = img_cv
        pil_img = Image.fromarray(img)
        pil_img = pil_img.resize((400, 300), Image.LANCZOS)  # Medium size
        img_tk = ImageTk.PhotoImage(pil_img)
        image_label.configure(image=img_tk, bg="white")
        image_label.image = img_tk

input_btn = tk.Button(
    frame, text="📁 Input Image",
    command=open_file,
    font=("Helvetica", 16, "bold"),
    bg="#4CAF50", fg="white", relief="flat",
    activebackground="#45a049", padx=20, pady=10, bd=0,
)
input_btn.grid(row=0, column=0, padx=10, sticky="w")

# ===== Password Entry =====
pass_icon = tk.Label(frame, text="🗝️ Password:", font=("Helvetica", 16, "bold"), bg="#f0f4ff")
pass_icon.grid(row=0, column=1, padx=5, sticky="e")

password_entry = ttk.Entry(frame, font=("Helvetica", 16), width=15)
password_entry.grid(row=0, column=2, padx=5)

# ===== Secret Entry =====
secret_frame = tk.Frame(root, bg="#f0f4ff")
secret_frame.pack(pady=10, fill="x", padx=20)

secret_icon = tk.Label(secret_frame, text="✉️ Secret Message:", font=("Helvetica", 18, "bold"), bg="#f0f4ff")
secret_icon.pack(side="left")

secret_entry = ttk.Entry(secret_frame, font=("Helvetica", 18), width=50)
secret_entry.pack(side="left", padx=10)

# ===== Image Display =====
image_frame = tk.Frame(root, bg="#f0f4ff")
image_frame.pack(pady=20)

image_label = tk.Label(image_frame, bg="white", width=400, height=300, bd=5, relief="solid")
image_label.pack()

# ===== Output Box =====
output_box = tk.Label(
    root,
    text="🔎 Decoded message will appear here.",
    font=("Helvetica", 16, "italic"),
    bg="#e3f2fd",
    fg="#0d47a1",
    bd=3,
    relief="groove",
    padx=15,
    pady=10,
    wraplength=600
)
output_box.pack(pady=20)
output_box.configure(highlightbackground="#64b5f6", highlightthickness=2)

# ===== Encode and Decode Functions =====
def encode_message():
    global img
    if img is None:
        output_box.config(text="❌ Load an image first!", fg="red")
        return

    secret = secret_entry.get()
    password = password_entry.get()
    if not secret or not password:
        output_box.config(text="❌ Enter secret message and password!", fg="red")
        return

    h, w, c = img.shape
    max_bytes = (h * w * c) // 8
    message = f"{password}:{secret}~"
    bin_message = ''.join(format(ord(char), '08b') for char in message)
    if len(bin_message) > h * w * c:
        output_box.config(text=f"❌ Message too long! Max: {max_bytes - len(password) - 2} chars", fg="red")
        return

    flat = img.flatten().copy()
    for i, bit in enumerate(bin_message):
        flat[i] = (int(flat[i]) & ~1) | int(bit)

    encoded_img = flat.reshape(img.shape)

    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
    if not file_path:
        return

    cv2.imwrite(file_path, cv2.cvtColor(encoded_img, cv2.COLOR_RGB2BGR))

    secret_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)
    image_label.configure(image='', bg="white")
    output_box.config(text="✅ Message successfully encoded and saved!", fg="#2e7d32")

def decode_message():
    global img, decoded_secret
    if img is None:
        output_box.config(text="❌ Load an image first!", fg="red")
        return

    flat = img.flatten()
    bits = [str(flat[i] & 1) for i in range(len(flat))]
    chars = ""
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        if len(byte) < 8:
            break
        char = chr(int(''.join(byte), 2))
        if char == "~":
            break
        chars += char

    if ':' not in chars:
        output_box.config(text="❌ No valid hidden message found!", fg="red")
        return

    passwd, secret = chars.split(':', 1)
    if passwd != password_entry.get():
        output_box.config(text="❌ Incorrect password!", fg="red")
        return

    decoded_secret = secret
    output_box.config(text=f"🔓 Secret Message: {secret}", fg="#1a237e")

def speak_message():
    global decoded_secret
    if not decoded_secret:
        output_box.config(text="❌ No message to speak. Decode first!", fg="red")
        return
    threading.Thread(target=_speak_thread).start()

def _speak_thread():
    engine = pyttsx3.init()
    engine.say(decoded_secret)
    engine.runAndWait()

def save_audio():
    global decoded_secret
    if not decoded_secret:
        output_box.config(text="❌ No message to save. Decode first!", fg="red")
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".mp3",
        filetypes=[("MP3 Files", "*.mp3"), ("WAV Files", "*.wav")]
    )
    if not file_path:
        return
    threading.Thread(target=_save_audio_thread, args=(file_path,)).start()
    output_box.config(text="💾 Saving audio file...", fg="#1565c0")

def _save_audio_thread(file_path):
    engine = pyttsx3.init()
    engine.save_to_file(decoded_secret, file_path)
    engine.runAndWait()
    output_box.config(text=f"✅ Audio saved at: {file_path}", fg="#2e7d32")

# ===== Buttons Row (Encode, Decode, Speak, Save Audio) =====
encode_btn = tk.Button(
    frame, text="🔐 Encode",
    command=encode_message,
    font=("Helvetica", 16, "bold"),
    bg="#2196F3", fg="white", relief="flat",
    activebackground="#1976D2", padx=20, pady=10, bd=0,
)
encode_btn.grid(row=0, column=3, padx=10)

decode_btn = tk.Button(
    frame, text="📤 Decode",
    command=decode_message,
    font=("Helvetica", 16, "bold"),
    bg="#FF9800", fg="white", relief="flat",
    activebackground="#F57C00", padx=20, pady=10, bd=0,
)
decode_btn.grid(row=0, column=4, padx=10)

speak_btn = tk.Button(
    frame, text="🔊 Speak",
    command=speak_message,
    font=("Helvetica", 16, "bold"),
    bg="#9C27B0", fg="white", relief="flat",
    activebackground="#7B1FA2", padx=20, pady=10, bd=0,
)
speak_btn.grid(row=0, column=5, padx=10)

save_audio_btn = tk.Button(
    frame, text="💾 Save Audio",
    command=save_audio,
    font=("Helvetica", 16, "bold"),
    bg="#009688", fg="white", relief="flat",
    activebackground="#00796B", padx=20, pady=10, bd=0,
)
save_audio_btn.grid(row=0, column=6, padx=10)

root.mainloop()
