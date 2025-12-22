from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.lectures.tasks.error_handlers import handle_crawl_failure


class HandleCrawlFailureTest(TestCase):
    @patch("apps.lectures.tasks.error_handlers.logger")
    @patch("apps.lectures.tasks.error_handlers.AsyncResult")
    def test_no_traceback_logs_error(self, mock_async_result: MagicMock, mock_logger: MagicMock) -> None:
        mock_async_result.return_value.traceback = None

        task_id = "fake-task-id"
        handle_crawl_failure.run(task_id)

        mock_logger.error.assert_any_call(f"크롤링 태스크 실패, task_id={task_id}")
        mock_logger.error.assert_any_call("traceback 정보를 가져올 수 없습니다.")

    @patch("apps.lectures.tasks.error_handlers.logger")
    @patch("apps.lectures.tasks.error_handlers.AsyncResult")
    def test_with_traceback_logs_traceback(self, mock_async_result: MagicMock, mock_logger: MagicMock) -> None:
        fake_traceback = "some traceback info"
        mock_async_result.return_value.traceback = fake_traceback

        task_id = "fake-task-id"
        handle_crawl_failure.run(task_id)

        mock_logger.error.assert_any_call(f"크롤링 태스크 실패, task_id={task_id}")
        mock_logger.error.assert_any_call(f"실패한 태스크의 traceback:\n{fake_traceback}")
