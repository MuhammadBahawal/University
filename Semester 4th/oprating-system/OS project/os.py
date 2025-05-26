import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from enum import Enum
import random
import matplotlib.pyplot as plt

class MappingType(Enum):
    DIRECT = "Direct Mapping"
    FULLY_ASSOCIATIVE = "Fully Associative"
    SET_ASSOCIATIVE = "Set Associative"

class ReplacementPolicy(Enum):
    RANDOM = "Random"
    FIFO = "FIFO"
    LRU = "LRU"

class CacheSimulator:
    def __init__(self, config):
        self.sequence = config["sequence"]
        self.cache_size = config["cache_size"]
        self.mapping = config["mapping"]
        self.associativity = config.get("associativity", None)
        self.hits = 0
        self.misses = 0
        self.history = []

        if self.mapping == MappingType.SET_ASSOCIATIVE:
            self.num_sets = self.cache_size // self.associativity
            self.cache = [[] for _ in range(self.num_sets)]
            self.fifo_queues = {i: [] for i in range(self.num_sets)}
            self.lru_stacks = {i: [] for i in range(self.num_sets)}
        else:
            self.cache = []
            self.fifo_queue = []
            self.lru_stack = []

    def run(self, ask_policy_callback):
        for address in self.sequence:
            if self.mapping == MappingType.DIRECT:
                self._direct_mapping(address)
            elif self.mapping == MappingType.FULLY_ASSOCIATIVE:
                self._fully_associative(address, ask_policy_callback)
            elif self.mapping == MappingType.SET_ASSOCIATIVE:
                self._set_associative(address, ask_policy_callback)

        return {
            "hits": self.hits,
            "misses": self.misses,
            "cache": self.cache,
            "history": self.history,
            "sequence": self.sequence
        }

    def _direct_mapping(self, address):
        if len(self.cache) < self.cache_size:
            self.cache.extend([None] * (self.cache_size - len(self.cache)))

        index = address % self.cache_size
        if self.cache[index] == address:
            self.hits += 1
            self.history.append('H')
        else:
            self.cache[index] = address
            self.misses += 1
            self.history.append('M')

    def _fully_associative(self, address, ask_policy_callback):
        if address in self.cache:
            self.hits += 1
            self.history.append('H')
        else:
            self.misses += 1
            self.history.append('M')
            if len(self.cache) < self.cache_size:
                self.cache.append(address)
            else:
                policy = ask_policy_callback()
                evict_index = self._get_eviction_index(policy, self.cache, self.fifo_queue, self.lru_stack)
                self.cache[evict_index] = address

    def _set_associative(self, address, ask_policy_callback):
        set_index = address % self.num_sets
        cache_set = self.cache[set_index]
        if address in cache_set:
            self.hits += 1
            self.history.append('H')
        else:
            self.misses += 1
            self.history.append('M')
            if len(cache_set) < self.associativity:
                cache_set.append(address)
            else:
                policy = ask_policy_callback()
                fifo = self.fifo_queues[set_index]
                lru = self.lru_stacks[set_index]
                evict_index = self._get_eviction_index(policy, cache_set, fifo, lru)
                cache_set[evict_index] = address

    def _get_eviction_index(self, policy, cache_set, fifo, lru):
        if policy == ReplacementPolicy.RANDOM:
            return random.randint(0, len(cache_set) - 1)
        elif policy == ReplacementPolicy.FIFO:
            if not fifo:
                fifo.extend(cache_set)
            victim = fifo.pop(0)
            return cache_set.index(victim)
        elif policy == ReplacementPolicy.LRU:
            if not lru:
                lru.extend(cache_set)
            victim = lru.pop(0)
            return cache_set.index(victim)
        return 0

class CacheSimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Cache Memory Simulator")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

        ttk.Label(root, text="Cache Memory Management Simulator", style="Header.TLabel").pack(pady=10)

        input_frame = ttk.Frame(root)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="Memory Access Sequence (comma-separated):").grid(row=0, column=0, sticky="w")
        self.seq_entry = ttk.Entry(input_frame, width=50)
        self.seq_entry.grid(row=1, column=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Cache Size:").grid(row=2, column=0, sticky="w")
        self.cache_size_entry = ttk.Entry(input_frame, width=20)
        self.cache_size_entry.grid(row=3, column=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Mapping Type:").grid(row=4, column=0, sticky="w")
        self.mapping_var = tk.StringVar(value="DIRECT")
        self.mapping_menu = ttk.Combobox(input_frame, textvariable=self.mapping_var, state="readonly",
                                         values=[m.name for m in MappingType])
        self.mapping_menu.grid(row=5, column=0, padx=5, pady=5)

        self.run_btn = ttk.Button(root, text="Run Simulation", command=self.run_simulation)
        self.run_btn.pack(pady=10)

        search_frame = ttk.Frame(root)
        search_frame.pack(pady=5)

        ttk.Label(search_frame, text="Search Memory Address in Cache:").grid(row=0, column=0, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_btn = ttk.Button(search_frame, text="Search in Cache", command=self.search_in_cache)
        self.search_btn.grid(row=0, column=2, padx=5)

        self.graph_btn = ttk.Button(root, text="Show Graph", command=self.show_graph)
        self.graph_btn.pack(pady=10)

        output_frame = ttk.Frame(root)
        output_frame.pack(fill="both", expand=True, padx=10)

        self.output = tk.Text(output_frame, wrap="word", height=12, font=("Courier New", 10))
        scrollbar = ttk.Scrollbar(output_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.last_result = None

    def ask_replacement_policy(self):
        policy = simpledialog.askstring("Choose Replacement Policy", "Cache Miss! Choose policy (RANDOM, FIFO, LRU):")
        if policy:
            policy = policy.strip().upper()
            if policy in ReplacementPolicy.__members__:
                return ReplacementPolicy[policy]
        return ReplacementPolicy.RANDOM

    def run_simulation(self):
        try:
            sequence = [int(x.strip()) for x in self.seq_entry.get().split(",")]
            cache_size = int(self.cache_size_entry.get())
            mapping = MappingType[self.mapping_var.get()]
            config = {
                "sequence": sequence,
                "cache_size": cache_size,
                "mapping": mapping
            }

            if mapping == MappingType.SET_ASSOCIATIVE:
                assoc = simpledialog.askinteger("Associativity", "Enter associativity (e.g., 2):",
                                                minvalue=1, maxvalue=cache_size)
                config["associativity"] = assoc

            simulator = CacheSimulator(config)
            result = simulator.run(self.ask_replacement_policy)
            self.last_result = result

            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, f"\n✔ Total Hits: {result['hits']}\n")
            self.output.insert(tk.END, f"✖ Total Misses: {result['misses']}\n")
            self.output.insert(tk.END, "\n🗃 Final Cache State:\n")

            if mapping == MappingType.SET_ASSOCIATIVE:
                for i, s in enumerate(result["cache"]):
                    self.output.insert(tk.END, f"Set {i}: {s}\n")
            else:
                self.output.insert(tk.END, f"{result['cache']}\n")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_in_cache(self):
        if not self.last_result:
            messagebox.showinfo("Info", "Please run the simulation first.")
            return

        try:
            search_address = int(self.search_entry.get().strip())
            mapping = MappingType[self.mapping_var.get()]
            found = False

            if mapping == MappingType.SET_ASSOCIATIVE:
                for i, cache_set in enumerate(self.last_result["cache"]):
                    if search_address in cache_set:
                        found = True
                        messagebox.showinfo("Found", f"Address {search_address} found in Set {i}.")
                        return
            else:
                if search_address in self.last_result["cache"]:
                    found = True
                    index = self.last_result["cache"].index(search_address)
                    messagebox.showinfo("Found", f"Address {search_address} found at Index {index}.")

            if not found:
                messagebox.showinfo("Not Found", f"Address {search_address} not found in cache.")

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer address.")

    def show_graph(self):
        if not self.last_result:
            messagebox.showinfo("Info", "Please run the simulation first.")
            return

        hits = self.last_result["hits"]
        misses = self.last_result["misses"]
        history = self.last_result["history"]
        sequence = self.last_result["sequence"]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
        fig.suptitle('Cache Simulation Results')

        # Pie chart for total hits vs misses
        labels = ['Hits', 'Misses']
        sizes = [hits, misses]
        colors = ['green', 'red']
        explode = (0.1, 0)  # explode hits slice for emphasis

        ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.set_title("Total Hits vs Misses")

        # Per access hit/miss visualization using colored dots
        colors = ['green' if status == 'H' else 'red' for status in history]
        ax2.scatter(range(len(history)), [1]*len(history), c=colors, s=100)

        for i, addr in enumerate(sequence):
            ax2.text(i, 1.05, str(addr), ha='center', va='bottom', fontsize=8)

        ax2.set_title("Per Access Hit/Miss Visualization")
        ax2.set_yticks([])
        ax2.set_xticks(range(len(history)))
        ax2.set_xticklabels(range(1, len(history)+1))
        ax2.set_xlim(-0.5, len(history)-0.5)
        ax2.set_ylim(0.8, 1.2)

        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = CacheSimGUI(root)
    root.mainloop()
