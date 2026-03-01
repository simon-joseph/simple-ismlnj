from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF, TIMEOUT
from subprocess import check_output

import re
import signal

crlf_pat = re.compile(r'[\r\n]+')
timeout_pat = re.compile(r'^\s*%timeout\s+(\d+)\s*$', re.MULTILINE)

class SMLNJKernel(Kernel):
    implementation = 'SML/NJ'
    implementation_version = '0.0.1'

    language_info = {
        'name': 'SML/NJ',
        'codemirror_mode': 'fsharp',
        'mimetype': 'text/plain',
        'file_extension': '.sml'
    }

    _language_version = '110.99.9'


    @property
    def language_version(self):
        if self._language_version is None:
            self._language_version = check_output(['sml', '']).decode('utf-8')
        return self._language_version

    @property
    def banner(self):
        return u'Simple SML/NJ Kernel (%s)' % self.language_version

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_smlnj()

    def _start_smlnj(self):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            self.smlnjwrapper = replwrap.REPLWrapper("sml", "- ", None)
        finally:
            signal.signal(signal.SIGINT, sig)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        # Parse optional %timeout magic (e.g. "%timeout 30")
        timeout = None
        m = timeout_pat.search(code)
        if m:
            timeout = int(m.group(1))
            code = timeout_pat.sub('', code)

        code = crlf_pat.sub(' ', code.strip())
        if not code:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        try:
            if not code.rstrip().endswith(';'):
                code = code.rstrip() + ';'
            output = self.smlnjwrapper.run_command(code, timeout=timeout)
        except KeyboardInterrupt:
            self.smlnjwrapper.child.sendintr()
            interrupted = True
            self.smlnjwrapper._expect_prompt()
            output = self.smlnjwrapper.child.before
        except TIMEOUT:
            output = 'Execution timed out after %d seconds. Check for infinite loops or reduce computation complexity.' % timeout
            self._start_smlnj()
        except EOF:
            output = self.smlnjwrapper.child.before + 'Restarting SML/NJ'
            self._start_smlnj()

        if not silent:
            # Send standard output
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        return {'status': 'ok', 'execution_count': self.execution_count,
                'payload': [], 'user_expressions': {}}

# ===== MAIN =====
if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=SMLNJKernel)
