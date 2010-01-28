import sys, os
maindir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path += [maindir, os.path.join(maindir, 'site_tools')]