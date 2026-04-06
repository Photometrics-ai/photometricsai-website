"""
Phase Calculator Tab - CSV upload with column auto-detection.

Processes CSV files to calculate sun elevation and twilight phase for each record.
"""

import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.phase_processor import detect_csv_columns, auto_detect_columns, process_csv_with_progress


class PhaseCalculatorTab(ctk.CTkFrame):
    """Tab for processing CSV files with phase calculations."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.input_path = None
        self.columns = []

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout all widgets."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        row = 0

        # Input CSV
        ctk.CTkLabel(self, text="Input CSV:").grid(row=row, column=0, sticky="w", padx=10, pady=(10, 5))
        self.input_entry = ctk.CTkEntry(self, state="readonly", width=400)
        self.input_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=(10, 5))
        self.browse_input_btn = ctk.CTkButton(self, text="Browse...", width=100, command=self._browse_input)
        self.browse_input_btn.grid(row=row, column=2, padx=10, pady=(10, 5))

        row += 1

        # Output GPKG
        ctk.CTkLabel(self, text="Output GPKG:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.output_entry = ctk.CTkEntry(self, state="readonly", width=400)
        self.output_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.browse_output_btn = ctk.CTkButton(self, text="Browse...", width=100, command=self._browse_output)
        self.browse_output_btn.grid(row=row, column=2, padx=10, pady=5)

        row += 1

        # Column mapping frame
        col_frame = ctk.CTkFrame(self)
        col_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        col_frame.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(col_frame, text="Column Mapping", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, pady=(5, 10))

        # Latitude dropdown
        ctk.CTkLabel(col_frame, text="Latitude:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.lat_dropdown = ctk.CTkComboBox(col_frame, values=[""], state="readonly", width=200)
        self.lat_dropdown.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Longitude dropdown
        ctk.CTkLabel(col_frame, text="Longitude:").grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self.lon_dropdown = ctk.CTkComboBox(col_frame, values=[""], state="readonly", width=200)
        self.lon_dropdown.grid(row=1, column=3, sticky="ew", padx=(5, 10), pady=5)

        # Date dropdown
        ctk.CTkLabel(col_frame, text="Date:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.date_dropdown = ctk.CTkComboBox(col_frame, values=[""], state="readonly", width=200)
        self.date_dropdown.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Time dropdown
        ctk.CTkLabel(col_frame, text="Time:").grid(row=2, column=2, sticky="w", padx=10, pady=5)
        self.time_dropdown = ctk.CTkComboBox(col_frame, values=[""], state="readonly", width=200)
        self.time_dropdown.grid(row=2, column=3, sticky="ew", padx=(5, 10), pady=5)

        row += 1

        # Chunk size
        chunk_frame = ctk.CTkFrame(self, fg_color="transparent")
        chunk_frame.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(chunk_frame, text="Chunk Size:").pack(side="left", padx=(0, 10))
        self.chunk_entry = ctk.CTkEntry(chunk_frame, width=100)
        self.chunk_entry.insert(0, "50000")
        self.chunk_entry.pack(side="left")
        ctk.CTkLabel(chunk_frame, text="(rows per batch)", text_color="gray").pack(side="left", padx=10)

        row += 1

        # Progress section
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.progress_bar.set(0)

        row += 1

        # Run button
        self.run_btn = ctk.CTkButton(self, text="Run Processing", width=200, height=40,
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

    def _browse_input(self):
        """Open file dialog for input CSV selection."""
        filepath = filedialog.askopenfilename(
            title="Select Input CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            self.input_path = filepath
            self._update_entry(self.input_entry, filepath)
            self._load_columns(filepath)

            # Auto-suggest output path
            input_p = Path(filepath)
            output_path = input_p.parent / f"{input_p.stem}_phases.gpkg"
            self._update_entry(self.output_entry, str(output_path))

    def _browse_output(self):
        """Open file dialog for output GPKG selection."""
        filepath = filedialog.asksaveasfilename(
            title="Select Output GPKG",
            defaultextension=".gpkg",
            filetypes=[("GeoPackage files", "*.gpkg"), ("All files", "*.*")]
        )
        if filepath:
            self._update_entry(self.output_entry, filepath)

    def _update_entry(self, entry, text):
        """Update a readonly entry widget."""
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.configure(state="readonly")

    def _load_columns(self, filepath):
        """Load CSV columns and populate dropdowns."""
        try:
            self.columns = detect_csv_columns(filepath)

            # Update all dropdowns
            for dropdown in [self.lat_dropdown, self.lon_dropdown,
                           self.date_dropdown, self.time_dropdown]:
                dropdown.configure(values=self.columns)

            # Auto-detect column mappings
            detected = auto_detect_columns(self.columns)

            if detected['lat']:
                self.lat_dropdown.set(detected['lat'])
            elif self.columns:
                self.lat_dropdown.set(self.columns[0])

            if detected['lon']:
                self.lon_dropdown.set(detected['lon'])
            elif self.columns:
                self.lon_dropdown.set(self.columns[0])

            if detected['date']:
                self.date_dropdown.set(detected['date'])
            elif self.columns:
                self.date_dropdown.set(self.columns[0])

            if detected['time']:
                self.time_dropdown.set(detected['time'])
            elif self.columns:
                self.time_dropdown.set(self.columns[0])

            self._set_result(f"Loaded {len(self.columns)} columns from CSV")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {e}")

    def _validate_inputs(self) -> bool:
        """Validate all inputs before processing."""
        if not self.input_path:
            messagebox.showwarning("Validation", "Please select an input CSV file")
            return False

        if not self.output_entry.get():
            messagebox.showwarning("Validation", "Please specify an output CSV file")
            return False

        if not all([self.lat_dropdown.get(), self.lon_dropdown.get(),
                   self.date_dropdown.get(), self.time_dropdown.get()]):
            messagebox.showwarning("Validation", "Please select all column mappings")
            return False

        try:
            chunk_size = int(self.chunk_entry.get())
            if chunk_size < 1:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Validation", "Chunk size must be a positive integer")
            return False

        return True

    def _run_processing(self):
        """Start CSV processing in a background thread."""
        if not self._validate_inputs():
            return

        # Disable controls
        self.run_btn.configure(state="disabled")
        self.browse_input_btn.configure(state="disabled")
        self.browse_output_btn.configure(state="disabled")

        self.progress_bar.set(0)
        self.progress_label.configure(text="Processing...")

        # Get parameters
        params = {
            'input_path': self.input_path,
            'output_path': self.output_entry.get(),
            'lat_col': self.lat_dropdown.get(),
            'lon_col': self.lon_dropdown.get(),
            'date_col': self.date_dropdown.get(),
            'time_col': self.time_dropdown.get(),
            'chunk_size': int(self.chunk_entry.get())
        }

        # Start worker thread
        thread = threading.Thread(target=self._worker, args=(params,), daemon=True)
        thread.start()

    def _worker(self, params):
        """Background worker for CSV processing."""
        try:
            def progress_callback(current, total, stats):
                self.after(0, lambda: self._update_progress(current, total, stats))

            stats = process_csv_with_progress(
                params['input_path'],
                params['output_path'],
                params['lat_col'],
                params['lon_col'],
                params['date_col'],
                params['time_col'],
                params['chunk_size'],
                progress_callback
            )

            self.after(0, lambda: self._on_complete(stats, params['output_path']))

        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _update_progress(self, current, total, stats):
        """Update progress bar and label (called from main thread)."""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_label.configure(
            text=f"Processing: {current:,} / {total:,} ({progress*100:.1f}%) | "
                 f"Streetlights ON: {stats['streetlights_on']:,}"
        )

    def _on_complete(self, stats, output_path):
        """Handle processing completion."""
        self.progress_bar.set(1)
        self.progress_label.configure(text="Complete!")

        # Build summary
        total = stats['total']
        processed = stats['processed']
        lights_on = stats['streetlights_on']

        summary = f"""Processing Complete!
{'='*50}

