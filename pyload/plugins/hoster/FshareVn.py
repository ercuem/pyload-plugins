# -*- coding: utf-8 -*-

import re
import time
import urlparse

from ..internal.SimpleHoster import SimpleHoster
from ..internal.misc import json


def double_decode(m):
    return m.group(1).decode('raw_unicode_escape')


class FshareVn(SimpleHoster):
    __name__ = "FshareVn"
    __type__ = "hoster"
    __version__ = "0.31"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?fshare\.vn/file/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """FshareVn hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<i class="fa fa-file-.+?"></i>\s*(?P<N>.+?)\s*</div>'
    SIZE_PATTERN = r'<i class="fa fa-hdd-o"></i>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)\s*</div>'
    OFFLINE_PATTERN = ur'Tập tin quý khách yêu cầu không tồn tại.'

    NAME_REPLACEMENTS = [("(.*)", double_decode)]

    URL_REPLACEMENTS = [("http://", "https://")]

    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('id="download-form"')
        url = urlparse.urljoin(pyfile.url, action)

        if not inputs:
            self.error(_("Free Download form not found"))

        password = self.get_password()
        if password:
            inputs['DownloadForm[pwd]'] = password

        inputs.update({'ajax': "download-form", 'undefined': "undefined"})
        self.data = self.load(url, post=inputs)

        try:
            json_data = json.loads(self.data)

        except Exception:
            self.fail(_("Expected JSON data"))

        err_msg = json_data.get('msg')
        if err_msg:
            self.fail(err_msg)

        elif 'url' not in json_data:
            if 'DownloadForm_pwd' in json_data:
                if password:
                    self.fail(_("Wrong password"))

                else:
                    self.fail(_("Download is password protected"))

            else:
                self.fail(_("Unexpected response"))

        wait_time = json_data.get('wait_time', None)
        wait_time = 35 if wait_time is None else int(wait_time)
        self.wait(wait_time)

        self.link = json_data['url']

    def handle_premium(self, pyfile):
        self.handle_free(pyfile)
