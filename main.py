import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import webbrowser

import cv2
import qrcode
from PIL import Image, ImageTk


class QRApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("QRMaster (Python)")
        self.geometry("800x600")

        self._qr_image: Optional[Image.Image] = None
        self._qr_photo: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    # UI ------------------------------------------------------------------
    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Generate tab
        self.generate_frame = ttk.Frame(notebook)
        notebook.add(self.generate_frame, text="Generate")
        self._build_generate_tab(self.generate_frame)

        # Scan tab
        self.scan_frame = ttk.Frame(notebook)
        notebook.add(self.scan_frame, text="Scan")
        self._build_scan_tab(self.scan_frame)

    def _build_generate_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        input_label = ttk.Label(parent, text="Text to encode:")
        input_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.input_text = tk.Text(parent, height=5)
        self.input_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        generate_btn = ttk.Button(
            button_frame,
            text="Generate QR",
            command=self.on_generate_clicked,
        )
        generate_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        save_btn = ttk.Button(
            button_frame,
            text="Save QR Image",
            command=self.on_save_clicked,
        )
        save_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.preview_label = ttk.Label(parent, text="QR preview will appear here")
        self.preview_label.grid(row=3, column=0, sticky="n", padx=10, pady=10)

    def _build_scan_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)

        info = ttk.Label(
            parent,
            text=(
                "Click 'Start Camera Scan' to open your webcam and scan a QR code.\n"
                "The first detected QR code content will be displayed below."
            ),
            justify="center",
        )
        info.grid(row=0, column=0, padx=10, pady=10)

        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=1, column=0, padx=10, pady=10)

        scan_btn = ttk.Button(
            buttons_frame,
            text="Start Camera Scan",
            command=self.on_scan_clicked,
        )
        scan_btn.grid(row=0, column=0, padx=(0, 5))

        load_img_btn = ttk.Button(
            buttons_frame,
            text="Scan from Image",
            command=self.on_scan_image_clicked,
        )
        load_img_btn.grid(row=0, column=1, padx=(5, 0))

        result_label = ttk.Label(parent, text="Scanned content:")
        result_label.grid(row=2, column=0, sticky="w", padx=10, pady=(20, 0))

        self.scan_result = tk.Text(parent, height=6, state="disabled")
        self.scan_result.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        parent.rowconfigure(3, weight=1)

    # Generate tab handlers -----------------------------------------------
    def on_generate_clicked(self) -> None:
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No text", "Please enter some text to encode.")
            return

        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        except Exception as exc:  # pragma: no cover - very rare
            messagebox.showerror("Error", f"Failed to generate QR code:\n{exc}")
            return

        self._qr_image = img
        self._update_qr_preview()

    def _update_qr_preview(self) -> None:
        if self._qr_image is None:
            self.preview_label.configure(text="QR preview will appear here", image="")
            return

        # Resize for preview if too large
        max_size = 300
        img = self._qr_image
        if img.width > max_size or img.height > max_size:
            img = img.copy()
            img.thumbnail((max_size, max_size))

        self._qr_photo = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self._qr_photo, text="")

    def on_save_clicked(self) -> None:
        if self._qr_image is None:
            messagebox.showinfo("No QR image", "Generate a QR code before saving.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All files", "*.*")],
            title="Save QR Image",
        )
        if not file_path:
            return

        try:
            self._qr_image.save(file_path, format="PNG")
            messagebox.showinfo("Saved", f"QR image saved to:\n{file_path}")
        except Exception as exc:  # pragma: no cover - filesystem errors
            messagebox.showerror("Error", f"Failed to save QR image:\n{exc}")

    # Scan tab handlers ---------------------------------------------------
    def on_scan_clicked(self) -> None:
        # Run camera scan in background so UI stays responsive
        thread = threading.Thread(target=self._run_camera_scan, daemon=True)
        thread.start()

    def on_scan_image_clicked(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select QR Image",
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        img = cv2.imread(file_path)
        if img is None:
            messagebox.showerror("Error", "Could not read the selected image file.")
            return

        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(img)

        if points is not None and data:
            # Reuse same UI handling as camera scan
            self._set_scan_result_from_thread(data)
        else:
            messagebox.showinfo("No QR found", "No QR code detected in this image.")

    def _run_camera_scan(self) -> None:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._show_message_from_thread(
                "Camera error",
                "Could not open the default camera (index 0).",
                error=True,
            )
            return

        detector = cv2.QRCodeDetector()
        decoded_text: Optional[str] = None

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Detect and decode
                data, points, _ = detector.detectAndDecode(frame)
                if points is not None and data:
                    decoded_text = data
                    # Draw polygon around QR
                    pts = points[0].astype(int)
                    for i in range(len(pts)):
                        cv2.line(
                            frame,
                            tuple(pts[i]),
                            tuple(pts[(i + 1) % len(pts)]),
                            (0, 255, 0),
                            2,
                        )
                    cv2.putText(
                        frame,
                        "QR detected",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                    )

                cv2.imshow("QR Scan (press Q to quit)", frame)

                # Exit if QR found or user presses Q
                if decoded_text is not None:
                    break
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        if decoded_text:
            self._set_scan_result_from_thread(decoded_text)
        else:
            self._show_message_from_thread(
                "No QR found",
                "No QR code was detected before closing the camera window.",
                error=False,
            )

    # Thread-safe UI helpers ----------------------------------------------
    def _show_message_from_thread(self, title: str, message: str, error: bool) -> None:
        def fn() -> None:
            if error:
                messagebox.showerror(title, message)
            else:
                messagebox.showinfo(title, message)

        self.after(0, fn)

    def _set_scan_result_from_thread(self, text: str) -> None:
        def fn() -> None:
            self.scan_result.configure(state="normal")
            self.scan_result.delete("1.0", tk.END)
            self.scan_result.insert(tk.END, text)
            self.scan_result.configure(state="disabled")
            messagebox.showinfo("QR content", text)

            if self._looks_like_url(text):
                url = text
                if not url.lower().startswith(("http://", "https://")):
                    url = "https://" + url
                try:
                    webbrowser.open(url)
                except Exception:
                    # If opening fails, we silently ignore; user still sees the text.
                    pass

        self.after(0, fn)

    def _looks_like_url(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        return stripped.lower().startswith(("http://", "https://", "www."))


def main() -> None:
    app = QRApp()
    app.mainloop()


if __name__ == "__main__":
    main()

