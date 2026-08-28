"""
windows/main_window.py

The recipe entry page: Title / Category / Ingredients / Directions, with
File (New/Save/Quit) and Config menu actions.

This is a standalone QMainWindow for now, runnable and testable on its
own. When the QStackedWidget navigation shell is introduced later (see
project plan §9), the menu-building and central-widget logic here gets
lifted into a page the shell can swap in alongside the search page - the
widget layout and public method names (new_recipe, save_recipe, the
title/category/ingredients/directions attributes) are designed to stay
stable through that refactor.

Note on saved file layout: a blank line is written before the title, ahead
of Title / Ingredients / Directions each being separated by a single blank
line. This is intentional (not carried over by accident) - it keeps the
title from sitting flush against the top edge of the screen when recipes
are viewed on small displays, e.g. a 7" screen in the kitchen. The
Category footer is appended separately by categories.attach_category().
"""

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig
from categories import attach_category
from formatting import format_directions, format_filename, format_ingredients


class MainWindow(QMainWindow):
    """The recipe entry window."""

    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config

        self.setWindowTitle("Recipe Scribe")
        self._build_menu_bar()
        self._build_central_widget()
        self._apply_tab_order()
        self.title_entry.setFocus()

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_recipe)
        file_menu.addAction(new_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_recipe)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Config menu: full dialogs (path picker, bullet/format/dark-mode
        # toggles, category list management) land in config_dialogs.py in
        # a later step. These two actions are wired to minimal working
        # behavior now so the save path and category-adding flows are
        # usable in the meantime, and will be swapped for the richer
        # dialogs without changing this menu's structure.
        config_menu = menu_bar.addMenu("&Config")

        set_path_action = QAction("Set Default Save Path", self)
        set_path_action.triggered.connect(self.set_default_save_path)
        config_menu.addAction(set_path_action)

        manage_categories_action = QAction("Manage Categories", self)
        manage_categories_action.triggered.connect(self.manage_categories)
        config_menu.addAction(manage_categories_action)

        help_menu = menu_bar.addMenu("&Help")

        help_action = QAction("Program Help", self)
        help_action.setShortcut(QKeySequence("Ctrl+H"))
        help_menu.addAction(help_action)

        about_action = QAction("About", self)
        help_menu.addAction(about_action)

        # Placeholder - wired to the QStackedWidget shell once it exists.
        menu_bar.addAction("Search Recipes")

    # ------------------------------------------------------------------
    # Central widget
    # ------------------------------------------------------------------

    def _build_central_widget(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QGridLayout(central)

        title_label = QLabel("Recipe Title")
        self.title_entry = QLineEdit()
        self.title_entry.setToolTip("Enter the title of the recipe here")

        category_label = QLabel("Category")
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.config.categories)
        self.category_combo.setCurrentIndex(-1)  # no category selected by default
        self.category_combo.setToolTip(
            "Choose a category, or type a new one to add it on save"
        )

        layout.addWidget(title_label, 0, 0)
        layout.addWidget(self.title_entry, 0, 1)
        layout.addWidget(category_label, 0, 2)
        layout.addWidget(self.category_combo, 0, 3)

        ing_group = QGroupBox("Ingredients")
        ing_layout = QVBoxLayout(ing_group)
        self.ingredients_edit = QPlainTextEdit()
        self.ingredients_edit.setToolTip(
            "Enter ingredients here, one per line\n"
            "Begin a line with a period to omit the bullet point"
        )
        ing_layout.addWidget(self.ingredients_edit)
        layout.addWidget(ing_group, 1, 0, 1, 2)

        dir_group = QGroupBox("Directions")
        dir_layout = QVBoxLayout(dir_group)
        self.directions_edit = QPlainTextEdit()
        self.directions_edit.setToolTip("Enter the recipe instructions here")
        dir_layout.addWidget(self.directions_edit)
        layout.addWidget(dir_group, 1, 2, 1, 2)

        layout.setRowStretch(1, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

    def _apply_tab_order(self) -> None:
        self.setTabOrder(self.title_entry, self.category_combo)
        self.setTabOrder(self.category_combo, self.ingredients_edit)
        self.setTabOrder(self.ingredients_edit, self.directions_edit)
        self.setTabOrder(self.directions_edit, self.title_entry)

    # ------------------------------------------------------------------
    # File actions
    # ------------------------------------------------------------------

    def new_recipe(self) -> None:
        """Clears all fields for entry of another recipe."""
        self.title_entry.clear()
        self.category_combo.setCurrentIndex(-1)
        self.ingredients_edit.clear()
        self.directions_edit.clear()
        self.title_entry.setFocus()

    def save_recipe(self) -> None:
        """
        Opens the save dialog, formats the recipe body, prompts to add an
        unrecognized category to the known list, appends the category
        footer, and writes the file.
        """
        title = self.title_entry.text()
        category = self.category_combo.currentText().strip()

        suggested_filename = format_filename(title, self.config.format_filename)
        default_dir = self.config.save_path or ""
        default_path = (
            os.path.join(default_dir, suggested_filename)
            if default_dir
            else suggested_filename
        )

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Recipe", default_path, "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return  # user cancelled

        if category:
            self._offer_to_add_new_category(category)

        body = self._build_recipe_body(title)
        full_text = attach_category(body, category or None)

        with open(path, "w", encoding="utf-8") as f:
            f.write(full_text)

    def _offer_to_add_new_category(self, category: str) -> None:
        already_known = any(
            existing.lower() == category.lower() for existing in self.config.categories
        )
        if already_known:
            return

        reply = QMessageBox.question(
            self,
            "New Category",
            f'"{category}" is not in your category list yet. Add it?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config.add_category(category)
            self.config.save()
            self.category_combo.addItem(category)

    def _build_recipe_body(self, title: str) -> str:
        """
        Assembles the Title/Ingredients/Directions text that gets written
        to disk, ahead of the category footer being appended separately.

        A leading blank line is included before the title on purpose -
        it keeps the title from sitting flush against the top of the
        screen when the file is viewed on a small display.
        """
        ingredient_lines = format_ingredients(
            self.ingredients_edit.toPlainText(), self.config.use_bullet_points
        )
        direction_lines = format_directions(self.directions_edit.toPlainText())

        parts = [
            "",
            title,
            "",
            "Ingredients",
            "",
            *ingredient_lines,
            "",
            "Directions",
            "",
            *direction_lines,
        ]
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Config menu actions (minimal working behavior for now - see
    # config_dialogs.py in a later build step for the full dialogs)
    # ------------------------------------------------------------------

    def set_default_save_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Default Save Path")
        if path:
            self.config.save_path = path
            self.config.save()

    def manage_categories(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Category", "New category name:")
        if ok and name.strip():
            if self.config.add_category(name.strip()):
                self.config.save()
                self.category_combo.addItem(name.strip())
