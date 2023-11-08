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
    return text.strip().replace('&','\\&').replace('%', '\\%')

# clean BeautifulSoup item for use in LaTeX
def clean_soup(item):
    # clean up most HTML tags
    text = str(item)
    text = text.replace('<p>','').replace('</p>','')
    text = text.replace('<li>','').replace('</li>','')
    text = text.replace('<ul>','').replace('</ul>','')
    text = text.replace('<em>','\\textit{').replace('</em>','}')
    text = text.replace('<strong>','\\textbf{').replace('</strong>','}')
    text = text.replace('<b>','\\textbf{').replace('</b>','}')
    text = text.replace('<h2>','\\subsection{').replace('</h2>','}')
    text = text.replace('<h3>','\\subsection{').replace('</h3>','}')
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

# write a list as \itemize
def write_list(f, item):
    f.write('\\begin{itemize}\n')
    for item in item.find_all('li'):
        f.write('\item %s\n' % clean_soup(item))
    f.write('\\end{itemize}\n')

# write a general page (some pages might need manual parsing)
def write_general_page(f, soup, tag='div', class_='field'):
    if isinstance(soup, str): # actually a URL, not a soup
        url = soup; soup = scrape(url); write_scraped_from(f, url)
    if tag is None:
        children = list(soup)
    else:
        children = soup.find_all(tag, class_=class_)[0]
    for child in children:
        if child.name == 'p':
            f.write('%s\n\n' % clean_soup(child))
        elif child.name in {'h2', 'h3'}:
            f.write('\\subsection{%s}\n' % clean(child.text))
        elif child.name == 'ul':
            write_list(f, child)
        elif child.name == 'div':
            write_general_page(f, child, tag=None, class_=None)
        elif child.name is not None:
            raise ValueError("Unsupported HTML tag: %s\n%s" % (child.name, child))

# write header
def write_header(f):
    f.write('\\documentclass[12pt,titlepage]{book}\n\n')

    # packages
    f.write('% packages\n')
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
    f.write('% Introduction\n')
    f.write('\\chapter{Introduction}\n\n')

    # Mission Statement
    url = 'https://bioinformatics.ucsd.edu/node/1'
    f.write('% Mission Statement\n')
    f.write('\\section{Mission Statement}\n')
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
    f.write('% Curriculum\n')
    f.write('\\chapter{Curriculum}\n\n')

    # Curriculum Overview
    url = 'https://bioinformatics.ucsd.edu/curriculum'
    f.write('% Curriculum Overview\n')
    f.write('\\section{Curriculum Overview}\n')
    write_general_page(f, url)

# write Requirements
def write_requirements(f):
    f.write('% Requirements\n')
    f.write('\\chapter{Requirements}\n\n')

    # Seminars, Informal Courses, Group Meetings, Symposia, and Journal Clubs
    url = 'https://bioinformatics.ucsd.edu/node/24'
    f.write('% Seminars, Informal Courses, Group Meetings, Symposia, and Journal Clubs\n')
    f.write('\\section{Seminars, Informal Courses, Group Meetings, Symposia, and Journal Clubs}\n')
    write_general_page(f, url)

    # Teaching Requirement
    url = 'https://bioinformatics.ucsd.edu/node/25'
    f.write('% Teaching Requirement\n')
    f.write('\\section{Teaching Requirement}\n')
    write_general_page(f, url)

    # Qualifying Exam
    url = 'https://bioinformatics.ucsd.edu/node/37'
    f.write('% Qualifying Exam\n')
    f.write('\\section{Qualifying Exam}\n')
    write_general_page(f, url)

    # Doctoral Committee
    url = 'https://bioinformatics.ucsd.edu/node/17757'
    f.write('% Doctoral Committee\n')
    f.write('\\section{Doctoral Committee}\n')
    write_general_page(f, url)

    # Advancement to Ph.D. Candidacy
    url = 'https://bioinformatics.ucsd.edu/node/39'
    f.write('% Advancement to Ph.D. Candidacy\n')
    f.write('\\section{Advancement to Ph.D. Candidacy}\n')
    write_general_page(f, url)

# write Policies
def write_policies(f):
    f.write('% Policies\n')
    f.write('\\chapter{Policies}\n\n')

    # Advisor/Student Relationship
    url = 'https://bioinformatics.ucsd.edu/index.php/node/43'
    f.write('% Advisor/Student Relationship\n')
    f.write('\\section{Advisor/Student Relationship}\n')
    write_general_page(f, url)

# write footer
def write_footer(f):
    f.write('\\end{document}\n')

# main program
if __name__ == "__main__":
    f = open('main.tex', 'w')
    write_header(f)
    write_about(f)
    write_curriculum(f)
    write_requirements(f)
    write_policies(f)
    write_footer(f)
    f.close()
