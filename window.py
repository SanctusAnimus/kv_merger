import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.scrolledtext import ScrolledText
from json import load, dump
from pathlib import Path

from watchdog.observers import Observer
from watchdog_class import FsChangesHandler

from merger import merge_profile


class Window:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.profiles = self.load_profiles()
        self.observer = None
        self.watchdog = None
        self.start_watchdog()

        style = ttk.Style(root)
        style.configure('lefttab.TNotebook', tabposition='wn')
        style.configure('lefttab.TNotebook.Tab', width=20)

        self.profile_tabs = ttk.Notebook(root, style='lefttab.TNotebook', width=600, height=340)
        for profile in self.profiles:
            frame = ProfileFrame(self.profile_tabs, profile)
            self.profile_tabs.add(frame, text=profile["name"])
        self.profile_tabs.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, expand=True)
        self.profile_tabs.bind("<Button-3>", self.open_profile_list_menu)
        self.active_profile_index = 0

        # self.profile_list.bind("<<ListboxSelect>>", self.profile_changed)
        # self.profile_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.profile_list_menu = tk.Menu(root, tearoff=0)
        self.profile_list_menu.add_command(label="Add profile", command=self.add_profile)
        self.profile_list_menu.add_command(label="Remove profile", command=self.remove_profile)

        self.root.protocol("WM_DELETE_WINDOW", self.on_shutdown)
        # self.on_active_profile_changed()

    def on_shutdown(self):
        with open("_profiles.json", "w") as target:
            dump(self.profiles or [], target)
        self.observer.stop()
        self.observer.join()
        self.root.destroy()

    def start_watchdog(self):
        self.watchdog = FsChangesHandler()
        self.observer = Observer()
        self.observer.schedule(self.watchdog, ".", recursive=True)
        self.watchdog.update_profiles(self.profiles)
        self.observer.start()

    def open_profile_list_menu(self, event):
        try:
            self.profile_list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.profile_list_menu.grab_release()

    def add_profile(self):
        new_profile_config = {
            "name": "<Name>",
            "source_dir": "",
            "target_file_name": "",
            "prefix": "",
            "postfix": "",
        }
        new_frame = ProfileFrame(self.profile_tabs, new_profile_config)
        self.profile_tabs.add(
            new_frame, text="<Name>"
        )
        self.profiles.append(new_profile_config)
        self.watchdog.update_profiles(self.profiles)

    def remove_profile(self):
        selected = self.profile_tabs.select()
        if selected:
            index = self.profile_tabs.index(selected)
            self.profiles.pop(index)
            self.profile_tabs.forget(selected)
            # print(self.profile_tabs.tab(selected))

    def load_profiles(self):
        path = Path("_profiles.json")
        if not path.exists():
            return []
        with open(path, 'rt') as profiles_src:
            return load(profiles_src)


class ProfileFrame(tk.Frame):
    def __init__(self, parent, profile):
        self.parent = parent
        self.profile = profile
        super().__init__(parent, pady=5, takefocus=0)

        ttk.Label(self, text="Profile Name").grid(column=0, row=0, sticky=tk.W)
        self.profile_name_variable = tk.StringVar()
        self.profile_name_variable.set(self.profile["name"])
        self.profile_name = ttk.Entry(self, width=30, textvariable=self.profile_name_variable, takefocus=0)
        self.profile_name.bind("<Return>", self.on_profile_name_changed)
        self.profile_name.grid(column=1, row=0, sticky=tk.W)

        ttk.Label(self, text="Directory").grid(column=0, row=1, sticky=tk.W)
        self.source_directory_variable = tk.StringVar()
        self.source_directory_variable.set(self.profile["source_dir"])
        self.source_directory = ttk.Entry(
            self, width=60, state="readonly",
            textvariable=self.source_directory_variable, takefocus=0
        )
        self.source_directory.grid(column=1, row=1)
        ttk.Button(self, text="...", width=5, command=self.ask_directory).grid(column=2, row=1)

        ttk.Label(self, text="Output File").grid(column=0, row=2, sticky=tk.W)
        self.target_variable = tk.StringVar()
        self.target_variable.set(self.profile["target_file_name"])
        self.target = ttk.Entry(self, width=60, state="readonly", textvariable=self.target_variable, takefocus=0)
        self.target.grid(column=1, row=2)
        ttk.Button(self, text="...", width=5, command=self.ask_save_file).grid(column=2, row=2)

        ttk.Label(self, text="Prefix").grid(column=0, row=3, sticky=tk.W)
        self.prefix = ScrolledText(self, height=3, takefocus=0)
        self.prefix.insert('1.0', profile["prefix"])
        self.prefix.bind("<KeyRelease>", self.prefix_modified)
        self.prefix.grid(row=4, column=0, columnspan=4, sticky=tk.NSEW)

        ttk.Label(self, text="Postfix").grid(column=0, row=5, sticky=tk.W)
        self.postfix = ScrolledText(self, height=3, takefocus=0)
        self.postfix.insert('1.0', profile["postfix"])
        self.postfix.bind("<KeyRelease>", self.postfix_modified)
        self.postfix.grid(row=6, column=0, columnspan=4, sticky=tk.NSEW)

        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)

        merge_profile(profile)

    def ask_directory(self):
        current_dir = os.getcwd()
        selected_folder = askdirectory(title="Select KV source directory", initialdir=current_dir)
        if selected_folder:
            rel_path = os.path.relpath(selected_folder, os.getcwd())
            self.source_directory_variable.set(rel_path)
            self.profile["source_dir"] = rel_path

    def ask_save_file(self):
        selected_file_name = askopenfilename(
            title="Select KV compilation target",
            initialdir=os.getcwd(),
            filetypes=[("Text", ".txt"), ("KV", ".kv")],
            defaultextension="txt"
        )
        if selected_file_name:
            rel_path = os.path.relpath(selected_file_name, os.getcwd())
            self.target_variable.set(rel_path)
            self.profile["target_file_name"] = rel_path

    def on_profile_name_changed(self, _):
        new_profile_name = self.profile_name.get()
        self.profile["name"] = new_profile_name
        self.parent.tab("current", text=new_profile_name)
        return True

    def prefix_modified(self, _):
        self.profile["prefix"] = self.prefix.get('1.0', tk.END)

    def postfix_modified(self, _):
        self.profile["postfix"] = self.postfix.get('1.0', tk.END)
