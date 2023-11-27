import cson

def load_config(class_):
    with open("config.cson", "r", encoding="utf-8") as f:
        return class_(**cson.load(f))
