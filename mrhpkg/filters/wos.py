#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Filename: wos.py
Usage: DataFile Parse Module For CORE COLLECTION Format of Web of Science
"""


class WosItem:
    """WOS Data Format.
    Web of Science Core Collection Fields List
    http://images.webofknowledge.com/WOKRS5272R3/help/zh_CN/WOK/hs_wos_fieldtags.html
    """

    def __init__(self):
        self.database = 'WOS'
        self.RID = -1  # References ID
        self.CCR = set()  # Remove DOI from Field CR
        self.CTX = ''  # Cited Text
        self.LCS = []  # Local Cited References List
        self.LCR = []  # Local Citing References List


def getdata(filepath):
    """Return Data From File By CORE Format Parser.
    Normal: Return Data Type List
    Error:  Return -1
    """
    data = _parsefile(filepath) if checktype(filepath) else -1
    if data != -1:
        data = _fixdata(data)
        data = _localinfo(data)
    return data


def checktype(filepath):
    """Check WOS Exported File Format."""
    validlines = ['FN Clarivate Analytics Web of Science\n', 'VR 1.0\n']
    with open(filepath, encoding='utf-8-sig') as datafile:
        return datafile.readline() == validlines[0] and datafile.readline() == validlines[1]


def _parsefile(datafile_path):
    """Parse Exported File From Web of Science in CORE format."""
    data = []
    lastfield = ''
    wositem = ''
    uselesslines = ['\n', 'ER\n', 'EF\n',
                    'FN Clarivate Analytics Web of Science\n', 'VR 1.0\n']
    with open(datafile_path, encoding='utf-8-sig') as datafile:
        for line in datafile:
            if line not in uselesslines:
                field = line[:2].strip()
                text = line[3:].strip()
                if field:
                    if field == 'PT':
                        wositem = WosItem()
                        data.append(wositem)
                    setattr(wositem, field, text)
                    lastfield = field
                else:
                    content = getattr(wositem, lastfield)
                    if isinstance(content, str):
                        content = [content]
                    content.append(text)
                    setattr(wositem, lastfield, content)
    return data


def _localinfo(data):
    """Parse WosItem LCR LCS Data."""
    for rid, wositem in enumerate(data):
        wositem.RID = rid
        wositem.CCR = _remove_doi(wositem)
        wositem.CTX = _add_ctx(wositem)
    data = _add_info(data)
    return data


def _remove_doi(wositem):
    """Remove DOI In WosItem.CR."""
    ccr = set()
    if getattr(wositem, 'CR', ''):
        for item in wositem.CR:
            if ', DOI ' in item:
                item = item.split(', DOI')[0]
            ccr.add(item)
    return ccr


def _add_ctx(wositem):
    """Add Cited Text."""
    author = wositem.AU[0].replace(
        ', ', ' ') if getattr(wositem, 'AU', '') else ''
    year = wositem.PY if getattr(wositem, 'PY', '') else ''
    journal = wositem.J9 if getattr(wositem, 'J9', '') else wositem.BS if getattr(
        wositem, 'BS', '') else wositem.SO if getattr(wositem, 'SO', '') else ''
    volume = 'V' + wositem.VL if getattr(wositem, 'VL', '') else ''
    page = 'P' + wositem.BP if getattr(wositem, 'BP', '') else ''
    citetext = ', '.join([item for item in (
        author, year, journal, volume, page) if item])
    return citetext


def _add_info(data):
    """ADD LCR LCX"""
    ctx_rid = {}
    ctx_set = set()
    for wositem in data:
        ctx_rid[wositem.CTX] = wositem.RID
        ctx_set.add(wositem.CTX)
    for rid, wositem in enumerate(data):
        if wositem.CCR:
            citeinfo = ctx_set & wositem.CCR
            for item in citeinfo:
                data[ctx_rid.get(item)].LCS.append(rid)
                wositem.LCR.append(ctx_rid.get(item))
    return data


def _fixdata(data):
    """Data Preparation."""
    for wositem in data:

        # author to list
        if isinstance(getattr(wositem, 'AU', ''), str):
            wositem.AU = [wositem.AU]
        if isinstance(getattr(wositem, 'AF', ''), str):
            wositem.AF = [wositem.AF]
        
        # TI SO to str
        if isinstance(getattr(wositem, 'TI', ''), list):
            wositem.TI = ' '.join(wositem.TI)
        if isinstance(getattr(wositem, 'SO', ''), list):
            wositem.SO = ' '.join(wositem.SO)
        
        # Change DE keywords to list
        de = getattr(wositem, 'DE', '')
        if de:
            if isinstance(de, list):
                setattr(wositem, 'DE', ' '.join(de))
                de = getattr(wositem, 'DE', '')
            if isinstance(de, str):
                setattr(wositem, 'DE', de.split('; '))

        # Abstract
        abstract = getattr(wositem, 'AB', '')
        if abstract:
            if isinstance(abstract, list):
                setattr(wositem, 'AB', ' '.join(abstract))

    return data

if __name__ == '__main__':
    filepath = './mrhpkg/filters/demo_wos_202101.txt'
    data = getdata(filepath)
    for wositem in data:
        print(getattr(wositem, 'DE', ''))