Total records:        {total:,}
Successfully processed: {processed:,} ({100*processed/total:.1f}%)
Errors:               {stats['errors']:,}

--- Twilight Phase Distribution ---
Day:                  {stats['day']:,} ({100*stats['day']/processed:.1f}%)
Civil Twilight:       {stats['civil']:,} ({100*stats['civil']/processed:.1f}%)
Nautical Twilight:    {stats['nautical']:,} ({100*stats['nautical']/processed:.1f}%)
Astronomical Twilight: {stats['astronomical']:,} ({100*stats['astronomical']/processed:.1f}%)
Night:                {stats['night']:,} ({100*stats['night']/processed:.1f}%)

--- Streetlight Status ---
Streetlights ON:      {lights_on:,} ({100*lights_on/processed:.1f}%)
Streetlights OFF:     {processed-lights_on:,} ({100*(processed-lights_on)/processed:.1f}%)

Output saved to: {output_path}
"""
        self._set_result(summary)

        # Re-enable controls
        self._enable_controls()

        messagebox.showinfo("Complete", f"Processing complete!\n\nOutput saved to:\n{output_path}")

    def _on_error(self, error_msg):
        """Handle processing error."""
        self.progress_label.configure(text="Error!")
        self._set_result(f"Error: {error_msg}")
        self._enable_controls()
        messagebox.showerror("Error", f"Processing failed:\n{error_msg}")

    def _enable_controls(self):
        """Re-enable all controls after processing."""
        self.run_btn.configure(state="normal")
        self.browse_input_btn.configure(state="normal")
        self.browse_output_btn.configure(state="normal")

    def _set_result(self, text):
        """Set text in the results textbox."""
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", text)
        self.results_text.configure(state="disabled")
