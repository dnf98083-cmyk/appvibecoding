"""
Handwritten Digit Recognition
-------------------------------
GUI    : tkinter (Python built-in)
Model  : CNN trained on MNIST dataset via TensorFlow/Keras
Image  : PIL (Pillow) for preprocessing
Usage  : python digit_recognition.py
"""

import os
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL_PATH  = "mnist_cnn.keras"   # saved model file
CANVAS_SIZE = 280                 # drawing canvas (pixels)
MNIST_SIZE  = 28                  # MNIST input resolution
BRUSH_SIZE  = 14                  # drawing brush radius

# ── Model: build, train, and save ─────────────────────────────────────────────

def build_model():
    """Create a small CNN suited for 28x28 grayscale digit images."""
    model = keras.Sequential([
        # First convolution block
        layers.Conv2D(32, (3, 3), activation="relu", input_shape=(28, 28, 1)),
        layers.MaxPooling2D((2, 2)),

        # Second convolution block
        layers.Conv2D(64, (3, 3), activation="relu"),
        layers.MaxPooling2D((2, 2)),

        # Fully connected head
        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.25),           # regularisation to reduce overfitting
        layers.Dense(10, activation="softmax"),  # 10 output classes (0-9)
    ], name="mnist_cnn")
    return model


def train_model():
    """Download MNIST, train the CNN for 5 epochs, and save the weights."""
    print("[INFO] Downloading MNIST dataset…")
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

    # Normalize pixels to [0, 1] and add channel dimension
    x_train = x_train.astype("float32") / 255.0
    x_test  = x_test.astype("float32")  / 255.0
    x_train = x_train[..., np.newaxis]   # shape: (60000, 28, 28, 1)
    x_test  = x_test[..., np.newaxis]    # shape: (10000, 28, 28, 1)

    model = build_model()
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("[INFO] Training CNN on 60,000 MNIST samples…")
    model.fit(
        x_train, y_train,
        epochs=5,
        batch_size=128,
        validation_data=(x_test, y_test),
        verbose=1,
    )

    # Report test accuracy
    _, acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"[INFO] Test accuracy: {acc * 100:.2f}%")

    model.save(MODEL_PATH)
    print(f"[INFO] Model saved → {MODEL_PATH}")
    return model


def load_or_train():
    """Return a trained model, loading from disk if available."""
    if os.path.exists(MODEL_PATH):
        print(f"[INFO] Loading model from {MODEL_PATH}")
        return keras.models.load_model(MODEL_PATH)
    return train_model()


# ── Image preprocessing ────────────────────────────────────────────────────────

def preprocess_canvas(canvas_widget):
    """
    Capture what's drawn on the tkinter canvas,
    resize to 28×28, and return a numpy array ready for the model.
    """
    # Export canvas to a PIL image via PostScript
    ps = canvas_widget.postscript(colormode="gray")
    from io import BytesIO
    import subprocess, tempfile, sys

    # tkinter PostScript → PIL (use ghostscript if available, else fallback)
    try:
        img = Image.open(BytesIO(ps.encode("utf-8")))
    except Exception:
        # Fallback: render canvas to a temporary PNG via screencapture is not
        # portable, so we rebuild the image from the canvas pixel buffer.
        img = canvas_to_pil(canvas_widget)

    img = img.convert("L")                          # grayscale
    img = ImageOps.invert(img)                      # invert: white digit on black
    img = img.resize((MNIST_SIZE, MNIST_SIZE),      # resize to 28×28
                     Image.LANCZOS)
    arr = np.array(img, dtype="float32") / 255.0    # normalize to [0, 1]
    arr = arr[np.newaxis, ..., np.newaxis]           # shape: (1, 28, 28, 1)
    return arr


def canvas_to_pil(canvas_widget):
    """
    Alternative path: rebuild a PIL image from the internal pixel buffer
    stored in our DrawingApp class.
    """
    # This function is called by the App instance; see DrawingApp.get_pil_image()
    raise RuntimeError("Use DrawingApp.get_pil_image() instead.")


