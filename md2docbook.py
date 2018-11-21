#!/usr/bin/env python3
#
# Copyright (c) 2018 Edward Tomasz Napierala <trasz@FreeBSD.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

#
# XXX: This should get rewritten by someone who actually knows Python.
#

import datetime
import re
import sys
from email.utils import parseaddr
from xml.sax.saxutils import escape

# This part is copy/pasted from en_US.ISO8859-1/htdocs/news/status/report-template.xml
docbook_header = '''\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE report PUBLIC "-//FreeBSD//DTD FreeBSD XML Database for
  Status Report//EN"
  "http://www.FreeBSD.org/XML/share/xml/statusreport.dtd" >

<!-- $FreeBSD: head/en_US.ISO8859-1/htdocs/news/status/report-template.xml 51132 2017-10-19 01:38:11Z bjk $ -->

<!--
     Variables to replace:
     %%START%%     - report month start
     %%STOP%%      - report month end
     %%YEAR%%      - report year
     %%NUM%%       - report issue (first, second, third, fourth)
     %%STARTNEXT%% - report month start
     %%STOPNEXT%%  - report month end
     %%YEARNEXT%%  - next report due year (if different than %%YEAR%%)
     %%DUENEXT%%   - next report due date (i.e., June 6)
-->

<report>
  <date>
    <month>%%START%%-%%STOP%%</month>

    <year>%%YEAR%%</year>
  </date>

  <section>
    <title>Introduction</title>

    <p><strong>This is a draft of the %%START%%&ndash;%%STOP%% %%YEAR%%
      status report.  Please check back after it is finalized, and
      an announcement email is sent to the &os;-Announce mailing
      list.</strong></p>

    <?ignore
    <p>This report covers &os;-related projects between %%START%% and
      %%STOP%% %%YEAR%%.  This is the %%NUM%% of four reports planned for
      %%YEAR%%.</p>

    <p>The %%NUM%% quarter of %%YEAR%% was another productive quarter for
      the &os; project and community. [...]</p>

    <p>Thanks to all the reporters for the excellent work!</p>

    <p>The deadline for submissions covering the period from %%STARTNEXT%%
      to %%STOPNEXT%% %%YEARNEXT%% is %%DUENEXT%%, %%YEARNEXT%%.</p>
     ?>
  </section>

  <category>
    <name>team</name>

    <description>&os; Team Reports</description>

    <p>Entries from the various official and semi-official teams,
      as found in the <a href="&enbase;/administration.html">Administration
        Page</a>.</p>
  </category>

  <category>
    <name>proj</name>

    <description>Projects</description>

    <p>Projects that span multiple categories, from the kernel and userspace
      to the Ports Collection or external projects.</p>
  </category>

  <category>
    <name>kern</name>

    <description>Kernel</description>

    <p>Updates to kernel subsystems/features, driver support,
      filesystems, and more.</p>
  </category>

  <category>
    <name>arch</name>

    <description>Architectures</description>

    <p>Updating platform-specific features and bringing in support
      for new hardware platforms.</p>.
  </category>

  <category>
    <name>bin</name>

    <description>Userland Programs</description>

    <p>Changes affecting the base system and programs in it.</p>
  </category>

  <category>
    <name>ports</name>

    <description>Ports</description>

    <p>Changes affecting the Ports Collection, whether sweeping
      changes that touch most of the tree, or individual ports
      themselves.</p>
  </category>

  <category>
    <name>doc</name>

    <description>Documentation</description>

    <p>Noteworthy changes in the documentation tree or new external
      books/documents.</p>
  </category>

  <category>
    <name>misc</name>

    <description>Miscellaneous</description>

    <p>Objects that defy categorization.</p>
  </category>

  <category>
    <name>third</name>

    <description>Third-Party Projects</description>

    <p>Many projects build upon &os; or incorporate components of
      &os; into their project.  As these projects may be of interest
      to the broader &os; community, we sometimes include brief
      updates submitted by these projects in our quarterly report.
      The &os; project makes no representation as to the accuracy or
      veracity of any claims in these submissions.</p>
  </category>

'''

docbook_footer = '''\
</report>'''

def reflow(s, indent):
    if not s:
        return ''

    t = ''
    tlen = 0

    for word in s.split():
        if tlen + len(word) >= 79 - indent:
            t = t + '\n' + ' ' * indent
            tlen = indent
        elif tlen > 0:
            t = t + ' '
            tlen = tlen + 1

        t = t + word
        tlen = tlen + len(word)

    return t

def open_p(db):
    db = db + '''\

      <p>'''
    return db

def close_p(db):
    db = db + '''</p>\n'''
    return db

def open_ul(db):
    db = db + '''
      <ul>'''
    return db

def close_ul(db):
    db = db + '''\
      </ul>
'''
    return db

def open_li(db):
    db = db + '''
        <li>'''
    return db

def close_li(db):
    db = db + '''</li>\n'''
    return db

def open_body(db):
    db = db + '''\
    <body>'''
    return db

def close_body(db):
    db = db + '''
    </body>
'''
    return db

def open_project(db, cat, title):
    db = db + '''\
  <project cat='%s'>
    <title>%s</title>

''' % (cat, title)
    return db

