import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class JsonEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SCUM parameters.json Editor")
        self.root.geometry("800x600")
        self.root.state('zoomed')

        self.data = None
        self.current_editing_item = None
        self.current_editing_field = None
        self.editing_entry = None
        self.original_value = None

        # Load settings
        self.settings_file = "settings.json"
        self.load_settings()

        # Create menu
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_as_file)

        # Create treeview for displaying data
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Id", "IsDisabledForSpawning", "AllowedLocations",
                                                           "CooldownPerSquadMemberMin", "CooldownPerSquadMemberMax",
                                                           "CooldownGroup", "Variations", "ShouldOverrideInitialAndRandomUsage",
                                                           "InitialUsageOverride", "RandomUsageOverrideUsage"),
                                 show="headings", height=20)

        # Define headings
        self.tree.heading("Id", text="Id")
        self.tree.heading("IsDisabledForSpawning", text="Disabled")
        self.tree.heading("AllowedLocations", text="AllowedLocations")
        self.tree.heading("CooldownPerSquadMemberMin", text="CooldownPerSquadMemberMin")
        self.tree.heading("CooldownPerSquadMemberMax", text="CooldownPerSquadMemberMax")
        self.tree.heading("CooldownGroup", text="CooldownGroup")
        self.tree.heading("Variations", text="Variations")
        self.tree.heading("ShouldOverrideInitialAndRandomUsage", text="ShouldOverrideInitialAndRandomUsage")
        self.tree.heading("InitialUsageOverride", text="InitialUsageOverride")
        self.tree.heading("RandomUsageOverrideUsage", text="RandomUsageOverrideUsage")

        # Set column widths
        self.tree.column("Id", width=250, minwidth=250, stretch=tk.NO)
        self.tree.column("IsDisabledForSpawning", anchor='center', width=60, minwidth=60, stretch=tk.NO)
        self.tree.column("AllowedLocations", width=210, minwidth=210, stretch=tk.NO)
        self.tree.column("CooldownPerSquadMemberMin", anchor='center', width=180, minwidth=180, stretch=tk.NO)
        self.tree.column("CooldownPerSquadMemberMax", anchor='center', width=180, minwidth=180, stretch=tk.NO)
        self.tree.column("CooldownGroup", width=200, minwidth=200, stretch=tk.NO)
        self.tree.column("Variations", width=280, minwidth=280, stretch=tk.NO)
        self.tree.column("ShouldOverrideInitialAndRandomUsage", anchor='center', width=220, minwidth=220, stretch=tk.NO)
        self.tree.column("InitialUsageOverride", anchor='center', width=120, minwidth=120, stretch=tk.NO)
        self.tree.column("RandomUsageOverrideUsage", anchor='center', width=180, minwidth=180, stretch=tk.NO)

        # Add vertical scrollbar
        vsb = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        # Add horizontal scrollbar
        hsb = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=hsb.set)

        # Grid layout for scrollbars and treeview
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Key>", self.on_key_press)

        # Set up editing entry
        self.editing_frame = tk.Frame(root)
        self.editing_frame.pack_forget()

        # Load last opened file if exists and is valid
        if hasattr(self, 'last_file_path') and self.last_file_path:
            if os.path.exists(self.last_file_path):
                self.load_file(self.last_file_path)
            else:
                # File doesn't exist, clear the last file path
                self.last_file_path = None
                self.save_settings()

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.last_file_path = settings.get('last_file_path')
            else:
                self.last_file_path = None
        except Exception as e:
            print(f"Failed to load settings: {e}")
            self.last_file_path = None

    def save_settings(self):
        try:
            settings = {
                'last_file_path': getattr(self, 'current_file_path', None)
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                self.current_file_path = file_path
                self.data = json.load(f)
            self.populate_tree()
            self.root.title(f"SCUM parameters.json Editor - {file_path}")
            self.save_settings()  # Save the path after successful loading
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Open JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.load_file(file_path)

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        if self.data and "Parameters" in self.data:
            for item in self.data["Parameters"]:
                values = (
                    item["Id"],
                    str(item["IsDisabledForSpawning"]).lower(),
                    str(item["AllowedLocations"]),
                    str(item["CooldownPerSquadMemberMin"]),
                    str(item["CooldownPerSquadMemberMax"]),
                    item["CooldownGroup"],
                    str(item["Variations"]),
                    str(item["ShouldOverrideInitialAndRandomUsage"]).lower(),
                    str(item["InitialUsageOverride"]),
                    str(item["RandomUsageOverrideUsage"])
                )
                self.tree.insert("", tk.END, values=values)

    def save_file(self):
        if not self.data:
            return

        # Update data from tree
        items = self.tree.get_children()
        self.data["Parameters"] = []

        for item in items:
            values = self.tree.item(item, "values")
            param = {
                "Id": values[0],
                "IsDisabledForSpawning": values[1].lower() == "true",
                "AllowedLocations": self.parse_list(values[2]),
                "CooldownPerSquadMemberMin": int(values[3]) if values[3] else 0,
                "CooldownPerSquadMemberMax": int(values[4]) if values[4] else 0,
                "CooldownGroup": values[5],
                "Variations": self.parse_list(values[6]),
                "ShouldOverrideInitialAndRandomUsage": values[7].lower() == "true",
                "InitialUsageOverride": int(values[8]) if values[8] else 0,
                "RandomUsageOverrideUsage": int(values[9]) if values[9] else 0
            }
            self.data["Parameters"].append(param)

        try:
            with open(self.current_file_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            messagebox.showinfo("Success", "File saved successfully!")
            self.save_settings()  # Save settings after successful save
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save JSON File",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.current_file_path = file_path
            self.save_file()

    def parse_list(self, value):
        # Parse string representation of list to actual list
        if value.startswith('[') and value.endswith(']'):
            # Remove brackets and split by comma
            items = value[1:-1].split(',')
            return [item.strip().strip("'\"") for item in items if item.strip()]
        return []

    def on_tree_select(self, event):
        return

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        column_index = int(column.replace("#", "")) - 1

        if column_index == 0 or column_index == 6:  # column is not editable
            return

        if column_index == 1 or column_index == 7:
            current_value = self.tree.item(item, "values")[column_index]
            new_value = "false" if current_value == "true" else "true"
            values = list(self.tree.item(item, "values"))
            values[column_index] = new_value
            self.tree.item(item, values=values)
            return

        # Get the item values
        values = self.tree.item(item, "values")
        self.original_value = values[column_index]

        # Position editing entry
        x, y, width, height = self.tree.bbox(item, column)
        self.editing_entry = tk.Entry(self.tree_frame)
        self.editing_entry.place(x=x, y=y, width=width, height=height)
        self.editing_entry.insert(0, self.original_value)
        self.editing_entry.focus_set()

        self.current_editing_item = item
        self.current_editing_field = column_index

        # Bind events to editing entry
        self.editing_entry.bind("<Return>", self.apply_edit)
        self.editing_entry.bind("<Escape>", self.cancel_edit)
        self.editing_entry.bind("<FocusOut>", self.apply_edit)

    def apply_edit(self, event=None):
        if self.editing_entry and self.current_editing_item and self.current_editing_field:
            new_value = self.editing_entry.get()
            # Update the treeview
            values = self.tree.item(self.current_editing_item, "values")
            values = list(values)
            values[self.current_editing_field] = new_value
            self.tree.item(self.current_editing_item, values=values)

            # Destroy editing entry
            self.editing_entry.destroy()
            self.editing_entry = None
            self.current_editing_item = None
            self.current_editing_field = None

    def cancel_edit(self, event=None):
        if self.editing_entry and self.current_editing_item and self.current_editing_field:
            # Restore original value
            values = self.tree.item(self.current_editing_item, "values")
            values = list(values)
            values[self.current_editing_field] = self.original_value
            self.tree.item(self.current_editing_item, values=values)

            # Destroy editing entry
            self.editing_entry.destroy()
            self.editing_entry = None
            self.current_editing_item = None
            self.current_editing_field = None

    def on_key_press(self, event):
        if event.keysym == "Escape" and self.editing_entry:
            self.cancel_edit()
        elif event.keysym == "Return" and self.editing_entry:
            self.apply_edit()

    def on_closing(self):
        # Clear last file path if no file was opened or saved
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            self.last_file_path = None
            self.save_settings()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonEditor(root)
    root.mainloop()
