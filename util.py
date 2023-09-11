#!/bin/env python3
from os.path import isdir
import sys
import os
import shutil
import json
import uuid
import random
import subprocess


def read_json():
    with open("./src/pages/pepe.json", "r") as fp:
        return json.load(fp)


def write_json(data):
    with open("./src/pages/pepe.json", "w") as fp:
        json.dump(data, fp, indent=2)


def modify_json(file, tags):
    name = os.path.splitext(os.path.basename(file))[0]
    _, ext = os.path.splitext(file)
    ext = ext[1:].lower()

    data: list = read_json()

    rnd_index = random.randint(0, len(data))
    data.insert(rnd_index, {"id": name, "tags": tags, "extension": ext})
    write_json(data)


def move(file) -> str:
    file_name = uuid.uuid4()
    _, ext = os.path.splitext(file)
    ext = ext[1:].lower()
    new_file = f"./public/{file_name}.{ext}"
    shutil.move(file, new_file)
    print("moved file:", file, "->", new_file)
    return new_file


def folder(path):
    files = os.listdir(path)

    exts = [".jpg", ".jpeg", ".png", ".gif", ".mp4"]
    files = [
        file
        for file in files
        if os.path.isfile(os.path.join(path, file))
        and any(file.lower().endswith(ext) for ext in exts)
    ]

    for file in files:
        print("file:", os.path.join(path, file))
        subprocess.run(f"chafa -d 2 --size 69 {os.path.join(path, file)}", shell=True)
        add = input("add: ")
        if add == "y":
            tags = input("tags: ")
            new_file = move(os.path.join(path, file))
            modify_json(new_file, [tag.strip() for tag in tags.split(",")])
        elif add == "n":
            print("removed file:", os.path.join(path, file))
            os.remove(os.path.join(path, file))
        else:
            print("incorrect input")
            break


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        if os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]):
            folder(sys.argv[1])
        else:
            print("Usage: python util.py <file_name> <tags>")
    else:
        file = sys.argv[1]
        tags = sys.argv[2:]
        new_file = move(file)
        modify_json(new_file, tags)
