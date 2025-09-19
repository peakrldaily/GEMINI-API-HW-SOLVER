import base64
import requests
import mss
import numpy as np
import customtkinter as ctk
from tkinter import messagebox
import screeninfo

# ---------------- API CONFIG ----------------
API_KEY = "YOUR API KEY"
MODEL = "gemini-2.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# ---------------- SCREENSHOT ----------------
def capture_screen(monitor_index=0):
    """Capture a specific monitor using mss."""
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index >= len(monitors) - 1:
            raise RuntimeError(f"Monitor index {monitor_index} not available. Only {len(monitors)-1} monitor(s) detected.")
        monitor = monitors[monitor_index + 1]
        screenshot = sct.grab(monitor)
        img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        print(f"[DEBUG] Captured monitor {monitor_index} ({monitor['width']}x{monitor['height']})")
        return img_bytes

# ---------------- AI QUERY ----------------
def get_ai_answer(img_bytes, instruction_text):
    try:
        print("[DEBUG] Encoding image to base64...")
        image_base64 = base64.b64encode(img_bytes).decode("utf-8")
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": instruction_text},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        }
        print("[DEBUG] Sending request to Gemini API...")
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print("[ERROR] API returned non-200 response:", response.text)
            return None
        result = response.json()
        print("[DEBUG] Full API response:", result)
        answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"[DEBUG] Answer from AI: {answer}")
        return answer
    except Exception as e:
        print("[EXCEPTION] Error while querying AI:", e)
        return None

# ---------------- GUI ACTION WITH DYNAMIC FONT ----------------
def capture_and_get_answer():
    try:
        selected_index = monitor_options.index(monitor_var.get())
        answer_mode = mode_var.get()
        img_bytes = capture_screen(selected_index)

        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.insert("end", "Processing screenshot...\n")
        output_box.configure(state="disabled")


        if answer_mode == "Direct Answer":
            instruction_text = (
                "You are shown a screenshot containing a single math question. "
                "Ignore everything else on the screen. "
                "Extract the math problem and return only the final answer. "
                "Do NOT describe the screen, do NOT explain, do NOT include any extra text."
            )
        else:
            instruction_text = (
                "You are shown a screenshot containing a single math question. "
                "Ignore everything else on the screen. "
                "Extract the math problem and provide step-by-step solution. "
                "Do NOT describe the screen, do NOT add extra commentary, return only the steps and final answer."
            )

        answer = get_ai_answer(img_bytes, instruction_text)

        max_font = 20
        min_font = 10
        if answer:
            num_lines = answer.count("\n") + 1
            box_height = output_box.winfo_height()
            font_size = max(min(int(box_height / (num_lines * 1.5)), max_font), min_font)
        else:
            font_size = max_font

        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.configure(font=("Segoe UI", font_size))
        if answer:
            output_box.insert("end", answer)
        else:
            output_box.insert("end", "[ERROR] No answer returned from AI.")
        output_box.configure(state="disabled")
    except Exception as e:
        print("[EXCEPTION]", str(e))
        messagebox.showerror("Error", str(e))

# ---------------- COPY BUTTON ----------------
def copy_to_clipboard():
    output_box.configure(state="normal")
    text = output_box.get("1.0", "end").strip()
    output_box.configure(state="disabled")
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        

# ---------------- CUSTOM TKINTER GUI ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("AI Screenshot Helper")
root.geometry("750x550")

# Header
header = ctk.CTkLabel(root, text="AI Screenshot Helper", font=ctk.CTkFont(size=24, weight="bold"))
header.pack(pady=(15,10))

# Monitor selection
monitors = screeninfo.get_monitors()
monitor_options = [f"Monitor {i+1} ({m.width}x{m.height})" for i, m in enumerate(monitors)]
monitor_var = ctk.StringVar(value=monitor_options[0])

monitor_frame = ctk.CTkFrame(root)
monitor_frame.pack(pady=5)
monitor_label = ctk.CTkLabel(monitor_frame, text="Select monitor:")
monitor_label.pack(side="left", padx=5)

monitor_menu = ctk.CTkOptionMenu(
    monitor_frame,
    values=monitor_options,
    variable=monitor_var
)
monitor_menu.pack(side="left", padx=5)

# Answer mode selection
mode_var = ctk.StringVar(value="Direct Answer")
mode_frame = ctk.CTkFrame(root)
mode_frame.pack(pady=5)
mode_label = ctk.CTkLabel(mode_frame, text="Select answer mode:")
mode_label.pack(side="left", padx=5)

mode_menu = ctk.CTkOptionMenu(
    mode_frame,
    values=["Direct Answer", "Step-by-Step"],
    variable=mode_var
)
mode_menu.pack(side="left", padx=5)

# Capture button
capture_btn = ctk.CTkButton(root, text="Capture & Get Answer", command=capture_and_get_answer, corner_radius=20, height=50, width=220)
capture_btn.pack(pady=10)

# Output box using modern CTkTextbox
output_box = ctk.CTkTextbox(root, corner_radius=10, border_width=1, font=("Segoe UI", 14), fg_color="#1f1f1f", text_color="#ffffff")
output_box.pack(padx=15, pady=10, fill="both", expand=True)
output_box.configure(state="disabled")

# Copy button
copy_btn = ctk.CTkButton(root, text="Copy Answer", command=copy_to_clipboard, corner_radius=15)
copy_btn.pack(pady=(0, 15))

print("[DEBUG] GUI ready. Starting mainloop...")
root.mainloop()
