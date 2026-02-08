import json
import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QMenu, QAction, 
                           QFrame, QTreeWidget, QTreeWidgetItem, QHeaderView,
                           QFileDialog, QMessageBox, QHBoxLayout, QVBoxLayout,
                           QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QTextEdit, QAbstractItemView)
from PyQt5.QtCore import Qt

class JsonEditor(QMainWindow):
    def __init__(self):
        self.settings_file = "settings.json"
        super().__init__()
        self.initUI()
        self.data = None
        self.current_file_path = None
        self.load_settings()
        self.filtered_items = []
        self.current_filtered_index = -1
        
        # Load last opened file if exists and is valid
        if hasattr(self, 'last_file_path') and self.last_file_path:
            if os.path.exists(self.last_file_path):
                self.load_file(self.last_file_path)
            else:
                # File doesn't exist, clear the last file path
                self.last_file_path = None
                self.save_settings()

    def initUI(self):
        self.setWindowTitle("SCUM parameters.json Editor")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowState(Qt.WindowMaximized)

        # Load stylesheet
        self.load_stylesheet()

        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        # Create filter frame
        filter_frame = QFrame(self)
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_frame.setFrameShadow(QFrame.Raised)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setAlignment(Qt.AlignLeft)  # Align all widgets to the left
        
        filter_label = QLabel("Find ID:")
        self.filter_input = QLineEdit()
        self.filter_input.setMaxLength(50)  # Limit to 50 characters
        self.filter_input.setMinimumWidth(200)  # Set minimum width
        self.filter_input.setMaximumWidth(200)  # Set maximum width
        self.filter_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.filter_input.textChanged.connect(self.filter_items)
        
        prev_button = QPushButton("Previous")
        prev_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        prev_button.clicked.connect(self.previous_match)
        
        next_button = QPushButton("Next")
        next_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        next_button.clicked.connect(self.next_match)
        
        self.counter_label = QLabel("0/0")
        self.counter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(prev_button)
        filter_layout.addWidget(next_button)
        filter_layout.addWidget(self.counter_label)
        
        # Set minimum size for filter frame and make it not stretch
        filter_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        filter_frame.setFixedHeight(50)  # Set fixed height to prevent resizing
        
        # Create treeview
        tree_frame = QFrame(self)
        tree_layout = QVBoxLayout(tree_frame)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Id", "IsDisabledForSpawning", "AllowedLocations",
            "CooldownPerSquadMemberMin", "CooldownPerSquadMemberMax",
            "CooldownGroup", "Variations", "ShouldOverrideInitialAndRandomUsage",
            "InitialUsageOverride", "RandomUsageOverrideUsage"
        ])
    
        # Set column widths
        column_widths = [250, 60, 210, 180, 180, 200, 258, 220, 120, 180]
        for i, width in enumerate(column_widths):
            self.tree.setColumnWidth(i, width)
        
        # Set header options
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Fix: Set tree widget properties to prevent selection shift
        self.tree.setFrameStyle(QFrame.NoFrame)  # Remove frame to prevent padding
        self.tree.setIndentation(0)  # Remove indentation
        self.tree.setRootIsDecorated(False)  # Remove tree decoration
        self.tree.setUniformRowHeights(True)  # Ensure consistent row heights
        
        # Create scroll area for tree
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.tree)
        
        tree_layout.addWidget(scroll_area)
        
        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(filter_frame)
        main_layout.addWidget(tree_frame)
        main_layout.setStretch(1, 1)  # Only the tree area should stretch
        
        central_widget = QFrame()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.tree.itemSelectionChanged.connect(self.on_tree_select)
        self.tree.itemDoubleClicked.connect(self.on_double_click)
        
        # Load window state from settings
        self.load_window_state()

    def load_stylesheet(self):
        """Load the stylesheet from style.css file if it exists"""
        try:
            # Get the directory where the executable is located
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            style_file = os.path.join(exe_dir, "style.css")
            
            if os.path.exists(style_file):
                with open(style_file, 'r') as f:
                    style = f.read()
                    self.setStyleSheet(style)
            # If style.css doesn't exist, don't set any stylesheet
            # This allows Qt to use default colors
        except Exception as e:
            print(f"Failed to load stylesheet: {e}")
            # Don't set any fallback - let Qt use default styling

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.last_file_path = settings.get('last_file_path')
                    # Load window geometry and state
                    if 'geometry' in settings and settings['geometry']:
                        geometry = QtCore.QByteArray.fromHex(settings['geometry'].encode('utf-8'))
                        self.restoreGeometry(geometry)
                    if 'window_state' in settings and settings['window_state']:
                        window_state = QtCore.QByteArray.fromHex(settings['window_state'].encode('utf-8'))
                        self.restoreState(window_state)
                    if 'column_widths' in settings:
                        self.load_column_widths(settings['column_widths'])
        except Exception as e:
            print(f"Failed to load settings: {e}")
            self.last_file_path = None

    def save_settings(self):
        try:
            # Convert QByteArray to bytes for JSON serialization
            geometry = self.saveGeometry()
            window_state = self.saveState()
            
            settings = {
                'last_file_path': getattr(self, 'current_file_path', None),
                'geometry': geometry.toHex().data().decode('utf-8') if not geometry.isNull() else None,
                'window_state': window_state.toHex().data().decode('utf-8') if not window_state.isNull() else None,
                'column_widths': self.save_column_widths()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def save_column_widths(self):
        """Save column widths from tree header"""
        widths = []
        header = self.tree.header()
        for i in range(header.count()):
            widths.append(header.sectionSize(i))
        return widths

    def load_column_widths(self, widths):
        """Load column widths into tree header"""
        header = self.tree.header()
        for i, width in enumerate(widths):
            if i < header.count():
                header.resizeSection(i, width)

    def load_window_state(self):
        """Load window state (position, size, maximized status)"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    if 'geometry' in settings and settings['geometry']:
                        geometry = QtCore.QByteArray.fromHex(settings['geometry'].encode('utf-8'))
                        self.restoreGeometry(geometry)
                    if 'window_state' in settings and settings['window_state']:
                        window_state = QtCore.QByteArray.fromHex(settings['window_state'].encode('utf-8'))
                        self.restoreState(window_state)
        except Exception as e:
            print(f"Failed to load window state: {e}")

    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                self.current_file_path = file_path
                self.data = json.load(f)
            self.populate_tree()
            self.setWindowTitle(f"SCUM parameters.json Editor - {file_path}")
            self.save_settings()  # Save the path after successful loading
            # Update counter after loading file
            self.update_counter()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def open_file(self):
        # Get the directory of the last opened file or default to home directory
        if hasattr(self, 'last_file_path') and self.last_file_path:
            directory = os.path.dirname(self.last_file_path)
        else:
            directory = os.path.expanduser("~")
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", directory, "JSON files (*.json);;All files (*)"
        )
        if file_path:
            self.load_file(file_path)
            # Save the last used directory
            self.last_file_path = file_path
            self.save_settings()

    def populate_tree(self):
        self.tree.clear()
        if self.data and "Parameters" in self.data:
            for item in self.data["Parameters"]:
                tree_item = QTreeWidgetItem()
                tree_item.setText(0, str(item["Id"]))
                tree_item.setText(1, str(item["IsDisabledForSpawning"]).lower())
                tree_item.setText(2, str(item["AllowedLocations"]))
                tree_item.setText(3, str(item["CooldownPerSquadMemberMin"]))
                tree_item.setText(4, str(item["CooldownPerSquadMemberMax"]))
                tree_item.setText(5, str(item["CooldownGroup"]))
                tree_item.setText(6, str(item["Variations"]))
                tree_item.setText(7, str(item["ShouldOverrideInitialAndRandomUsage"]).lower())
                tree_item.setText(8, str(item["InitialUsageOverride"]))
                tree_item.setText(9, str(item["RandomUsageOverrideUsage"]))
                self.tree.addTopLevelItem(tree_item)

    def save_file(self):
        if not self.data:
            return

        # Update data from tree
        items = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            param = {
                "Id": item.text(0),
                "IsDisabledForSpawning": item.text(1).lower() == "true",
                "AllowedLocations": self.parse_list(item.text(2)),
                "CooldownPerSquadMemberMin": int(item.text(3)) if item.text(3) else 0,
                "CooldownPerSquadMemberMax": int(item.text(4)) if item.text(4) else 0,
                "CooldownGroup": item.text(5),
                "Variations": self.parse_list(item.text(6)),
                "ShouldOverrideInitialAndRandomUsage": item.text(7).lower() == "true",
                "InitialUsageOverride": int(item.text(8)) if item.text(8) else 0,
                "RandomUsageOverrideUsage": int(item.text(9)) if item.text(9) else 0
            }
            items.append(param)

        self.data["Parameters"] = items

        try:
            with open(self.current_file_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            QMessageBox.information(self, "Success", "File saved successfully!")
            self.save_settings()  # Save settings after successful save
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def save_as_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save JSON File", "", "JSON files (*.json);;All files (*)"
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

    def on_tree_select(self):
        pass

    def on_double_click(self, item, column):
        # Don't allow editing ID column
        if column == 0:
            return
            
        # Handle boolean columns
        if column == 1 or column == 7:
            current_value = item.text(column)
            new_value = "false" if current_value == "true" else "true"
            item.setText(column, new_value)
            return
            
        # For other columns, show edit dialog
        value = item.text(column)
        
        # Special handling for AllowedLocations and Variations columns
        if column == 2 or column == 6:
            # Create a dialog with a multi-line text edit for editing
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"Edit {self.tree.headerItem().text(column)}")
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            
            # Create text edit with word wrap
            text_edit = QTextEdit()
            text_edit.setPlainText(value)
            text_edit.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
            text_edit.setAcceptRichText(False)
            
            layout.addWidget(text_edit)
            
            # Buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.resize(500, 300)
            
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                new_value = text_edit.toPlainText()
                item.setText(column, new_value)
        else:
            # For other columns, use regular input dialog
            new_value, ok = QtWidgets.QInputDialog.getText(self, "Edit Value", "Enter new value:", text=value)
            if ok:
                item.setText(column, new_value)

    def filter_items(self, text):
        filter_text = text.lower()
        
        # Get all items
        all_items = []
        for i in range(self.tree.topLevelItemCount()):
            all_items.append(self.tree.topLevelItem(i))
        
        self.filtered_items = []
        
        # Filter items by ID (case insensitive)
        for item in all_items:
            item_id = item.text(0).lower()
            if filter_text in item_id:
                self.filtered_items.append(item)
        
        # Reset counter
        self.current_filtered_index = -1
        self.update_counter()
        
        # Clear selection
        self.tree.clearSelection()
        
        # If there's a filter, select first match and scroll to it
        if self.filtered_items and filter_text:
            # Temporarily disable selection change signals to prevent flickering
            self.tree.itemSelectionChanged.disconnect(self.on_tree_select)
            
            # Use a more controlled selection approach
            if self.filtered_items:
                self.tree.setCurrentItem(self.filtered_items[0])
                # Force update without causing layout shifts
                self.tree.scrollToItem(self.filtered_items[0], QAbstractItemView.PositionAtCenter)
                self.current_filtered_index = 0
                self.update_counter()
            
            # Reconnect the signal
            self.tree.itemSelectionChanged.connect(self.on_tree_select)

    def update_counter(self):
        # Get total items count
        total_items = self.tree.topLevelItemCount()
        if self.filtered_items:
            self.counter_label.setText(f"{self.current_filtered_index + 1}/{len(self.filtered_items)}")
        else:
            self.counter_label.setText(f"0/{total_items}")

    def next_match(self):
        if not self.filtered_items:
            return
            
        if self.current_filtered_index < len(self.filtered_items) - 1:
            self.current_filtered_index += 1
        else:
            self.current_filtered_index = 0  # Loop back to first
            
        item = self.filtered_items[self.current_filtered_index]
        
        # Temporarily disable selection change signals to prevent flickering
        self.tree.itemSelectionChanged.disconnect(self.on_tree_select)
        
        # Use a more controlled approach to avoid layout shifts
        self.tree.clearSelection()
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item, QAbstractItemView.PositionAtCenter)
        self.update_counter()
        
        # Reconnect the signal
        self.tree.itemSelectionChanged.connect(self.on_tree_select)

    def previous_match(self):
        if not self.filtered_items:
            return
            
        if self.current_filtered_index > 0:
            self.current_filtered_index -= 1
        else:
            self.current_filtered_index = len(self.filtered_items) - 1  # Loop to last
            
        item = self.filtered_items[self.current_filtered_index]
        
        # Temporarily disable selection change signals to prevent flickering
        self.tree.itemSelectionChanged.disconnect(self.on_tree_select)
        
        # Use a more controlled approach to avoid layout shifts
        self.tree.clearSelection()
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item, QAbstractItemView.PositionAtCenter)
        self.update_counter()
        
        # Reconnect the signal
        self.tree.itemSelectionChanged.connect(self.on_tree_select)

    def closeEvent(self, event):
        """Save settings when closing the application"""
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = JsonEditor()
    editor.show()
    sys.exit(app.exec_())
