import pandas as pd
from pathlib import Path

script_dir = Path(__file__).resolve().parent

df = pd.read_json(script_dir / "posts.jsonl", orient="records", lines=True)
#print(df.shape)

print(df['author'].value_counts())