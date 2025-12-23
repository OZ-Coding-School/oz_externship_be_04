from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.lectures.tasks.orchestration import crawl_then_embed


class CrawlThenEmbedOrchestrationTest(TestCase):
    @patch("apps.lectures.tasks.orchestration.sync_inflearn_task")
    def test_links_are_configured_correctly(self, mock_task: MagicMock) -> None:
        crawl_then_embed()

        mock_task.apply_async.assert_called_once()

        _, kwargs = mock_task.apply_async.call_args

        link = kwargs["link"]
        link_error = kwargs["link_error"]

        self.assertEqual(link.task, "lectures.build_all_lecture_embeddings")
        self.assertEqual(link_error.task, "lectures.handle_crawl_failure")
