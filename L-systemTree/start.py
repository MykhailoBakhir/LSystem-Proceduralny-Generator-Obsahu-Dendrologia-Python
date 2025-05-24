import tkinter as tk
from tkinter import messagebox
import tree

def validate_inputs(values):
    if not (0 < values["seed"]):
        raise ValueError("Seed must be greater than 0.")
    if not (5 < values["length"] < 15):
        raise ValueError("Length must be between 5 and 15.")
    if not (5 < values["initial_radius"] < 15):
        raise ValueError("Initial radius must be between 5 and 15.")
    if not (0.85 < values["taper"] <= 1):
        raise ValueError("Taper must be greater than 0.85 and less than or equal to 1.")
    if not (8 < values["sections"] < 256):
        raise ValueError("Sections must be between 8 and 256.")
    if not (5 < values["iterations"] < 12):
        raise ValueError("Iterations must be between 5 and 12.")
    if not (15 <= values["angle_deg"] <= 30):
        raise ValueError("Angle (deg) must be between 15 and 30.")
    if not (0 <= values["angle_variation"] <= 30):
        raise ValueError("Angle variation must be between 0 and 30.")
    if not (0 <= values["branch_deletion_chance"] <= 1):
        raise ValueError("Branch deletion chance must be between 0 and 1.")

def on_start():
    try:
        values = {}
        for key, entry in entries.items():
            if key in ("seed", "sections", "iterations"):
                values[key] = int(entry.get())
            else:
                values[key] = float(entry.get())

        validate_inputs(values)

        print("Entered values:")
        for key, value in values.items():
            print(f"{key}: {value}")

        messagebox.showinfo("Success", "All values are valid. Check the console.")

        tree.generate_tree(
            seed=values["seed"],
            length=values["length"],
            initial_radius=values["initial_radius"],
            taper=values["taper"],
            sections=values["sections"],
            iterations=values["iterations"],
            angle_deg=values["angle_deg"],
            angle_variation=values["angle_variation"],
            branch_deletion_chance=values["branch_deletion_chance"]  
        )
    except ValueError as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Parameter Input")

params = {
    "seed": 618,
    "length": 10,
    "initial_radius": 8,
    "taper": 0.9,
    "sections": 32,
    "iterations": 9,
    "angle_deg": 15,
    "angle_variation": 20,
    "branch_deletion_chance": 0.4
}

entries = {}

for i, (param, default_value) in enumerate(params.items()):
    label = tk.Label(root, text=param)
    label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    entry = tk.Entry(root)
    entry.insert(0, str(default_value))
    entry.grid(row=i, column=1, padx=5, pady=5)
    entries[param] = entry

start_button = tk.Button(root, text="Start", command=on_start)
start_button.grid(row=len(params), column=0, columnspan=2, pady=10)

root.mainloop()
