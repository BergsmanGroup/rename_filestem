# Rename Filestems

A small desktop utility for finding and renaming text within file stems. It uses
Python's built-in Tkinter interface and does not require third-party packages.

## Run

From this directory, run:

```powershell
python app.py
```

Choose **Browse...** to select either a directory (including its subdirectories)
or individual files. When individual files are selected, files with the same
stem under their common parent directory are included too. Enter the text to
find and click **Find**. The directory menu filters the matches by directory;
choose one or more files in the list and review the preview before clicking
**Replace**. Matching is case-sensitive and literal, and file extensions are
preserved. Existing destination files are never overwritten.

The `config.json` file controls whether each text field offers existing file
stems as autofill suggestions. Find autofill is enabled by default; replace
autofill is disabled.
