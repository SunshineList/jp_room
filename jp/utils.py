# -*- coding: utf-8 -*-
def list_to_choice(rawlist):
    tmplist = []
    for i in rawlist:
        a = (i, i)
        tmplist.append(a)
    return tuple(tmplist)