# ── GUI ────────────────────────────────────────────────────────────────────────

class DrawingApp:
    """Main application window with a drawing canvas and recognition panel."""

    def __init__(self, root, model):
        self.root  = root
        self.model = model
        root.title("Handwritten Digit Recognition")
        root.resizable(False, False)
        root.configure(bg="#0f172a")

        # Internal PIL image — we draw here in parallel with the canvas
        # so we can feed it directly to the model without PostScript export.
        self.pil_image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), color=0)
        from PIL import ImageDraw as ID
        self.pil_draw  = ID.Draw(self.pil_image)

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Left panel: drawing canvas ────────────────────────────────────────
        left = tk.Frame(self.root, bg="#1e293b", padx=20, pady=20)
        left.pack(side=tk.LEFT)

        tk.Label(left, text="✍️  Draw a digit (0–9)",
                 bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 11)).pack(pady=(0, 10))

        self.canvas = tk.Canvas(
            left,
            width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg="black", cursor="crosshair",
            highlightthickness=2, highlightbackground="#334155",
        )
        self.canvas.pack()

        # Bind mouse events for drawing
        self.canvas.bind("<Button-1>",        self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self._last_x = self._last_y = None

        # Buttons
        btn_frame = tk.Frame(left, bg="#1e293b")
        btn_frame.pack(pady=14, fill=tk.X)

        self.btn_recognize = tk.Button(
            btn_frame, text="🔍  Recognize",
            command=self._recognize,
            bg="#818cf8", fg="white", activebackground="#6366f1",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
        )
        self.btn_recognize.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        self.btn_clear = tk.Button(
            btn_frame, text="🗑  Clear",
            command=self._clear,
            bg="#334155", fg="#94a3b8", activebackground="#475569",
            font=("Segoe UI", 11),
            relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
        )
        self.btn_clear.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # ── Right panel: results ──────────────────────────────────────────────
        right = tk.Frame(self.root, bg="#0f172a", padx=24, pady=20)
        right.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(right, text="Prediction",
                 bg="#0f172a", fg="#64748b",
                 font=("Segoe UI", 10)).pack()

        # Large digit display
        self.lbl_digit = tk.Label(
            right, text="?",
            bg="#0f172a", fg="#818cf8",
            font=("Segoe UI", 72, "bold"),
        )
        self.lbl_digit.pack(pady=(4, 0))

        # Confidence label
        self.lbl_conf = tk.Label(
            right, text="Draw and click Recognize",
            bg="#0f172a", fg="#64748b",
            font=("Segoe UI", 10),
        )
        self.lbl_conf.pack()

        # Separator
        tk.Frame(right, bg="#1e293b", height=1).pack(fill=tk.X, pady=16)

        # Probability bars for each digit 0–9
        tk.Label(right, text="All probabilities",
                 bg="#0f172a", fg="#64748b",
                 font=("Segoe UI", 9)).pack()

        bar_frame = tk.Frame(right, bg="#0f172a")
        bar_frame.pack(pady=8)

        self.bars   = []   # Canvas widgets (bar charts)
        self.bar_pct = []  # Label widgets (percentage text)
        BAR_W, BAR_MAX_H = 22, 80

        for i in range(10):
            col = tk.Frame(bar_frame, bg="#0f172a")
            col.pack(side=tk.LEFT, padx=3)

            # Percentage text (above bar)
            pct_lbl = tk.Label(col, text="0%", bg="#0f172a", fg="#475569",
                               font=("Segoe UI", 7))
            pct_lbl.pack()

            # Bar canvas
            bar_cv = tk.Canvas(col, width=BAR_W, height=BAR_MAX_H,
                               bg="#1e293b", highlightthickness=0)
            bar_cv.pack()

            # Digit label (below bar)
            tk.Label(col, text=str(i), bg="#0f172a", fg="#64748b",
                     font=("Segoe UI", 9, "bold")).pack()

            self.bars.append(bar_cv)
            self.bar_pct.append(pct_lbl)

        self.BAR_W      = BAR_W
        self.BAR_MAX_H  = BAR_MAX_H

        # Initialize bars to zero
        self._update_bars([0.0] * 10, -1)

    # ── Drawing callbacks ──────────────────────────────────────────────────────

    def _on_press(self, event):
        """Record starting point of a stroke."""
        self._last_x, self._last_y = event.x, event.y

    def _on_drag(self, event):
        """Draw a smooth line from the last recorded point to the current one."""
        if self._last_x is None:
            return
        x, y = event.x, event.y
        r = BRUSH_SIZE

        # Draw on tkinter canvas (visible to user)
        self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill="white", outline="white",
        )
        self.canvas.create_line(
            self._last_x, self._last_y, x, y,
            fill="white", width=r * 2, capstyle=tk.ROUND, joinstyle=tk.ROUND,
        )

        # Mirror stroke on PIL image (used for model inference)
        self.pil_draw.ellipse([x - r, y - r, x + r, y + r], fill=255)
        self.pil_draw.line(
            [self._last_x, self._last_y, x, y],
            fill=255, width=r * 2,
        )

        self._last_x, self._last_y = x, y

    def _on_release(self, event):
        self._last_x = self._last_y = None

    # ── Recognition ───────────────────────────────────────────────────────────

    def _recognize(self):
        """Preprocess the drawn image and run model inference."""
        # Resize PIL image from 280×280 → 28×28 and normalize
        resized = self.pil_image.resize((MNIST_SIZE, MNIST_SIZE), Image.LANCZOS)
        arr = np.array(resized, dtype="float32") / 255.0  # [0, 1]
        arr = arr[np.newaxis, ..., np.newaxis]             # (1, 28, 28, 1)

        # Run prediction
        probs     = self.model.predict(arr, verbose=0)[0]  # shape: (10,)
        top_digit = int(np.argmax(probs))
        top_prob  = float(probs[top_digit])

        # Update UI
        self.lbl_digit.config(text=str(top_digit))
        self.lbl_conf.config(
            text=f"Confidence: {top_prob * 100:.1f}%",
            fg="#4ade80" if top_prob > 0.7 else "#facc15",
        )
        self._update_bars(probs.tolist(), top_digit)

    # ── Probability bars ───────────────────────────────────────────────────────

    def _update_bars(self, probs, top_idx):
        """Redraw the 10 probability bar charts."""
        for i, (bar_cv, pct_lbl) in enumerate(zip(self.bars, self.bar_pct)):
            bar_cv.delete("all")
            h    = int(probs[i] * self.BAR_MAX_H)
            y0   = self.BAR_MAX_H - h
            color = "#818cf8" if i == top_idx else "#334155"

            if h > 0:
                bar_cv.create_rectangle(
                    0, y0, self.BAR_W, self.BAR_MAX_H,
                    fill=color, outline="",
                )

            pct_lbl.config(
                text=f"{probs[i]*100:.0f}%",
                fg="#c084fc" if i == top_idx else "#475569",
            )

    # ── Clear ──────────────────────────────────────────────────────────────────

    def _clear(self):
        """Reset canvas, PIL image, and result panel."""
        self.canvas.delete("all")
        self.pil_image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), color=0)
        from PIL import ImageDraw as ID
        self.pil_draw  = ID.Draw(self.pil_image)
        self.lbl_digit.config(text="?")
        self.lbl_conf.config(text="Draw and click Recognize", fg="#64748b")
        self._update_bars([0.0] * 10, -1)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[INFO] Loading model (this may take a moment on first run)…")
    model = load_or_train()
    model.summary()

    root = tk.Tk()
    app  = DrawingApp(root, model)
    root.mainloop()
