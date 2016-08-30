#!venv/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import re
import shutil
from argparse import ArgumentParser
import xmltodict
from subprocess import call

doc_map = {}
docs = {}


_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def _slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)

def map_doc(id, title):
    ''' Creates a unique filename for each document based on its title
    The very first document will be set to index.htm '''
    if not doc_map:
        title = 'index'
    if id not in doc_map:
        candidate = "%s.htm" % _slugify(title)
        i = 1
        while candidate in doc_map.values():
            candidate = "%s-%s.htm" % (_slugify(title), i)
            i = i + 1
        doc_map[id] = candidate

def load_docs(dir):
    ''' Loads docs into the list of docs '''
    for f in os.listdir(dir):
        if not f=='docs.checksum':
            id = f.split('.')[0]
            docs[id] = os.path.join(dir, f)

def convert_docs(output_dir, bibliography_file=False, citation_format=False):
    ''' Converts all rtf files to txt using textutil then html using pandoc '''
    dir='./.markdown'
    #shutil.rmtree(output_dir)
    if not os.path.exists(dir):
        os.mkdir(dir)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    for f in os.listdir(output_dir):
        if f.endswith('.htm'):
            os.remove(os.path.join(output_dir, f))
    for id in docs:
        # first convert to markdown
        mdfile = os.path.join(dir, doc_map[id]).replace('.htm','.md')
        outfile = os.path.join(output_dir, doc_map[id])
        call(['textutil','-convert', 'txt', '-output', mdfile, docs[id]])
        # now use pandoc to convert to html
        pandoc_call = ['pandoc', '-s', '-S', '--normalize']
        if bibliography_file:
            pandoc_call.extend(['--bibliography', bibliography_file])
        if citation_format:
            pandoc_call.extend(['--csl', citation_format])
        pandoc_call.extend(['-f', 'markdown', '-t', 'html', '-o', outfile, mdfile])
        call(pandoc_call)
    if os.path.exists(os.path.join(output_dir,dir)):
        shutil.rmtree(os.path.join(output_dir,dir))
    shutil.move(dir, output_dir)


def build_outline(sections):
    ''' Creates a markdown representation of the outline '''
    def _l(id, title):
        if id in docs:
            return '[%s](%s)' % (title, doc_map[id])
        else:
            return title
    def _s(d):
        return '*'
    def process_section(s, depth=0, path=[]):
        content = ""
        if 'IncludeInCompile' in s['MetaData'] and s['MetaData']['IncludeInCompile']:
            map_doc(s['@ID'], s['Title'])
            path.append(s['@ID'])
            content = "%s%s %s\n" % ('\t'*depth, _s(depth),_l(s['@ID'],s['Title']))
            if 'Children' in s:
                if 'Title' in s['Children']['BinderItem']:
                    map_doc(s['Children']['BinderItem']['@ID'], s['Children']['BinderItem']['Title'])
                    path.append(s['Children']['BinderItem']['@ID'])
                    content = content + "%s%s %s\n" % ('\t'*(depth+1), _s(depth+1), _l(s['Children']['BinderItem']['@ID'], s['Children']['BinderItem']['Title']))
                else:
                    for c in s['Children']['BinderItem']:
                        content = content + process_section(c, depth=depth+1, path=path)
            return content

    content = ""
    path = [] # build a linear path through the content
    for section in sections:
        content = content + "%s" % process_section(section, path=path)
    return content, path

