#!/usr/bin/env python
# encoding: utf-8

# Based on http://pymotw.com/2/sys/tracing.html, "Tracing a program as it runs"
# and http://hg.python.org/cpython/file/2.7/Lib/trace.py

import sys
import os
import struct

fifo_file = None

def report_trace(file, line):
    size = len(file) + 1 + 8 + 4 + 4
    data = struct.pack(">QLL%dsb" % len(file), 0x6d6574616c6c6775, size, int(line), file, 0)

    fifo_file.write(data)

def trace_lines(frame, event, arg):
    if event != 'line':
        return
    co = frame.f_code
    func_name = co.co_name
    line_no = frame.f_lineno
    filename = co.co_filename
    report_trace(filename, line_no)

def trace_calls(frame, event, arg):
    if event != 'call':
        return
    co = frame.f_code
    func_name = co.co_name
    line_no = frame.f_lineno
    filename = co.co_filename
    report_trace(filename, line_no)
    return trace_lines

def runctx(cmd, globals=None, locals=None):
    if globals is None: globals = {}
    if locals is None: locals = {}
    sys.settrace(trace_calls)
    try:
        exec cmd in globals, locals
    finally:
        sys.settrace(None)

if __name__ == "__main__":
    prog_argv = sys.argv[1:]

    sys.argv = prog_argv
    progname = prog_argv[0]
    sys.path[0] = os.path.split(progname)[0]

    fifo_path = os.getenv("KCOV_PYTHON_PIPE_PATH")
    if fifo_path == None:
        sys.stderr.write("the KCOV_PYTHON_PIPE_PATH environment variable is not set")
        sys.exit(127)
    try:
        fifo_file = open(fifo_path, "w")
    except:
        sys.stderr.write("Can't open fifo file")
        sys.exit(127)

    try:
        with open(progname) as fp:
            code = compile(fp.read(), progname, 'exec')
            # try to emulate __main__ namespace as much as possible
            globs = {
                '__file__': progname,
                '__name__': '__main__',
                '__package__': None,
                '__cached__': None,
            }
            runctx(code, globs, globs)
    except IOError, err:
        sys.stderr.write("Cannot run file %r because: %s" % (sys.argv[0], err))
        sys.exit(127)
