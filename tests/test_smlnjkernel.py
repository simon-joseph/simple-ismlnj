"""Unit tests for the SML/NJ Jupyter kernel."""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

from pexpect import EOF, TIMEOUT, replwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smlnjkernel import crlf_pat, timeout_pat, SMLNJKernel


class TestRegexPatterns(unittest.TestCase):
    """Tests for the regular expression patterns used in the kernel."""

    def test_crlf_pat_replaces_newline(self):
        self.assertEqual(crlf_pat.sub(' ', 'a\nb'), 'a b')

    def test_crlf_pat_replaces_carriage_return(self):
        self.assertEqual(crlf_pat.sub(' ', 'a\rb'), 'a b')

    def test_crlf_pat_replaces_crlf(self):
        self.assertEqual(crlf_pat.sub(' ', 'a\r\nb'), 'a b')

    def test_crlf_pat_replaces_multiple(self):
        self.assertEqual(crlf_pat.sub(' ', 'a\nb\nc'), 'a b c')

    def test_timeout_pat_matches_basic(self):
        m = timeout_pat.search('%timeout 30')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '30')

    def test_timeout_pat_no_match_for_plain_code(self):
        self.assertIsNone(timeout_pat.search('1 + 1;'))

    def test_timeout_pat_multiline(self):
        code = '%timeout 60\nfun fib n = n;'
        m = timeout_pat.search(code)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '60')

    def test_timeout_pat_strips_magic_from_code(self):
        code = '%timeout 10\n1 + 1;'
        cleaned = timeout_pat.sub('', code)
        self.assertNotIn('%timeout', cleaned)
        self.assertIn('1 + 1;', cleaned)


class TestSMLNJKernelExecute(unittest.TestCase):
    """Tests for the SMLNJKernel.do_execute method."""

    def _make_kernel(self):
        """Create a kernel instance with all external dependencies mocked."""
        kernel = SMLNJKernel.__new__(SMLNJKernel)
        kernel.execution_count = 1
        kernel.iopub_socket = MagicMock()
        kernel.send_response = MagicMock()
        kernel.smlnjwrapper = MagicMock()
        return kernel

    @patch('smlnjkernel.replwrap.REPLWrapper')
    def test_start_smlnj_uses_newline_prefixed_prompt(self, mock_replwrapper):
        instance = mock_replwrapper.return_value
        kernel = SMLNJKernel.__new__(SMLNJKernel)
        kernel._start_smlnj()

        self.assertEqual(instance.prompt, '\r\n- ')
        self.assertEqual(instance.continuation_prompt, replwrap.PEXPECT_CONTINUATION_PROMPT)

    def test_execute_adds_semicolon(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        kernel.do_execute('1 + 1', silent=False)
        kernel.smlnjwrapper.run_command.assert_called_once_with('1 + 1;', timeout=None)

    def test_execute_does_not_double_semicolon(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        kernel.do_execute('1 + 1;', silent=False)
        kernel.smlnjwrapper.run_command.assert_called_once_with('1 + 1;', timeout=None)

    def test_execute_returns_ok_status(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        result = kernel.do_execute('1 + 1;', silent=False)
        self.assertEqual(result['status'], 'ok')

    def test_execute_sends_output_when_not_silent(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        kernel.do_execute('1 + 1;', silent=False)
        kernel.send_response.assert_called_once()
        args = kernel.send_response.call_args
        self.assertEqual(args[0][1], 'stream')
        self.assertEqual(args[0][2]['text'], 'val it = 2 : int')

    def test_execute_silent_does_not_send_output(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        kernel.do_execute('1 + 1;', silent=True)
        kernel.send_response.assert_not_called()

    def test_execute_empty_code_returns_ok(self):
        kernel = self._make_kernel()
        result = kernel.do_execute('', silent=False)
        self.assertEqual(result['status'], 'ok')
        kernel.smlnjwrapper.run_command.assert_not_called()

    def test_execute_whitespace_only_returns_ok(self):
        kernel = self._make_kernel()
        result = kernel.do_execute('   \n  ', silent=False)
        self.assertEqual(result['status'], 'ok')
        kernel.smlnjwrapper.run_command.assert_not_called()

    def test_execute_with_timeout_magic(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        kernel.do_execute('%timeout 30\n1 + 1', silent=False)
        kernel.smlnjwrapper.run_command.assert_called_once_with('1 + 1;', timeout=30)

    def test_execute_normalizes_crlf(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.return_value = 'val it = 2 : int'
        kernel.do_execute('1 +\r\n1', silent=False)
        kernel.smlnjwrapper.run_command.assert_called_once_with('1 + 1;', timeout=None)

    def test_execute_timeout_exception_restarts_repl(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.side_effect = TIMEOUT('timed out')
        with patch.object(kernel, '_start_smlnj') as mock_restart:
            result = kernel.do_execute('%timeout 5\n1 + 1;', silent=False)
        mock_restart.assert_called_once()
        self.assertEqual(result['status'], 'ok')

    def test_execute_eof_exception_restarts_repl(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.side_effect = EOF('eof')
        kernel.smlnjwrapper.child.before = 'partial output'
        with patch.object(kernel, '_start_smlnj') as mock_restart:
            result = kernel.do_execute('1 + 1;', silent=False)
        mock_restart.assert_called_once()
        self.assertEqual(result['status'], 'ok')

    def test_execute_keyboard_interrupt_returns_abort(self):
        kernel = self._make_kernel()
        kernel.smlnjwrapper.run_command.side_effect = KeyboardInterrupt()
        kernel.smlnjwrapper.child.before = 'interrupted output'
        result = kernel.do_execute('1 + 1;', silent=False)
        self.assertEqual(result['status'], 'abort')

    def test_execute_full_stream_example(self):
        kernel = SMLNJKernel.__new__(SMLNJKernel)
        kernel.execution_count = 1
        kernel.iopub_socket = MagicMock()
        kernel.send_response = MagicMock()
        kernel._start_smlnj()
        import os
        stream_path = os.path.abspath('tests/regression/stream.sml')
        result = kernel.do_execute(f'use "{stream_path}"; open Stream;', silent=False)
        self.assertEqual(result['status'], 'ok')


class TestSMLNJKernelMetadata(unittest.TestCase):
    """Tests for kernel metadata and class-level properties."""

    def test_implementation_name(self):
        self.assertEqual(SMLNJKernel.implementation, 'SML/NJ')

    def test_language_info_name(self):
        self.assertEqual(SMLNJKernel.language_info['name'], 'SML/NJ')

    def test_language_info_file_extension(self):
        self.assertEqual(SMLNJKernel.language_info['file_extension'], '.sml')

    def test_language_version_default(self):
        self.assertEqual(SMLNJKernel._language_version, '110.99.9')

    def test_banner_contains_version(self):
        kernel = SMLNJKernel.__new__(SMLNJKernel)
        self.assertIn('110.99.9', kernel.banner)

    def test_banner_contains_kernel_name(self):
        kernel = SMLNJKernel.__new__(SMLNJKernel)
        self.assertIn('SML/NJ', kernel.banner)


if __name__ == '__main__':
    unittest.main()
