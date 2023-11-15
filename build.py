#! /usr/bin/env python3
'''
Build BISB/BMI handbook PDF by scraping BISB website, creating LaTeX file, and compiling to PDF.
'''

# imports
from bs4 import BeautifulSoup, NavigableString
from urllib.request import urlopen

# constants
BISB_BASE_URL = 'https://bioinformatics.ucsd.edu'

# scrape a given URL
def scrape(url):
    return BeautifulSoup(urlopen(url).read(), 'html.parser')

# clean text for use in LaTeX (e.g. replace "&" with "\&")
def clean(text):
    text = text.strip()
    text = text.replace('&', '\\&')
    text = text.replace('\\&amp;', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\$')
    text = text.replace('[', '{[')
    text = text.replace(']', ']}')
    return text

# clean BeautifulSoup item for use in LaTeX
def clean_soup(item):
    # clean up most HTML tags
    text = str(item)
    text = text.replace('<p>','').replace('</p>','')
    text = text.replace('<li>','').replace('</li>','')
    text = text.replace('<ul>','').replace('</ul>','')
    text = text.replace('<em>','\\textit{').replace('</em>','}')
    text = text.replace('<i>','\\textit{').replace('</i>','}')
    text = text.replace('<strong>','\\textbf{').replace('</strong>','}')
    text = text.replace('<b>','\\textbf{').replace('</b>','}')
    text = text.replace('<h2>','\\subsection{').replace('</h2>','}')
    text = text.replace('<h3>','\\subsection{').replace('</h3>','}')
    text = text.replace('<h4>','\\subsubsection{').replace('</h4>','}')
    text = text.replace('<br/><br/>','\n\n')
    text = text.replace('<br/>',' ')

    # handle hyperlinks (DO THIS LAST!)
    if '<a href' in text:
        parts = text.split('<a href="')
        for i in range(1, len(parts)):
            if parts[i].startswith('/'):
                parts[i] = '%s%s' % (BISB_BASE_URL, parts[i])
        text = '\\href{'.join(parts).replace('">','}{').replace('</a>','}').replace('" target="_blank','')

    # finish up
    if '<' in text and '>' in text:
        raise ValueError("Need to finish parsing HTML:\n%s" % text)
    return clean(text)

# write "Scraped From:" text
def write_scraped_from(f, url):
    f.write("\\textit{Scraped from: \\href{%s}{%s}}\\\\\n\n" % (url, url))

# write chapter/section header
def write_header(f, title, header_type):
    if header_type not in {'chapter', 'section'}:
        raise ValueError("Invalid header type: %s" % header_type)
    f.write('%% %s\n' % title)
    f.write('\\%s{%s}\n\n' % (header_type, title))

# write a list as \itemize
def write_list(f, item):
    f.write('\\begin{itemize}\n')
    for item in item.find_all('li'):
        f.write('\item %s\n' % clean_soup(item))
    f.write('\\end{itemize}\n')

# write a table as \tabular
def write_table(f, item):
    contents = [[clean_soup(list(cell)[0]) for cell in row.find_all('th')] + [clean_soup(list(cell)[0]) for cell in row.find_all('td')] for row in item.find_all('tr')]
    num_cols = max(len(row) for row in contents)
    for i in range(len(contents)):
        contents[i] += ['']*(num_cols-len(contents[i]))
    f.write('\\begin{table}[ht]\n')
    f.write('\\centering\n')
    f.write('\\begin{adjustbox}{width=\\textwidth}\n')
    f.write('\\begin{tabular}{ %s }\n' % ' '.join(['l']*num_cols))
    for row in contents:
        f.write('%s\\\\\n' % (' & '.join(row)))
    f.write('\\end{tabular}\n')
    f.write('\\end{adjustbox}\n')
    f.write('\\end{table}\n')

# write a general page (some pages might need manual parsing)
def write_general_page(f, soup, tag='div', class_='field'):
    if isinstance(soup, str): # actually a URL, not a soup
        url = soup; soup = scrape(url); write_scraped_from(f, url)
    if tag is None:
        children = list(soup)
    else:
        children = soup.find_all(tag, class_=class_)[0]
    for child in children:
        if child.name in {'p', 'h4'}:
            f.write('%s\n\n' % clean_soup(child))
        elif child.name in {'h2', 'h3'}:
            f.write('\\subsection{%s}\n' % clean(child.text))
        elif child.name == 'ul':
            write_list(f, child)
        elif child.name == 'div':
            write_general_page(f, child, tag=None, class_=None)
        elif child.name == 'table':
            write_table(f, child)
        elif child.name == 'blockquote':
            f.write('\\begin{displayquote}\n')
            write_general_page(f, child, tag=None, class_=None)
            f.write('\\end{displayquote}\n')
        elif child.name is not None:
            raise ValueError("Unsupported HTML tag: %s\n%s" % (child.name, child))

# write document header
def write_document_header(f):
    f.write('\\documentclass[12pt,titlepage]{book}\n\n')

    # packages
    f.write('% packages\n')
    f.write('\\usepackage{adjustbox}\n')
    f.write('\\usepackage{csquotes}\n')
    f.write('\\usepackage{hyperref}\n')
    f.write('\\usepackage[pagestyles]{titlesec}\n')
    f.write('\n')

    # title page properties
    f.write('% title page properties\n')
    f.write('\\title{\\textbf{Bioinformatics \\& Systems Biology}\\\\Graduate Student Handbook}\n')
    f.write('\\date{Compiled: \\today\\\\~\\\\This unofficial PDF is automatically generated.\\\\~\\\\Information on the BISB website is the authority.\\\\\\href{https://bioinformatics.ucsd.edu}{bioinformatics.ucsd.edu}}\n')
    f.write('\n')

    # remove "Chapter #" from chapter titles and numbers from section titles
    f.write('% fix chapter/section titles\n')
    f.write('\\titleformat{\\chapter}[display]{\\normalfont\\bfseries}{}{0pt}{\\Huge}\n')
    f.write('\\newpagestyle{mystyle}\n')
    f.write('{\\sethead[\\thepage][][\\textit{\\chaptertitle}]{}{}{\\thepage}}\n')
    f.write('\\pagestyle{mystyle}\n')
    f.write('\\titleformat{\\section}{\\normalfont\\Large\\bfseries}{}{0pt}{}\n')
    f.write('\\titleformat{\\subsection}{\\normalfont\\large\\bfseries}{}{0pt}{}\n')
    f.write('\n')

    # start main document
    f.write('% start main document\n')
    f.write('\\begin{document}\n')
    f.write('\\maketitle\n')
    f.write('\\begingroup\\let\\cleardoublepage\\clearpage\\tableofcontents\\endgroup\n')
    f.write('\n')

# write About
def write_about(f):
    write_header(f, 'Introduction', 'chapter')

    # Mission Statement
    write_header(f, 'Mission Statement', 'section')
    url = 'https://bioinformatics.ucsd.edu/node/1'
    write_general_page(f, url)

    # Graduate Financial Support
    write_header(f, 'Graduate Financial Support', 'section')
    url = 'https://bioinformatics.ucsd.edu/node/18'
    write_general_page(f, url)

    # Graduate Program Committees
    url = 'https://bioinformatics.ucsd.edu/node/3'
    f.write('% Graduate Program Committees\n')
    f.write('\\section{Graduate Program Committees}\n')
    write_scraped_from(f, url)
    soup = scrape(url)
    for committee in soup.find_all('div', class_='cwp-chrome07'):
        f.write('\n\\subsection{%s}\n' % clean_soup(committee.find_all('h2')[0].text))
        paragraphs = committee.find_all('p')
        if len(paragraphs) != 0:
            f.write('\\subsubsection*{Duties}\n')
            f.write('\\begin{itemize}\n')
            for paragraph in committee.find_all('p'):
                for line in paragraph.text.splitlines():
                    f.write('\item %s\n' % clean_soup(line))
            f.write('\\end{itemize}\n')
        f.write('\\subsubsection*{Members}\n')
        write_list(f, committee)
    f.write('\n')

# write Curriculum
def write_curriculum(f):
    write_header(f, 'Curriculum', 'chapter')
    sections = [
        ('Curriculum Overview', 'https://bioinformatics.ucsd.edu/curriculum'),
        ('Course Requirements', 'https://bioinformatics.ucsd.edu/node/104'),
    ]
    for title, url in sections:
        write_header(f, title, 'section')
        write_general_page(f, url)

# write Research Rotations
def write_rotations(f):
     write_header(f, 'Research Rotations', 'chapter')
     url = 'https://bioinformatics.ucsd.edu/node/99'
     write_general_page(f, url)

# write Requirements
def write_requirements(f):
    write_header(f, 'Requirements', 'chapter')
    sections = [
        ('Seminars, etc.', 'https://bioinformatics.ucsd.edu/node/24'),
        ('Teaching Requirement', 'https://bioinformatics.ucsd.edu/node/25'),
        ('Qualifying Exam', 'https://bioinformatics.ucsd.edu/node/37'),
        ('Doctoral Committee', 'https://bioinformatics.ucsd.edu/node/17757'),
        ('Ph.D. Advancement', 'https://bioinformatics.ucsd.edu/node/39'),
        ('Ph.D. Advancement Instructions', 'https://bioinformatics.ucsd.edu/node/40'),
        ('Thesis or Dissertation', 'https://bioinformatics.ucsd.edu/node/38'),
        ('Dissertation Defense', 'https://bioinformatics.ucsd.edu/node/41'),
        ('Individual Development Plan (IDP)', 'https://bioinformatics.ucsd.edu/node/1086'),
    ]
    for title, url in sections:
        write_header(f, title, 'section')
        write_general_page(f, url)

# write Policies
def write_policies(f):
    write_header(f, 'Policies', 'chapter')
    sections = [
        ('Advisor/Student Relationship', 'https://bioinformatics.ucsd.edu/index.php/node/43'),
        ('Internships', 'https://bioinformatics.ucsd.edu/node/186'),
        ('How to Cite Training Grant', 'https://bioinformatics.ucsd.edu/node/1023'),
        ('Curriculum Petitions FAQ', 'https://bioinformatics.ucsd.edu/node/1034'),
        ('Grades FAQ', 'https://bioinformatics.ucsd.edu/node/1085'),
        ('Exam Scheduling FAQ', 'https://bioinformatics.ucsd.edu/node/1035'),
    ]
    for title, url in sections:
        write_header(f, title, 'section')
        write_general_page(f, url)

# write footer
def write_footer(f):
    f.write('\\end{document}\n')

# main program
if __name__ == "__main__":
    f = open('main.tex', 'w')
    write_document_header(f)
    write_about(f)
    write_curriculum(f)
    write_rotations(f)
    write_requirements(f)
    write_policies(f)
    write_footer(f)
    f.close()
