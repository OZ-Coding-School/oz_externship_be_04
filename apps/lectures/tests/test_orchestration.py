from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.lectures.tasks.orchestration import crawl_then_embed


class CrawlThenEmbedOrchestrationTest(TestCase):
    @patch("apps.lectures.tasks.orchestration.sync_inflearn_task.apply_async")
    def test_links_are_configured_correctly(self, mock_apply_async: MagicMock) -> None:
        crawl_then_embed()

        mock_apply_async.assert_called_once()

        _, kwargs = mock_apply_async.call_args

        link = kwargs["link"]
        link_error = kwargs["link_error"]

        self.assertEqual(link.task, "lectures.build_all_lecture_embeddings")
        self.assertEqual(link_error.task, "lectures.handle_crawl_failure")
