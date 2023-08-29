#!/bin/env python3
import sys
import os
import shutil
import json
import uuid
import random


def read_json():
    with open("./src/pages/pepe.json", "r") as fp:
        return json.load(fp)


def write_json(data):
    with open("./src/pages/pepe.json", "w") as fp:
        json.dump(data, fp, indent=2)


def modify_json(file, tags):
    name = os.path.splitext(os.path.basename(file))[0]
    _, ext = os.path.splitext(file)
    ext = ext[1:]

    data: list = read_json()

    rnd_index = random.randint(0, 3)
    data.insert(rnd_index, {"id": name, "tags": tags, "extension": ext})
    write_json(data)


def move(file) -> str:
    file_name = uuid.uuid4()
    _, ext = os.path.splitext(file)
    ext = ext[1:]
    new_file = f"./public/{file_name}.{ext}"
    shutil.move(file, new_file)
    print("moved file:", new_file)
    return new_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python util.py <file_name> <tags>")
    else:
        file = sys.argv[1]
        tags = sys.argv[2:]
        new_file = move(file)
        modify_json(new_file, tags)
