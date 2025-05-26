import matplotlib.pyplot as plt
import datetime
import csv
import os

# --- Configuration and Input ---
def get_input_data():
    config = {
        "cache_size": 4,
        "block_size": 1,
        "mapping": "Direct",  # or "Fully-Associative", "Set-Associative"
        "replacement_policy": "LRU"  # or "FIFO"
    }
    memory_accesses = [1, 2, 3, 2, 4, 1, 5, 6, 2, 1, 7, 8]
    return config, memory_accesses

# --- Cache Block and Set Classes ---
class CacheBlock:
    def __init__(self, tag):
        self.tag = tag

class CacheSet:
    def __init__(self, associativity):
        self.blocks = []
        self.associativity = associativity

    def is_full(self):
        return len(self.blocks) >= self.associativity

    def find_block(self, tag):
        for block in self.blocks:
            if block.tag == tag:
                return block
        return None

    def remove_block(self):
        return self.blocks.pop(0)

    def add_block(self, block):
        self.blocks.append(block)

# --- Cache Class (Handles Mapping) ---
class Cache:
    def __init__(self, config):
        self.mapping = config["mapping"]
        self.replacement_policy = config["replacement_policy"]
        self.cache_size = config["cache_size"]
        self.sets = []

        if self.mapping == "Direct":
            self.sets = [CacheSet(1) for _ in range(self.cache_size)]
        elif self.mapping == "Fully-Associative":
            self.sets = [CacheSet(self.cache_size)]
        elif self.mapping == "Set-Associative":
            num_sets = 2
            associativity = self.cache_size // num_sets
            self.sets = [CacheSet(associativity) for _ in range(num_sets)]

    def get_set_index(self, address):
        if self.mapping == "Direct":
            return address % self.cache_size
        elif self.mapping == "Set-Associative":
            return address % len(self.sets)
        else:  # Fully-Associative
            return 0

# --- Replacement Policies ---
def apply_lru_policy(cache_set, tag):
    for i, block in enumerate(cache_set.blocks):
        if block.tag == tag:
            block = cache_set.blocks.pop(i)
            cache_set.blocks.append(block)
            break

def apply_fifo_policy(cache_set):
    return cache_set.remove_block()

# --- Simulation Engine ---
class CacheSimulator:
    def __init__(self, config):
        self.config = config
        self.cache = Cache(config)
        self.hits = 0
        self.misses = 0
        self.access_log = []

    def run(self, memory_accesses):
        for addr in memory_accesses:
            set_index = self.cache.get_set_index(addr)
            cache_set = self.cache.sets[set_index]
            block = cache_set.find_block(addr)

            if block:
                self.hits += 1
                if self.config["replacement_policy"] == "LRU":
                    apply_lru_policy(cache_set, addr)
                status = "HIT"
            else:
                self.misses += 1
                if cache_set.is_full():
                    if self.config["replacement_policy"] == "FIFO":
                        apply_fifo_policy(cache_set)
                    elif self.config["replacement_policy"] == "LRU":
                        cache_set.remove_block()
                cache_set.add_block(CacheBlock(addr))
                status = "MISS"

            self.access_log.append((addr, status))

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": len(memory_accesses),
            "log": self.access_log
        }

# --- Output and Reporting ---
class OutputHandler:
    @staticmethod
    def print_summary(results):
        print("\n--- Cache Simulation Summary ---")
        print(f"Total Accesses: {results['total']}")
        print(f"Hits: {results['hits']}")
        print(f"Misses: {results['misses']}")
        print(f"Hit Rate: {results['hits'] / results['total']:.2f}")
        print(f"Miss Rate: {results['misses'] / results['total']:.2f}")

    @staticmethod
    def save_report(results, filename="output/simulation_report.txt"):
        os.makedirs("output", exist_ok=True)
        with open(filename, "w") as f:
            f.write("--- Cache Simulation Report ---\n")
            for addr, status in results["log"]:
                f.write(f"Address: {addr} => {status}\n")
            f.write(f"\nTotal: {results['total']}\n")
            f.write(f"Hits: {results['hits']}, Misses: {results['misses']}\n")
            f.write(f"Hit Rate: {results['hits'] / results['total']:.2f}\n")

# --- Graph Plotting ---
def plot_graph(results, csv_path="output/graph_data.csv", image_path="output/graph_output.png"):
    os.makedirs("output", exist_ok=True)
    with open(csv_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Hits", "Misses"])
        writer.writerow([results["hits"], results["misses"]])

    labels = ['Hits', 'Misses']
    sizes = [results["hits"], results["misses"]]
    colors = ['green', 'red']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title("Cache Hit vs Miss")
    plt.savefig(image_path)
    plt.close()

# --- Optional Debug Logger ---
def log(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs("output", exist_ok=True)
    with open("output/debug_log.txt", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# --- Main Program ---
def main():
    config, memory_accesses = get_input_data()
    simulator = CacheSimulator(config)
    results = simulator.run(memory_accesses)
    OutputHandler.print_summary(results)
    OutputHandler.save_report(results)
    plot_graph(results)

if __name__ == "__main__":
    main()