def close_project(db):
    db = db + '''
  </project>

'''
    return db
 
def append_contacts(db, contacts):
    if not contacts:
        return db

    # You know, it's not that I don't know about templating
    # engines.  I do.  I just want to give you some additional
    # motivation :->
    db = db + '''\
    <contact>
'''
    for person in contacts:
        db = db + '''\
      <person>
        <name>%s</name>
        <email>%s</email>
      </person>
''' % (person[0], person[1])

    db = db + '''\
    </contact>

''' 
    return db

def append_links(db, links):
    if not links:
        return db

    db = db + '''\
    <links>
'''
    for link in links:
        db = db + '''\
      <url href="%s">%s</url>
''' % (link[1], link[0])

    db = db + '''\
    </links>

''' 
    return db

def append_sponsors(db, sponsors):
    if not sponsors:
        return db

    for sponsor in sponsors:
        db = db + '''\

    <sponsor>
      %s
    </sponsor>
''' % sponsor

    return db


def md2docbook(infile):
    cat = 'unknown' # For parsing individual submissions.
    db = docbook_header
    inside_project = False
    inside_body = False
    inside_p = False
    inside_ul = False
    contacts = []
    links = []
    sponsors = []

    for line in infile:
        line = line.rstrip()
        avoid_newline = False

        if line == '# FreeBSD Team Reports #':
            cat = 'team'
            continue
        if line == '# Kernel Projects #':
            cat = 'kern'
            continue
        if line == '# Ports #':
            cat = 'ports'
            continue
        if line == '# Architectures #':
            cat = 'arch'
            continue
        if line == '# Documentation #':
            cat = 'doc'
            continue
        if line == '# Third-Party Projects #':
            cat = 'third'
            continue
        if line.startswith('# '):
            sys.exit('invalid category name "%s"; please consult %s source code"' % (line, sys.argv[0]))

        if line.startswith('## '):
            title = line.strip('# ')

            # Start a new <project> entry.  But first finish
            # the old one.

            # XXX: As I've mentioned, this _really_ should get rewritten.
            if inside_p:
                db = close_p(db)
                inside_p = False

            if inside_ul:
                db = close_ul(db)
                inside_ul = False

            if inside_body:
                db = close_body(db)
                inside_body = False

            if inside_project:
                db = append_sponsors(db, sponsors)
                db = close_project(db)
                inside_project = False

            contacts = []
            links = []
            sponsors = []

            db = open_project(db, cat, title)
            inside_project = True
            continue

        # Translate '###' into '<p>', to match earlier reports.
        if line.startswith('### '):
            line = line.strip('# ')

        if line.startswith('Contact:'):
            # The comma in 'Name, <email>' confuses parseaddr().
            line = line.replace(',', '')
            contacts.append(parseaddr(line))
            continue

        if line.startswith('Link:'):
            href = re.search('\((.+)\)', line)
            if href:
                href = href.group(1)
            else:
                href = ''

            name = re.search('\[(.+)\]', line)
            if name:
                name = name.group(1)
            else:
                name = href

            links.append((name, href))
            continue

        if line.startswith('Sponsor:'):
            sponsor = line[len('Sponsor:'):].strip()
            sponsors.append(sponsor)
            continue

        if line.strip() == '':
            if not inside_body:
                continue;
            if inside_p:
                db = close_p(db)
                inside_p = False
                continue

        if not inside_body:
            db = append_contacts(db, contacts)
            db = append_links(db, links)
            db = open_body(db)
            inside_body = True

        # Unordered lists.
        if line.strip().startswith(('-', '*')):
            line = line.lstrip('*- ')
            if inside_p:
                db = close_p(db)
                inside_p = False
            if inside_ul:
                db = close_li(db)
            else:
                db = open_ul(db)
                inside_ul = True
            db = open_li(db)
            avoid_newline = True

        elif not line.startswith(' ') and inside_ul:
            db = close_li(db)
            db = close_ul(db)
            inside_ul = False

        # Here we paste the plain text.  Note that the text
        # in 'db' is generally _not_ followed by a newline,
        # so that we don't need to remove them when we append
        # '</p>'.
        if inside_p:
            db = db + '\n        '
        elif inside_ul:
            if not avoid_newline:
                db = db + '\n          '
        else:
            db = open_p(db)
            inside_p = True

        db = db + reflow(escape(line), 8)

    # Now I'm feeling guilty :-(
    if inside_p:
        db = close_p(db)
        inside_p = False

    if inside_ul:
        db = close_ul(db)
        inside_ul = False

    db = append_sponsors(db, sponsors)
    db = close_body(db)
    db = close_project(db) + docbook_footer
    inside_body = False

    return db

def main():
    if len(sys.argv) > 3:
        sys.exit('usage: %s [input-file [output-file]]' % sys.argv[0])

    if len(sys.argv) > 2:
        outfile = open(sys.argv[2], 'w')
    else:
        outfile = sys.stdout

    if len(sys.argv) > 1:
        infile = open(sys.argv[1], 'r')
    else:
        infile = sys.stdin

    docbook = md2docbook(infile)
    outfile.write(docbook)

if __name__ == '__main__':
    main()

