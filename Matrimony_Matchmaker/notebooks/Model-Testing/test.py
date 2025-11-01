import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import json

API_BASE_URL = "http://127.0.0.1:5000/user"
PREDICT_ENDPOINT = f"{API_BASE_URL}/predict_match"
FETCH_ENDPOINT = f"{API_BASE_URL}/get_user"


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True).start()
    return wrapper


class MatchPredictorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Match Predictor")
        self.geometry("980x620")
        self.minsize(880, 540)
        self.configure(bg="#f4f6f8")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("Header.TLabel", font=("Inter", 18, "bold"), foreground="#263238", background="#f4f6f8")
        style.configure("SubHeader.TLabel", font=("Inter", 11, "bold"), foreground="#455A64", background="#ffffff")
        style.configure("Field.TLabel", font=("Inter", 10), background="#ffffff")
        style.configure("TButton", font=("Inter", 10, "bold"))
        style.map("TButton", background=[("active", "#2e7d32")], foreground=[("active", "white")])

        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self, padding=(20, 14))
        header.pack(fill="x")
        ttk.Label(header, text="Match Predictor", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="Enter two identifiers (id / username / email)",
                  foreground="#607D8B", background="#f4f6f8").pack(side="right")

        body = ttk.Frame(self, padding=(18, 10))
        body.pack(fill="both", expand=True)

        # === Left: Two User Panels side-by-side ===
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        users_frame = ttk.Frame(left, style="TFrame")
        users_frame.pack(fill="x", pady=(0, 12))

        # --- User 1 Card ---
        u1_frame = ttk.Frame(users_frame, style="Card.TFrame", padding=12)
        u1_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(u1_frame, text="User 1 identifier", style="SubHeader.TLabel").pack(anchor="w")
        self.user1_var = tk.StringVar()
        ttk.Entry(u1_frame, textvariable=self.user1_var, width=30).pack(anchor="w", pady=(8, 4))
        ttk.Button(u1_frame, text="Fetch User 1", command=self.fetch_user1).pack(anchor="w")
        self.user1_card = ProfileCard(u1_frame)
        self.user1_card.frame.pack(fill="both", expand=True, pady=(10, 0))

        # --- User 2 Card ---
        u2_frame = ttk.Frame(users_frame, style="Card.TFrame", padding=12)
        u2_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ttk.Label(u2_frame, text="User 2 identifier", style="SubHeader.TLabel").pack(anchor="w")
        self.user2_var = tk.StringVar()
        ttk.Entry(u2_frame, textvariable=self.user2_var, width=30).pack(anchor="w", pady=(8, 4))
        ttk.Button(u2_frame, text="Fetch User 2", command=self.fetch_user2).pack(anchor="w")
        self.user2_card = ProfileCard(u2_frame)
        self.user2_card.frame.pack(fill="both", expand=True, pady=(10, 0))

        # Control + Status
        ctrl_frame = ttk.Frame(left, padding=(6, 8))
        ctrl_frame.pack(fill="x", pady=(10, 0))
        self.predict_btn = ttk.Button(ctrl_frame, text="Predict Compatibility", command=self.predict_match)
        self.predict_btn.pack(fill="x")
        self.status_label = ttk.Label(ctrl_frame, text="", foreground="#455A64", background="#f4f6f8")
        self.status_label.pack(anchor="w", pady=(8, 0))

        # === Right: Prediction Result Panel ===
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        result_frame = ttk.Frame(right, style="Card.TFrame", padding=16)
        result_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(result_frame, text="Prediction Result", style="SubHeader.TLabel").pack(anchor="w")
        self.result_value = ttk.Label(result_frame, text="—", font=("Inter", 16, "bold"),
                                      foreground="#1b5e20", background="white")
        self.result_value.pack(anchor="w", pady=(8, 2))

        details_frame = ttk.Frame(right, style="Card.TFrame", padding=12)
        details_frame.pack(fill="both", expand=True)
        ttk.Label(details_frame, text="Combined Features (model input)", style="SubHeader.TLabel").pack(anchor="w")
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill="both", expand=True, pady=(8, 0))
        self.text = tk.Text(text_frame, height=18, wrap="word", padx=8, pady=8)
        self.text.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        vsb.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=vsb.set, state="disabled",
                            background="#ffffff", relief="flat", font=("Consolas", 10))

    # === Networking Functions ===
    @threaded
    def fetch_user1(self):
        identifier = self.user1_var.get().strip()
        if not identifier:
            messagebox.showwarning("Input required", "Enter an identifier for User 1")
            return
        self._set_status("Fetching user 1...")
        try:
            resp = requests.get(FETCH_ENDPOINT, params={"input": identifier}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                self.user1_card.update_card(title=data.get("name", identifier), features=data)
                self._set_status("User 1 fetched")
            else:
                msg = resp.json().get("error", resp.text)
                messagebox.showerror("Error fetching user 1", str(msg))
                self._set_status("Error fetching user 1")
        except Exception as e:
            messagebox.showerror("Network error", str(e))
            self._set_status("Network error")

    @threaded
    def fetch_user2(self):
        identifier = self.user2_var.get().strip()
        if not identifier:
            messagebox.showwarning("Input required", "Enter an identifier for User 2")
            return
        self._set_status("Fetching user 2...")
        try:
            resp = requests.get(FETCH_ENDPOINT, params={"input": identifier}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                self.user2_card.update_card(title=data.get("name", identifier), features=data)
                self._set_status("User 2 fetched")
            else:
                msg = resp.json().get("error", resp.text)
                messagebox.showerror("Error fetching user 2", str(msg))
                self._set_status("Error fetching user 2")
        except Exception as e:
            messagebox.showerror("Network error", str(e))
            self._set_status("Network error")

    @threaded
    def predict_match(self):
        user1 = self.user1_var.get().strip()
        user2 = self.user2_var.get().strip()
        if not user1 or not user2:
            messagebox.showwarning("Missing input", "Enter both user identifiers before predicting.")
            return
        self.predict_btn.state(["disabled"])
        self._set_status("Calculating prediction...")
        try:
            resp = requests.get(PREDICT_ENDPOINT, params={"user1": user1, "user2": user2}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                predicted_class = data.get("predicted_class", "—")
                features = data.get("features", {})
                self.result_value.config(text=predicted_class)
                self._show_features(features)
                self.user1_card.update_title(data.get("user1", user1))
                self.user2_card.update_title(data.get("user2", user2))
                self._set_status("Prediction ready")
            else:
                msg = resp.json().get("error", resp.text)
                messagebox.showerror("Error during prediction", str(msg))
                self._set_status("Prediction error")
        except Exception as e:
            messagebox.showerror("Network error", str(e))
            self._set_status("Network error")
        finally:
            self.predict_btn.state(["!disabled"])

    # === UI Helpers ===
    def _show_features(self, features_dict):
        pretty = json.dumps(features_dict, indent=2, ensure_ascii=False)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", pretty)
        self.text.configure(state="disabled")

    def _set_status(self, text):
        self.status_label.config(text=text)


class ProfileCard:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, style="Card.TFrame", padding=(8, 8))
        self.title_lbl = ttk.Label(self.frame, text="—", style="SubHeader.TLabel")
        self.title_lbl.pack(anchor="w")
        container = ttk.Frame(self.frame)
        container.pack(fill="both", expand=True, pady=(6, 0))
        self.canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0,
                                background="white", height=200)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas, style="Card.TFrame")
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.inner_id, width=event.width)

    def update_card(self, title="—", features=None):
        self.update_title(title)
        for c in self.inner.winfo_children():
            c.destroy()
        if not features:
            ttk.Label(self.inner, text="No features loaded", style="Field.TLabel").pack(anchor="w")
            return
        for k, v in features.items():
            row = ttk.Frame(self.inner)
            row.pack(fill="x", anchor="w", pady=1, padx=(2, 2))
            ttk.Label(row, text=f"{k}:", width=16, anchor="w", style="Field.TLabel").pack(side="left")
            ttk.Label(row, text=str(v), anchor="w", style="Field.TLabel").pack(side="left")

    def update_title(self, title):
        self.title_lbl.config(text=title)


if __name__ == "__main__":
    app = MatchPredictorApp()
    app.mainloop()
