import tkinter as tk
from window import Window

root = tk.Tk()
root.title("KV Merger")
root.geometry('650x340+300+200')
root.resizable(False, False)
window = Window(root)
root.mainloop()
