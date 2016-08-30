# scriv2web

This script exists because I wanted to be able to:

- write in Scrivener in Markdown
- export the outlined structure into a website with left sidebar contents
- push the website to git (for access through GitHub pages)

It began by reading [Academic writing with Scrivener, Zotero, Pandoc and Marked 2](https://github.com/davepwsmith/academic-scrivener-howto) by David Smith. It didn't take long to set up the system he describes, so I was able to write in pandoc Markdown (with Biblatex references from Zotero) and compile into a final Word document or PDF for distribution. However, I kept looking for a way to translate the structure of the Zotero project into a website without needing to compile it all into one giant document, but I was never able to find anything. So I wrote this.

### Requirements

It expects you to be creating a Python 2.7 virtual environment to install requirements.txt. It uses _textutil_ to convert .rtf to plain text, which I believe is part of OSX. (If not, it wouldn't be hard to rewrite that part to use another conversion). You'll need to have already followed David Smith's guide above: installed Pandoc and, ideally, a citation style (from [https://github.com/citation-style-language/styles](https://github.com/citation-style-language/styles)), and have set up Zotero to autoexport a Biblatex bibliography file on changes.

Finally, if you want to export to GitHub (or some other remote repository) you'll need to initialize a repo in a directory and set a remote. Make sure you've configured it so you can run commands without needing to authenticate interactively (like providing SSH keys or something).

### Setup/Configuration

```
git clone https://github.com/seandockray/scriv2web.git
cd scriv2web
virtualenv venv
pip install -r requirements.txt
./publish.py -i /path/to/Project.scriv -o /path/to/output_directory  -b /path/to/biblatex/bibliography_file.bib -c /path/to/citation/style.csl -r git_remote_name
```

-i and -o are required, the rest are optional. 
