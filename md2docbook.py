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

def md2docbook(infile):
    cat = 'unknown' # For parsing individual submissions.
    db = docbook_header
    inside_body = False
    inside_p = False
    inside_ul = False
    contacts = []
    links = []

    for line in infile:
        line = line.rstrip()

        if line == '# FreeBSD Team Reports #':
            cat = 'team'
            continue
        if line == '# Kernel Projects #':
            cat = 'kern'
            continue
        if line == '# Ports #':
            cat = 'ports'
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
                db = db + '''\
      </p>
'''

            if inside_ul:
                db = db + '''\
      </ul>
'''

            if inside_body:
                db = db + '''\

    </body>
  </project>

'''
            contacts = []
            links = []
            inside_body = False
            inside_p = False
            inside_ul = False

            db = db + '''\
  <project cat='%s'>
    <title>%s</title>

''' % (cat, title)
            continue

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

        if line == '' and not inside_body:
            continue;

        if not inside_body:
            if contacts:

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

            if links:
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

            db = db + '''\
    <body>'''
            inside_body = True

        # Unordered lists.
        if line.strip().startswith(('-', '*')):
            line = line.lstrip('*- ')
            if inside_p:
                db = db + '''\
      </p>
'''
                inside_p = False
            if inside_ul:
                db = db + '''</li>\n'''
            else:
                db = db + '''
      <ul>
'''
                inside_ul = True
            db = db + '''\
        <li>'''

        elif not line.startswith(' ') and inside_ul:
            db = db + '''</li>
      </ul>
'''
            inside_ul = False

        if line == '' and inside_p:
            db = db + '''</p>\n'''
            inside_p = False
            continue

        # Here we paste the plain text.
        if inside_p:
            db = db + '\n        '
        elif inside_ul:
            db = db + '\n'
            pass
        else:
            db = db + '''
      <p>'''
            inside_p = True

        db = db + reflow(line, 8)

    # Now I'm feeling guilty :-(
    db = db + '''
      </p>
    </body>
  </project>
'''
    db = db + docbook_footer

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

