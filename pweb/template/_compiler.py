#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#---------------------------------#
#author: yehuaqing                #
#email:valan1978@163.com          #
#date: 2013-1-30                  #
#---------------------------------#

import re
import string
import traceback

class CompilerError(Exception):
    pass

class Compiler:
    def __init__(self, reduce=False):
        self.pyindent = 2
        self.reduce = reduce
        self.outtag = ['print>> stdout,', 'print >> stdout,', 'print ']

    def _fix(self, fixstr, isTag=False):
        if not fixstr:
            return fixstr

        if isTag:
            fixstr = fixstr.strip()

        if fixstr.startswith('\n'):
            fixstr = fixstr[1:]

        if fixstr.endswith('\n'):
            fixstr = fixstr[:-1]

        return fixstr

    def parseHtml(self, data):
        if self.reduce:
            data = self._pscript(data)

        i = 0
        c = len(data)

        # fix empty template_file
        # if c <= 0: yield ""

        while i < c:
            x = data.find('<%',i)
            if x == -1:
                y = c
                yield self._fix(data[i:])
            else:
                y = data.find('%>',i)
                if y == -1: y = c
                else:  y += 2

                if i != x: yield self._fix(data[i:x])
                if x != y: yield self._fix(data[x:y], True)
            i = y

    def _skipSpace(self, source):
        if isinstance(source, basestring):
            source = string.split(source, '\n')
        source = [x for x in source if string.strip(x)!='']

        for s in source:
            yield s
        else:
            yield ''

    def goAnyWhere(self, source):
        isStart = True
        skipspace = 0
        for s in self._skipSpace(source):
            if isStart:
                skipspace = len(s) - len(s.lstrip())
                isStart = False
            yield s[skipspace:].replace('\t', ' '*self.pyindent)

    def repstr(self, n=0, s=' '):
        return str(s) * (self.pyindent + n)

    def makerepstr(self, stack):
        return self.repstr(len(stack) * self.pyindent)

    def _escapestr(self, s):
        for ch in str(s):
            if ch=='"': yield '\\"'
            elif ch=='\\': yield '\\\\'
            elif ch=="'": yield "\\'"
            else: yield ch

    def escapestr(self, s):
        s = s.rstrip()
        return "".join(self._escapestr(s))

    def _rep(self, line, defkey="print ", escape=False):
        fpos = line.find(defkey)
        if fpos != -1:
            #if self.reduce:
            #    line = """%sout.write(%s, escape=%s)""" % (line[:fpos], line[fpos+len(defkey):], escape)
            #else:
            line = """%sout.write(%s, "\\n", escape=%s)""" % (line[:fpos], line[fpos+len(defkey):], escape)
        return line

    def repout(self, line, deflist=None):
        for k in (deflist or []):
            line = self._rep(line, k)
        return "%s\n"% line

    def _replacemark(self, s, rpmark, *marks):
        pt = re.compile("|".join(str(v) for v in marks))
        return rpmark.join(self._skipSpace(pt.split(s)))

    def _replace(self, s):
        s = self._replacemark(s, '\n', '[ ]+\n', '\n[ ]+', '[\n]{2:}')
        s = self._replacemark(s, ' ', '\t+', '[ ]{2:}')
        #if self.reduce: s = s.replace('\r','').replace('\n','')
        return s

    def compile(self, resp_src):
        nodes = self.parseHtml(resp_src)
        return "".join(self._parse(nodes))

    def _wipescript(self, script):
        script = script.replace("\r\n", "\n").replace("\r", "\n")
        ldat = script.split("\n")
        resp_list = []
        for line in ldat:
            tline = line.strip().lower()
            pos = tline.find('//')
            if pos != -1 and not tline[pos+2:].startswith('-->'):
                line = line[:pos]

            ptn = re.compile(r"/\*([^\*.]*)\*/", re.I)
            mathkeys = ptn.findall(line)
            for key in mathkeys:
                line = line.replace("/*%s*/"% key, "")

            line = line.strip()

            if line:
                if not line[-1:] in ['-','>','{','}',';'] and \
                  not line.lower().startswith("function"):
                    line = "%s"% line
                resp_list.append(line)
        return "\n".join(resp_list)

    def _pscript(self, resp_src):
        p = re.compile(r'<script[^>.]*>([\s\S]*?)</script>', re.S|re.I)
        script_list = p.findall(resp_src)
        for script in script_list:
            resp_src = resp_src.replace(script, self._wipescript(script))
        return resp_src

    def _parse(self, fields):
        yield '''import traceback\n'''
        yield '''try:\n'''

        #stack item:[<#tag>,<index of fields>]
        stack   = []
        icode   = 0

        # setup data and parse code
        try:
            for field in fields:
                if field.startswith('''<%='''):
                    yield """%sout.write(str(%s), escape=False)\n""" % ( self.makerepstr(stack), field[3:-2].strip() )
                elif field.startswith('''<%-'''): 
                    pass
                elif field.startswith('''<%#if'''):
                    yield """%sif %s:\n""" % ( self.makerepstr(stack), field[6:-2] )
                    stack.append(['#if', icode])
                elif field.startswith('''<%#else'''):
                    yield """%selse:\n""" % self.repstr((len(stack) - 1) * self.pyindent)
                elif field.startswith('''<%#elif'''):
                    yield """%selif %s:\n""" % ( self.repstr((len(stack) - 1) * self.pyindent), field[8:-2] )
                elif field.startswith('''<%#endif'''):
                    if len(stack) == 0: 
                        raise CompilerError('''error syntax:unmatch #if....#endif %s''' % field)
                    elif stack[-1][0] == '#if': 
                        del stack[len(stack) - 1]
                    else: 
                        raise CompilerError('''error syntax:unmatch #if....#endif %s''' % field)
                    yield """\n"""
                elif field.startswith('''<%#for'''):
                    yield """%sfor %s:\n""" % ( self.makerepstr(stack), field[7:-2] )
                    stack.append(['#for', icode])
                elif field.startswith('''<%#endfor'''):
                    while len(stack)>0 and stack[-1][0] != '#for':
                        del stack[len(stack) - 1]
                    if len(stack) == 0:
                        raise CompilerError('''error syntax: unmath #for...#endfor %s''' % field)
                    elif stack[-1][0] == '#for': 
                        del stack[len(stack) - 1]
                    else: 
                        raise CompilerError('''error syntax: unmatch #for...#endfor %s''' % field)
                    yield """\n"""
                elif field.startswith('''<%#while'''):
                    yield """%swhile %s:\n""" % ( self.makerepstr(stack), field[9:-2] )
                    stack.append(['#while', icode])
                elif field.startswith('''<%#break'''):
                    yield """%sbreak\n""" % self.makerepstr(stack)
                elif field.startswith('''<%#continue'''):
                    yield """%scontinue\n""" %  self.makerepstr(stack)
                elif field.startswith('''<%#endwhile'''):
                    while len(stack) > 0 and stack[-1][0] != '#while':
                        del stack[len(stack) - 1]
                    if len(stack) == 0:
                        raise CompilerError('''error syntax: unmatch #while ...#endwhile %s''' % field)
                    elif stack[-1][0] == '#while':
                        del stack[len(stack) - 1]
                    else:
                        raise CompilerError('''error syntax:unmatch #while ...#endwhile %s''' % field)
                    yield """\n"""
                elif field.startswith('''<%#end'''):
                    break
                elif field.startswith('''<%'''):
                    #if not self.reduce: yield "\n"
                    yield "\n"
                    for s in self.goAnyWhere(field[2:-2]):
                        yield """%s%s""" % ( self.makerepstr(stack), self.repout(s, self.outtag) )
                else:
                    if len(field.strip()) > 0:
                        field = self._replace(field)
                        if field.startswith('<') and not field.startswith('</'):
                            field = "\n%s"% field
                        yield """%sout.write('''%s''', escape=False)\n""" % ( self.makerepstr(stack), self.escapestr(field) )
                icode += 1
            else:
                yield """%spass\n""" % self.repstr()
        except :
            raise CompilerError(traceback.format_exc())

        yield '''except:\n'''
        yield '''%sout.write(traceback.format_exc())'''% (' ' * self.pyindent)

    def __call__(self, resp_src):
        return self.compile(resp_src)

if __name__ == '__main__' :
    import doctest
    doctest.testmod()