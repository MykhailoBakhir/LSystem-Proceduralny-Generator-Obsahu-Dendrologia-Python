import tkinter as tk
from tkinter import messagebox
import berryBush 

def validate_inputs(values):
    if not (0 < values["seed"]):
        raise ValueError("Seed must be greater than 0.")
    if not (2 < values["length"] < 5):
        raise ValueError("Length must be between 2 and 5.")
    if not (0.01 <= values["initial_radius"] < 1):
        raise ValueError("Initial radius must be between 0 and 15.")
    if not (5 <= values["iterations"] <= 12):
        raise ValueError("Iterations must be between 5 and 12.")
    if not (0 <= values["berry_radius"] <= 1):
        raise ValueError("Berry radius must be greater than 0 and at most 1.")

def on_start():
    try:
        values = {}
        for key, entry in entries.items():
            if key in ("seed", "iterations"):
                values[key] = int(entry.get())
            else:
                values[key] = float(entry.get())

        validate_inputs(values)

        print("Entered values:")
        for key, value in values.items():
            print(f"{key}: {value}")

        messagebox.showinfo("Success", "All values are valid. Generating berry bush...")

        berryBush.generate_berry_bush(
            seed=values["seed"],
            iterations=values["iterations"],
            length=values["length"],
            initial_radius=values["initial_radius"],
            berry_radius=values["berry_radius"]
        )
        root.destroy()
    except ValueError as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Berry Bush Parameters")

params = {
    "seed": 618,
    "iterations": 10,
    "length": 3.0,
    "initial_radius": 0.2,
    "berry_radius": 0.5
}

entries = {}

for i, (param, default_value) in enumerate(params.items()):
    label = tk.Label(root, text=param)
    label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    entry = tk.Entry(root)
    entry.insert(0, str(default_value))
    entry.grid(row=i, column=1, padx=5, pady=5)
    entries[param] = entry

start_button = tk.Button(root, text="Generate", command=on_start)
start_button.grid(row=len(params), column=0, columnspan=2, pady=10)

root.mainloop()
