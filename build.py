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
    return text.replace('&','\\&')

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
    f.write("\\textit{Scraped from: \\href{%s}{%s}}\\\\~\\\\\n\n" % (url,url))
    soup = scrape(url)
    for paragraph in soup.find_all('div', class_='field')[0].find_all('p'):
        f.write('%s\n\n' % clean(paragraph.text))

# write footer
def write_footer(f):
    f.write('\\end{document}\n')

# main program
if __name__ == "__main__":
    f = open('main.tex', 'w')
    write_header(f)
    write_introduction(f)
    write_footer(f)
    f.close()
