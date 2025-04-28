import sys
print("当前Python解释器路径:", sys.executable)
print("当前Python版本:", sys.version)
import tkinter as tk

root = tk.Tk()
root.title("Tkinter 测试")
label = tk.Label(root, text="Hello Tkinter!", bg="yellow")
label.pack(padx=50, pady=50)
root.mainloop()
