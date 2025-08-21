# save as simulate_ransom.py (run from anywhere)
import os, time, pathlib
target = pathlib.Path.home() / "Documents" / "Canaries"
target.mkdir(parents=True, exist_ok=True)

# create some dummy files
for i in range(30):
    (target / f"doc_{i}.txt").write_text("normal content\n")

time.sleep(30)
# "encrypt" by overwriting fast with random-ish content
import os
for i in range(30):
    p = target / f"doc_{i}.txt"
    # Write 2000 random bytes to simulate high-entropy ransomware encryption
    with open(p, "wb") as f:
        f.write(os.urandom(2000))
    time.sleep(0.05)
print("done")
