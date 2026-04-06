"""
Twilight Times Tab - Single lat/lon + year input for yearly twilight calculations.

Generates a CSV with nautical twilight times for an entire year.
"""

import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional, Tuple

import customtkinter as ctk

from core.twilight_processor import generate_twilight_with_progress


class TwilightTimesTab(ctk.CTkFrame):
    """Tab for generating yearly twilight times."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._create_widgets()

    def _create_widgets(self):
        """Create and layout all widgets."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        row = 0

        # Coordinates frame
        coord_frame = ctk.CTkFrame(self)
        coord_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        coord_frame.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(coord_frame, text="Location", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, pady=(5, 10))

        # Latitude
        ctk.CTkLabel(coord_frame, text="Latitude:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.lat_entry = ctk.CTkEntry(coord_frame, width=150, placeholder_text="36.7456")
        self.lat_entry.insert(0, "36.7456")
        self.lat_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Longitude
        ctk.CTkLabel(coord_frame, text="Longitude:").grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self.lon_entry = ctk.CTkEntry(coord_frame, width=150, placeholder_text="-93.4712")
        self.lon_entry.insert(0, "-93.4712")
        self.lon_entry.grid(row=1, column=3, sticky="w", padx=(5, 10), pady=5)

        # Info label
        ctk.CTkLabel(
            coord_frame,
            text="Default: US Census Mean Center of Population (2020). "
                 "Streetlights ON at \u22126\u00b0 sun elevation (civil twilight boundary).",
            text_color="gray",
            wraplength=500,
            font=ctk.CTkFont(size=11)
        ).grid(row=2, column=0, columnspan=4, padx=10, pady=(0, 5))

        row += 1

        # Year frame
        year_frame = ctk.CTkFrame(self)
        year_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(year_frame, text="Year", font=ctk.CTkFont(weight="bold")).pack(pady=(5, 10))

        year_inner = ctk.CTkFrame(year_frame, fg_color="transparent")
        year_inner.pack(pady=(0, 10))

        self.year_entry = ctk.CTkEntry(year_inner, width=100)
        self.year_entry.insert(0, str(datetime.now().year))
        self.year_entry.pack(side="left", padx=10)

        # Quick year buttons
        current_year = datetime.now().year
        ctk.CTkButton(year_inner, text=str(current_year - 1), width=60,
                      command=lambda: self._set_year(current_year - 1)).pack(side="left", padx=2)
        ctk.CTkButton(year_inner, text=str(current_year), width=60,
                      command=lambda: self._set_year(current_year)).pack(side="left", padx=2)
        ctk.CTkButton(year_inner, text=str(current_year + 1), width=60,
                      command=lambda: self._set_year(current_year + 1)).pack(side="left", padx=2)

        row += 1

        # Output CSV
        ctk.CTkLabel(self, text="Output CSV:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.output_entry = ctk.CTkEntry(self, state="readonly", width=400)
        self.output_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.browse_output_btn = ctk.CTkButton(self, text="Browse...", width=100, command=self._browse_output)
        self.browse_output_btn.grid(row=row, column=2, padx=10, pady=5)

        row += 1

        # Progress section
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        self.timezone_label = ctk.CTkLabel(progress_frame, text="", text_color="gray")
        self.timezone_label.grid(row=0, column=1, sticky="e", padx=10, pady=(5, 0))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.progress_bar.set(0)

        row += 1

        # Run button
        self.run_btn = ctk.CTkButton(self, text="Generate Twilight Times", width=200, height=40,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      command=self._run_processing)
        self.run_btn.grid(row=row, column=0, columnspan=3, pady=15)

        row += 1

        # Results textbox
        ctk.CTkLabel(self, text="Results:").grid(row=row, column=0, sticky="nw", padx=10, pady=(5, 0))
        row += 1

        self.results_text = ctk.CTkTextbox(self, height=150, state="disabled")
        self.results_text.grid(row=row, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 10))
        self.grid_rowconfigure(row, weight=1)

    def _set_year(self, year):
        """Set the year entry to a specific value."""
        self.year_entry.delete(0, "end")
        self.year_entry.insert(0, str(year))

    def _browse_output(self):
        """Open file dialog for output CSV selection."""
        filepath = filedialog.asksaveasfilename(
            title="Select Output CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            self._update_entry(self.output_entry, filepath)

    def _update_entry(self, entry, text):
        """Update a readonly entry widget."""
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.configure(state="readonly")

    def _validate_inputs(self) -> Optional[Tuple[float, float, int]]:
        """Validate all inputs before processing. Returns (lat, lon, year) or None."""
        # Validate latitude
        try:
            lat = float(self.lat_entry.get())
            if not (-90 <= lat <= 90):
                messagebox.showwarning("Validation", "Latitude must be between -90 and 90")
                return None
        except ValueError:
            messagebox.showwarning("Validation", "Please enter a valid latitude")
            return None

        # Validate longitude
        try:
            lon = float(self.lon_entry.get())
            if not (-180 <= lon <= 180):
                messagebox.showwarning("Validation", "Longitude must be between -180 and 180")
                return None
        except ValueError:
            messagebox.showwarning("Validation", "Please enter a valid longitude")
            return None

        # Validate year
        try:
            year = int(self.year_entry.get())
            if year < 1900 or year > 2100:
                messagebox.showwarning("Validation", "Year must be between 1900 and 2100")
                return None
        except ValueError:
            messagebox.showwarning("Validation", "Please enter a valid year")
            return None

        # Validate output path
        if not self.output_entry.get():
            messagebox.showwarning("Validation", "Please specify an output CSV file")
            return None

        return lat, lon, year

    def _run_processing(self):
        """Start twilight calculation in a background thread."""
        validated = self._validate_inputs()
        if validated is None:
            return

        lat, lon, year = validated

        # Disable controls
        self.run_btn.configure(state="disabled")
        self.browse_output_btn.configure(state="disabled")

        self.progress_bar.set(0)
        self.progress_label.configure(text="Processing...")
        self.timezone_label.configure(text="")

        # Get parameters
        params = {
            'lat': lat,
            'lon': lon,
            'year': year,
            'output_path': self.output_entry.get()
        }

        # Start worker thread
        thread = threading.Thread(target=self._worker, args=(params,), daemon=True)
        thread.start()

    def _worker(self, params):
        """Background worker for twilight calculation."""
        try:
            def progress_callback(current, total, timezone):
                self.after(0, lambda: self._update_progress(current, total, timezone))

            stats = generate_twilight_with_progress(
                params['lat'],
                params['lon'],
                params['year'],
                params['output_path'],
                progress_callback
            )

            self.after(0, lambda: self._on_complete(stats, params))

        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _update_progress(self, current, total, timezone):
        """Update progress bar and label (called from main thread)."""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Processing: Day {current} / {total}")
        self.timezone_label.configure(text=f"Timezone: {timezone}")

    def _on_complete(self, stats, params):
        """Handle processing completion."""
        self.progress_bar.set(1)
        self.progress_label.configure(text="Complete!")

        # Build summary
        summary = f"""Twilight Times Generated!
{'='*50}

Location: ({params['lat']}, {params['lon']})
Year: {params['year']}
Timezone: {stats['timezone']}

Total days:   {stats['total_days']}
Valid days:   {stats['valid_days']}"""

        if stats['polar_days'] > 0:
            summary += f"""
Polar days:   {stats['polar_days']} (no nautical twilight)"""

        summary += f"""

Output saved to: {params['output_path']}

The output CSV contains:
- date: The date (YYYY-MM-DD)
- streetlights_off_time: Time when streetlights turn OFF (sun at -6 degrees, morning)
- sunrise: Time of sunrise (sun crosses 0 degrees, rising)
- sunset: Time of sunset (sun crosses 0 degrees, setting)
- streetlights_on_time: Time when streetlights turn ON (sun at -6 degrees, evening)
- streetlights_on_hours_morning: Hours from midnight to streetlights OFF
- streetlights_on_hours_evening: Hours from streetlights ON to midnight
- streetlights_on_hours_total: Total darkness hours for the date
"""

        self._set_result(summary)

        # Re-enable controls
        self._enable_controls()

        messagebox.showinfo("Complete", f"Twilight times generated!\n\nOutput saved to:\n{params['output_path']}")

    def _on_error(self, error_msg):
        """Handle processing error."""
        self.progress_label.configure(text="Error!")
        self._set_result(f"Error: {error_msg}")
        self._enable_controls()
        messagebox.showerror("Error", f"Processing failed:\n{error_msg}")

    def _enable_controls(self):
        """Re-enable all controls after processing."""
        self.run_btn.configure(state="normal")
        self.browse_output_btn.configure(state="normal")

    def _set_result(self, text):
        """Set text in the results textbox."""
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", text)
        self.results_text.configure(state="disabled")
