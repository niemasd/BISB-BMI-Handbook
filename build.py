#! /usr/bin/env python3
'''
Build BISB/BMI handbook PDF by scraping BISB website, creating LaTeX file, and compiling to PDF.
'''

# imports
from bs4 import BeautifulSoup
from urllib.request import urlopen

# scrape a given URL
def scrape(url):
    return BeautifulSoup(urlopen(url).read(), 'html.parser')

# clean text for use in LaTeX (e.g. replace "&" with "\&")
def clean(text):
    return text.strip().replace('&','\\&')

# write "Scraped From:" text
def write_scraped_from(f, url):
    f.write("\\textit{Scraped from: \\href{%s}{%s}}\\\\\n\n" % (url, url))

# write header
def write_header(f):
    f.write('\\documentclass[12pt,titlepage]{book}\n')

    # packages
    f.write('\\usepackage{hyperref}\n')
    f.write('\\usepackage[pagestyles]{titlesec}\n')

    # title page properties
    f.write('\\title{\\textbf{Bioinformatics \\& Systems Biology}\\\\Graduate Student Handbook}\n')
    f.write('\\date{Compiled: \\today\\\\~\\\\This unofficial PDF is automatically generated.\\\\~\\\\Information on the BISB website is the authority.\\\\\\href{https://bioinformatics.ucsd.edu}{bioinformatics.ucsd.edu}}\n')

    # remove "Chapter #" from chapter titles and numbers from section titles
    f.write('\\titleformat{\\chapter}[display]{\\normalfont\\bfseries}{}{0pt}{\\Huge}\n')
    f.write('\\newpagestyle{mystyle}\n')
    f.write('{\\sethead[\\thepage][][\\textit{\\chaptertitle}]{}{}{\\thepage}}\n')
    f.write('\\pagestyle{mystyle}\n')
    f.write('\\titleformat{\\section}{\\normalfont\\Large\\bfseries}{}{0pt}{}\n')
    f.write('\\titleformat{\\subsection}{\\normalfont\\large\\bfseries}{}{0pt}{}\n')

    # start main document
    f.write('\\begin{document}\n')
    f.write('\\maketitle\n')
    f.write('\\begingroup\\let\\cleardoublepage\\clearpage\\tableofcontents\\endgroup\n')

# write introduction
def write_introduction(f):
    f.write('\\chapter{Introduction}\n')

    # mission statement
    url = 'https://bioinformatics.ucsd.edu/node/1'
    f.write('\\section{Mission Statement}\n')
    write_scraped_from(f, url)
    soup = scrape(url)
    for paragraph in soup.find_all('div', class_='field')[0].find_all('p'):
        f.write('%s\n\n' % clean(paragraph.text))

    # program committees
    url = 'https://bioinformatics.ucsd.edu/node/3'
    f.write('\\section{Graduate Program Committees}\n')
    write_scraped_from(f, url)
    soup = scrape(url)
    for committee in soup.find_all('div', class_='cwp-chrome07'):
        f.write('\\subsection{%s}\n' % clean(committee.find_all('h2')[0].text))
        paragraphs = committee.find_all('p')
        if len(paragraphs) != 0:
            f.write('\\subsubsection*{Duties}\n')
            f.write('\\begin{itemize}\n')
            for paragraph in committee.find_all('p'):
                for line in paragraph.text.splitlines():
                    f.write('\item %s\n' % clean(line))
            f.write('\\end{itemize}\n')
        f.write('\\subsubsection*{Members}\n')
        f.write('\\begin{itemize}\n')
        for member in committee.find_all('li'):
            f.write('\item %s\n' % clean(member.text))
        f.write('\\end{itemize}\n')

# write curriculum
def write_curriculum(f):
    f.write('\\chapter{Curriculum}\n')

    # overview
    url = 'https://bioinformatics.ucsd.edu/curriculum'
    f.write('\\section{Curriculum Overview}\n')
    write_scraped_from(f, url)
    soup = scrape(url)
    for child in soup.find_all('div', class_='field')[0]:
        if child.name == 'p':
            f.write('%s\n\n' % clean(child.text))
        elif child.name == 'h3':
            break # stop before "Program Timeline & Sample Schedules"
        elif child.name == 'ul':
            f.write('\\begin{itemize}\n')
            for item in child.find_all('li'):
                f.write('\item %s\n' % clean(item.text))
            f.write('\\end{itemize}\n')

# write policies
def write_policies(f):
    f.write('\\chapter{Policies}\n')

    # advisor/student relationship
    url = 'https://bioinformatics.ucsd.edu/index.php/node/43'
    f.write('\\section{Advisor/Student Relationship}\n')
    write_scraped_from(f, url)
    soup = scrape(url)
    f.write("TODO\n") # TODO
    #print(soup); exit() # TODO

# write footer
def write_footer(f):
    f.write('\\end{document}\n')

# main program
if __name__ == "__main__":
    f = open('main.tex', 'w')
    write_header(f)
    write_introduction(f)
    write_curriculum(f)
    write_policies(f)
    write_footer(f)
    f.close()