def templatize(template, css, dir, nav, path):
    ''' Takes a directory of html files and some navigation and merges them into new pages '''
    def extract_body(html):
        return html.split('<body>',1)[1].split('</body>', 1)[0]
    def name2id(name):
        for id, n in doc_map.iteritems():
            if n==name:
                return id
        return False
    def next(name):
        id = name2id(name)
        b = False
        for p in path:
            if b and p in docs:
                return "<a href='%s'>&rarr; %s</a>" % (doc_map[p], doc_map[p])
            if id==p:
                b = True
        return ''
    def prev(name):
        id = name2id(name)
        b = False
        for p in path:
            if b and id==p and b in docs:
                return "<a href='%s'>%s &larr;</a>" % (doc_map[b], doc_map[b])
            if p in docs:
                b = p
        return ''

    nav_md_file = os.path.join(dir, '_nav.md')
    nav_htm_file = os.path.join(dir, '_nav.htm')
    with open(nav_md_file,'w') as f:
        f.write(nav)
    pandoc_call = ['pandoc', '-s', '-S', '--normalize', '-f', 'markdown', '-t', 'html', '-o', nav_htm_file, nav_md_file]
    call(pandoc_call)
    html = ''
    with open(template, 'r') as f:
        tpl = f.read()
    with open(nav_htm_file, 'r') as f:
        nav_html = extract_body(f.read())
    os.remove(nav_md_file)
    os.remove(nav_htm_file)
    for f in os.listdir(dir):
        if '.htm' in f:
            print 'writing: ', f
            new_html = tpl
            with open(os.path.join(dir, f), 'r') as fr:
                new_html = new_html.replace('%navigation',nav_html).replace('%content',extract_body(fr.read()))
                new_html = "%s<p class='pager'>%s %s</p>" % (new_html, str(prev(f)),str(next(f)))
            with open(os.path.join(dir, f), 'w') as fw:
                fw.write(new_html)
    shutil.copyfile(css, os.path.join(dir, os.path.basename(css)))


def do_git(dir, remote):
    from git import Repo
    print "Pushing to git"
    try:
        repo = Repo(dir)
        """
        for f in os.listdir(dir):
            if not f.startswith('.'):
                repo.index.add([f])
        for f in os.listdir(os.path.join(dir,'.markdown')):
            if not f.startswith('.'):
                repo.index.add([os.path.join('.markdown',f)])
        """
        repo.git.add(A=True)
        #repo.git.add('--all')
        repo.index.commit("Autocommit from scriv2web")
        if remote:
            try:
                repo.remotes[remote].push()
            except:
                print "Couldn't commit to remote named ",remote
        else:
            print "No remote provided"
    except:
        print "No git repository available"

def parse_scrivener_file(fn):
    ''' Parses XML file for an outline '''
    sections = []
    with open(fn,'r') as f:
        d = xmltodict.parse(f.read())
        # These are the different things in the binder
        for items in d['ScrivenerProject']['Binder']['BinderItem']:
            sections.append(items)
    return sections

if __name__=='__main__':
    parser = ArgumentParser()
    parser.add_argument("-i", "--input",
        dest="project_path", default=False, help="Scrivener project file")
    parser.add_argument("-o", "--output",
        dest="output_dir", default='html', help="output directory")
    parser.add_argument("-b", "--bib",
        dest="bibliography", default=False, help="location of pandoc bibliography")
    parser.add_argument("-c", "--csl",
        dest="csl", default=False, help="location of citation format")
    parser.add_argument("-t", "--template",
        dest="template_file", default='template.default', help="location of template file")
    parser.add_argument("-s", "--css",
        dest="css_file", default='default.css', help="location of css file")
    parser.add_argument("-r", "--remote",
        dest="git_remote", default=False, help="name of git remote to push to")
    args = parser.parse_args()
    project_path = args.project_path
    output_dir = args.output_dir
    bibliography = args.bibliography
    template_file = args.template_file
    css_file = args.css_file
    csl = args.csl
    git_remote = args.git_remote
    project_file = False
    project_docs = False
    title = False
    try:
        if os.path.exists(project_path):
            for f in os.listdir(project_path):
                if f.endswith(".scrivx"):
                    title = f.replace('.scrivx','')
                    project_file = os.path.join(project_path, f)
                    project_docs = os.path.join(project_path, 'Files', 'Docs')
                    break
            if not project_file:
                print "There is no Scrivener project in this location"
                sys.exit(0)
        else:
            print "A file does not exist at that location"
            sys.exit(0)
    except:
        print "Enter the path to the Scrivener file you want to publish."
        sys.exit(0)
    # If we've made it this far then the project is there and we can move on to parsing/ publishing
    print "Running Scrivener publisher on ",title
    print "... outputting to ",output_dir
    load_docs(project_docs)
    sections = parse_scrivener_file(project_file)
    outline, path = build_outline(sections)
    convert_docs(output_dir, bibliography_file=bibliography, citation_format=csl)
    templatize( template_file, css_file, output_dir, outline, path)
    do_git(output_dir, remote=git_remote)
