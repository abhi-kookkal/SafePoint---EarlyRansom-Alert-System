# save as simulate_ransom.py (run from anywhere)
import os, time, pathlib
target = pathlib.Path.home() / "Documents" / "Canaries"
target.mkdir(parents=True, exist_ok=True)

# create some dummy files
for i in range(30):
    (target / f"doc_{i}.txt").write_text("normal content\n")

time.sleep(3)
# "encrypt" by overwriting fast with random-ish content
for i in range(30):
    p = target / f"doc_{i}.txt"
    p.write_text("ENCRYPTED_" * 200)
    time.sleep(0.05)
print("done")
