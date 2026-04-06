"""
Sun Phase Tools - Main Application Window

CustomTkinter desktop application with tabbed interface.
"""

import customtkinter as ctk

from gui.tabs.phase_tab import PhaseCalculatorTab
from gui.tabs.twilight_tab import TwilightTimesTab


class SunPhaseApp(ctk.CTk):
    """Main application window for Sun Phase Tools."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Sun Phase Tools")
        self.geometry("800x600")
        self.minsize(700, 500)

        # Set appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Add tabs
        self.tabview.add("Phase Calculator")
        self.tabview.add("Twilight Times")

        # Initialize tab contents
        self.phase_tab = PhaseCalculatorTab(self.tabview.tab("Phase Calculator"))
        self.phase_tab.pack(fill="both", expand=True)

        self.twilight_tab = TwilightTimesTab(self.tabview.tab("Twilight Times"))
        self.twilight_tab.pack(fill="both", expand=True)


def run():
    """Launch the application."""
    app = SunPhaseApp()
    app.mainloop()
