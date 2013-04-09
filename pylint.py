#!python
'''
Sublime Text 2 Pylint Plugin
'''

import sublime, sublime_plugin
import subprocess
import re
import os
import sys
import logging

DEBUG = True
logging.basicConfig(filename="/tmp/sublime-pylint.log", level=logging.DEBUG)

def log(msg):
    '''debug log'''

    if DEBUG: 
        logging.debug(msg)


def pylint_command(file_name):
    '''get pylint shell command'''

    if sys.platform == 'win32':
        pathes = os.getenv('PATH').split(';')
        python_path_pattern = re.compile(r'Python\d{2}$')
        for path in pathes:
            if python_path_pattern.search(path) is not None:
                return [path+r'\Python', path+r'\Scripts\pyflakes', file_name]
        return []
    return ['pylint', file_name, '--reports=no']

def highlight_error(view, warning):
    '''highlight error line'''

    if not warning: 
        return

    line_number = int(re.findall(r'(\d+),\d+', warning)[0]) - 1
    point = view.text_point(line_number, 0)
    line = view.line(point)

    message =  re.findall(r"^(\w+:)", warning)[0]
    message =  message + re.findall(r"\d+,\d+:(.*)", warning)[0]

    PylintListener.warning_messages.append({
        'region': line,
        'message': message
    })

    return line

def display_warning(warning):
    '''show message on status bar'''

    for region in PylintListener.warning_messages:
        if region['region'] == warning:
            sublime.status_message(region['message'])
            break

def is_python_file(view):
    '''check is python file'''

    return bool(re.search('Python', view.settings().get('syntax'), re.I))


class PylintListener(sublime_plugin.EventListener):
    '''pylint listener'''

    warning_messages = []

    def __init__(self, *args, **kwargs):
        '''init'''

        sublime_plugin.EventListener.__init__(self, *args, **kwargs)

    def on_post_save(self, view):
        '''save file handler'''
        
        if not is_python_file(view):
            return 

        view.erase_regions('PyflakesWarnings')
        self.warning_messages = []

        file_name = view.file_name().replace(' ', r'\ ')
        process = subprocess.Popen(pylint_command(file_name), 
                                    stdout = subprocess.PIPE)  
        results = process.communicate()[0]

        if not results: 
            return

        regions = []
        for line in results.split("\n"):
            if not re.search(r"^(\w:)", line): 
                continue

            region = highlight_error(view, line.replace(file_name, ''))

            if region:
                regions.append(region)

        view.add_regions('PyflakesWarnings', 
                        regions, 
                        'string pyflakeswarning', 
                        'dot')

    @staticmethod    
    def on_selection_modified(view):
        '''line selection handler'''

        if is_python_file(view):

            warnings = view.get_regions('PyflakesWarnings')

            for warning in warnings:
                if warning.contains(view.sel()[0]):
                    display_warning(warning)
                    break