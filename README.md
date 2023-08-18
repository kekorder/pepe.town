# pepe.town

Collecting pepe to build the rarest collection to date.

# adding pepe

1. Before adding your amazing pepe images make sure it's not already in the collection, filter by tags to check if it already exists.
2. Rename your pepe to a uuidv4 (uuidgen command on linux) and make the extension png.
3. Upload the new file to [this](https://github.com/kekorder/pepe.town/tree/master/public) location on github.
4. Now locate the following [file](https://github.com/kekorder/pepe.town/blob/master/src/pages/pepe.json).
5. Add the following lines at the bottom and make sure it is valid json (use this [tool](https://duckduckgo.com/?q=json+validator))

```json
  {
    "id": "", # uuid of the specific file
    "tags": [ # tags you feel are apropriate to the pepe
      "",
      ""
    ]
  },
```
