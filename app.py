import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


DEFAULT_CONFIG = {"autofill": {"find": True, "replace": False}}


def load_config(config_path):
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        autofill = config["autofill"]
        if not isinstance(autofill["find"], bool) or not isinstance(
            autofill["replace"], bool
        ):
            raise ValueError("The autofill settings must be true or false.")
        return {"autofill": autofill}
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        messagebox.showwarning(
            "Configuration problem",
            f"Could not read {config_path.name}: {error}\n"
            "The built-in autofill defaults will be used for this session.",
        )
        return DEFAULT_CONFIG.copy()


def matching_files(paths, find_text):
    if not find_text:
        return []
    return sorted(
        (path for path in paths if find_text in path.stem),
        key=lambda path: str(path).casefold(),
    )


def planned_renames(paths, find_text, replace_text):
    return [(path, path.with_name(path.stem.replace(find_text, replace_text) + path.suffix))
            for path in paths]


class RenameFilestemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rename Filestems")
        self.root.minsize(760, 500)
        self.config = load_config(Path(__file__).with_name("config.json"))

        self.base_directory = None
        self.source_paths = []
        self.matches = []
        self.last_find_text = None
        self.active_directories = set()
        self.directory_paths = set()

        self.find_text = tk.StringVar()
        self.replace_text = tk.StringVar()
        self.selection_text = tk.StringVar(value="No files selected")
        self.active_directory_text = tk.StringVar(value="Active Directory: All")
        self.find_text.trace_add("write", self._on_find_text_change)
        self.replace_text.trace_add("write", self.update_preview)

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        selection_row = ttk.Frame(main)
        selection_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        selection_row.columnconfigure(0, weight=1)
        ttk.Label(selection_row, textvariable=self.selection_text).grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        browse_button = ttk.Menubutton(selection_row, text="Browse...")
        browse_menu = tk.Menu(browse_button, tearoff=False)
        browse_menu.add_command(
            label="Select a directory...", command=self.select_directory
        )
        browse_menu.add_command(label="Select files...", command=self.select_files)
        browse_button["menu"] = browse_menu
        browse_button.grid(row=0, column=1, sticky="e")

        fields = ttk.Frame(main)
        fields.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        fields.columnconfigure(1, weight=1)
        fields.columnconfigure(3, weight=1)
        ttk.Label(fields, text="Find:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Label(fields, text="Replace with:").grid(
            row=0, column=2, sticky="w", padx=(14, 6)
        )
        self.find_field = self._make_text_field(
            fields, 1, self.find_text, self.config["autofill"]["find"]
        )
        self.replace_field = self._make_text_field(
            fields, 3, self.replace_text, self.config["autofill"]["replace"]
        )

        actions = ttk.Frame(main)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.find_button = ttk.Button(actions, text="Find", command=self.find_matches)
        self.find_button.pack(side="left")
        self.active_directory_button = ttk.Menubutton(
            actions, textvariable=self.active_directory_text, state="disabled"
        )
        self.active_directory_button.pack(side="left", padx=8)
        self.replace_button = ttk.Button(
            actions, text="Replace", command=self.replace_selected, state="disabled"
        )
        self.replace_button.pack(side="right")

        ttk.Label(
            main,
            text="Select matched files to rename. The file extension is preserved.",
        ).grid(row=3, column=0, sticky="w", pady=(0, 5))

        list_frame = ttk.Frame(main)
        list_frame.grid(row=5, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        columns = ("file", "directory", "new_name")
        self.file_list = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="extended"
        )
        self.file_list.heading("file", text="Matched file")
        self.file_list.heading("directory", text="Directory")
        self.file_list.heading("new_name", text="New name preview")
        self.file_list.column("file", width=240, minwidth=140)
        self.file_list.column("directory", width=220, minwidth=120)
        self.file_list.column("new_name", width=240, minwidth=140)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.file_list.yview
        )
        self.file_list.configure(yscrollcommand=scrollbar.set)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.status_text = tk.StringVar(value="Choose a directory or files to begin.")
        ttk.Label(main, textvariable=self.status_text).grid(
            row=6, column=0, sticky="w", pady=(8, 0)
        )

    @staticmethod
    def _make_text_field(parent, column, variable, autofill):
        if autofill:
            field = ttk.Combobox(parent, textvariable=variable)
        else:
            field = ttk.Entry(parent, textvariable=variable)
        field.grid(row=0, column=column, sticky="ew")
        return field

    def select_directory(self):
        selected = filedialog.askdirectory(title="Select a directory")
        if not selected:
            return
        root_directory = Path(selected)
        try:
            paths = [path for path in root_directory.rglob("*") if path.is_file()]
        except OSError as error:
            messagebox.showerror("Could not read directory", str(error))
            return
        self._set_source_paths(paths, root_directory)

    def select_files(self):
        selected = filedialog.askopenfilenames(title="Select files")
        if not selected:
            return
        selected_paths = [Path(path) for path in selected]
        try:
            base_directory = Path(
                os.path.commonpath([str(path.parent) for path in selected_paths])
            )
        except ValueError as error:
            messagebox.showerror("Files must share a directory", str(error))
            return
        stems = {path.stem for path in selected_paths}
        try:
            related_paths = [
                path
                for path in base_directory.rglob("*")
                if path.is_file() and path.stem in stems
            ]
        except OSError as error:
            messagebox.showerror("Could not read directory", str(error))
            return
        self._set_source_paths(related_paths, base_directory)

    def _set_source_paths(self, paths, base_directory):
        self.base_directory = base_directory
        self.source_paths = sorted(
            set(paths), key=lambda path: str(path).casefold()
        )
        unique_stems = sorted({path.stem for path in self.source_paths}, key=str.casefold)
        for field, key in (
            (self.find_field, "find"),
            (self.replace_field, "replace"),
        ):
            if self.config["autofill"][key] and isinstance(field, ttk.Combobox):
                field["values"] = unique_stems
        self.selection_text.set(
            f"{len(self.source_paths)} files available in {base_directory}"
        )
        self.matches = []
        self.last_find_text = None
        self.directory_paths = set()
        self.active_directories = set()
        self._set_active_directory_menu()
        self._render_matches()
        self.status_text.set("Enter text to find, then choose Find.")

    def find_matches(self):
        if not self.source_paths:
            messagebox.showinfo("No files selected", "Choose a directory or files first.")
            return
        find_text = self.find_text.get()
        if not find_text:
            messagebox.showinfo("Find text required", "Enter text to find.")
            return
        self.matches = matching_files(self.source_paths, find_text)
        self.last_find_text = find_text
        self.directory_paths = {
            path.parent.relative_to(self.base_directory) for path in self.matches
        }
        self.active_directories = set(self.directory_paths)
        self._set_active_directory_menu()
        self._render_matches()
        self.status_text.set(f"{len(self.matches)} matching files found.")

    def _set_active_directory_menu(self):
        menu = tk.Menu(self.active_directory_button, tearoff=False)
        menu.add_command(label="Select All", command=self._select_all_directories)
        menu.add_command(label="Select None", command=self._select_no_directories)
        menu.add_separator()

        tree = {}
        for relative_path in self.directory_paths:
            node = tree
            for part in relative_path.parts:
                node = node.setdefault(part, {})
            node.setdefault("", {})

        root_label = self.base_directory.name if self.base_directory else "Directory"
        root_variable = tk.BooleanVar(
            value=Path(".") in self.active_directories
        )
        root_menu = tk.Menu(menu, tearoff=False)
        menu.add_checkbutton(
            label=root_label,
            variable=root_variable,
            command=lambda: self._toggle_directory(Path("."), root_variable),
        )
        self._add_directory_items(menu, tree, Path())
        self.active_directory_button["menu"] = menu
        self._update_active_directory_label()

    def _add_directory_items(self, menu, tree, parent_path):
        for name in sorted(tree, key=str.casefold):
            if not name:
                continue
            relative_path = parent_path / name
            has_direct_files = "" in tree[name]
            if tree[name] and any(key for key in tree[name]):
                submenu = tk.Menu(menu, tearoff=False)
                menu.add_cascade(label=name, menu=submenu)
                if has_direct_files:
                    variable = tk.BooleanVar(
                        value=relative_path in self.active_directories
                    )
                    submenu.add_checkbutton(
                        label=name,
                        variable=variable,
                        command=lambda path=relative_path, var=variable: self._toggle_directory(
                            path, var
                        ),
                    )
                    submenu.add_separator()
                self._add_directory_items(submenu, tree[name], relative_path)
            else:
                variable = tk.BooleanVar(
                    value=relative_path in self.active_directories
                )
                menu.add_checkbutton(
                    label=name,
                    variable=variable,
                    command=lambda path=relative_path, var=variable: self._toggle_directory(
                        path, var
                    ),
                )

    def _toggle_directory(self, path, variable):
        if variable.get():
            self.active_directories.add(path)
        else:
            self.active_directories.discard(path)
        self._update_active_directory_label()
        self._render_matches()

    def _select_all_directories(self):
        self.active_directories = set(self.directory_paths)
        self._set_active_directory_menu()
        self._render_matches()

    def _select_no_directories(self):
        self.active_directories.clear()
        self._set_active_directory_menu()
        self._render_matches()

    def _update_active_directory_label(self):
        if self.active_directories == self.directory_paths:
            label = "All"
        elif not self.active_directories:
            label = "None"
        elif len(self.active_directories) == 1:
            selected = next(iter(self.active_directories))
            label = self.base_directory.name if selected == Path(".") else selected.name
        else:
            label = f"{len(self.active_directories)} selected"
        self.active_directory_text.set(f"Active Directory: {label}")
        self.active_directory_button.configure(
            state="normal" if self.directory_paths else "disabled"
        )

    def _visible_matches(self):
        return [
            path
            for path in self.matches
            if path.parent.relative_to(self.base_directory) in self.active_directories
        ]

    def _render_matches(self):
        self.file_list.delete(*self.file_list.get_children())
        for index, path in enumerate(self._visible_matches()):
            relative_directory = path.parent.relative_to(self.base_directory)
            directory_label = (
                self.base_directory.name
                if relative_directory == Path(".")
                else str(relative_directory)
            )
            self.file_list.insert(
                "",
                "end",
                iid=str(index),
                values=(path.name, directory_label, self._preview_name(path)),
            )
        self.replace_button.configure(
            state="normal"
            if self._visible_matches() and self.last_find_text == self.find_text.get()
            else "disabled"
        )

    def _preview_name(self, path):
        find_text = self.find_text.get()
        if not find_text:
            return path.name
        new_stem = path.stem.replace(find_text, self.replace_text.get())
        return new_stem + path.suffix

    def update_preview(self, *_):
        if hasattr(self, "file_list"):
            self._render_matches()

    def _on_find_text_change(self, *_):
        self.update_preview()
        if self.matches and self.find_text.get() != self.last_find_text:
            self.status_text.set("Find text changed; click Find to refresh the matches.")

    def replace_selected(self):
        if self.find_text.get() != self.last_find_text:
            messagebox.showinfo(
                "Refresh matches", "Click Find again before replacing files."
            )
            return
        selected_items = self.file_list.selection()
        if not selected_items:
            messagebox.showinfo(
                "No files selected", "Select one or more matched files to rename."
            )
            return
        find_text = self.find_text.get()
        if not find_text:
            messagebox.showinfo("Find text required", "Enter text to find.")
            return

        visible = self._visible_matches()
        selected_paths = [visible[int(item)] for item in selected_items]
        renames = planned_renames(selected_paths, find_text, self.replace_text.get())
        targets = {}
        conflicts = []
        for source, target in renames:
            normalized_target = os.path.normcase(str(target))
            if normalized_target in targets:
                conflicts.append(f"{target} is targeted by multiple files")
            targets[normalized_target] = source
            if target.exists() and os.path.normcase(str(source)) != normalized_target:
                conflicts.append(f"{target} already exists")
        if conflicts:
            messagebox.showerror(
                "Rename conflict",
                "No files were renamed:\n\n" + "\n".join(sorted(set(conflicts))),
            )
            return

        completed = []
        for source, target in renames:
            if source == target:
                continue
            try:
                source.rename(target)
                completed.append((source, target))
            except OSError as error:
                messagebox.showerror(
                    "Rename failed",
                    f"Renamed {len(completed)} file(s) before this error:\n"
                    f"{source} -> {target}\n{error}",
                )
                self._apply_completed_renames(completed)
                return

        self._apply_completed_renames(completed)
        self.status_text.set(f"Renamed {len(completed)} file(s).")

    def _apply_completed_renames(self, completed):
        renamed_paths = {source: target for source, target in completed}
        self.source_paths = [
            renamed_paths.get(path, path) for path in self.source_paths
        ]
        self.find_matches()


def main():
    root = tk.Tk()
    RenameFilestemApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
