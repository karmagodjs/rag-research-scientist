"""
Unit tests for WebRetriever and DDG Lite HTML parsing error handling.
"""

import unittest
from unittest.mock import patch, MagicMock
from retrieval.web import WebRetriever


class TestWebRetriever(unittest.TestCase):

    def setUp(self):
        self.retriever = WebRetriever(timeout=5)

    @patch("requests.post")
    def test_ddg_lite_successful_parse(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = """
        <html>
            <table>
                <tr>
                    <td><a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpaper1">Sample Paper Title 2025</a></td>
                </tr>
                <tr>
                    <td class="result-snippet">This is a snippet discussing benchmark results in 2025.</td>
                </tr>
            </table>
        </html>
        """
        mock_post.return_value = mock_resp

        docs = self.retriever.search("test query", top_k=5)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "Sample Paper Title 2025")
        self.assertEqual(docs[0].url, "https://example.com/paper1")

    @patch("requests.post")
    def test_ddg_lite_markup_changed_graceful_fallback(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body>Structure changed completely</body></html>"
        mock_post.return_value = mock_resp

        docs = self.retriever.search("test query", top_k=5)
        self.assertEqual(len(docs), 0)

    @patch("requests.post")
    def test_ddg_lite_http_error_graceful_fallback(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "Service Unavailable"
        mock_post.return_value = mock_resp

        docs = self.retriever.search("test query", top_k=5)
        self.assertEqual(len(docs), 0)


if __name__ == "__main__":
    unittest.main()
