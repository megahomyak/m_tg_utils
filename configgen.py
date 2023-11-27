import cson

with open("config.json", "r", encoding="utf-8") as f:
    cson.load(f)
