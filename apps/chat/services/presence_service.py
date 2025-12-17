from typing import Any, Dict, List

from django_redis import get_redis_connection  # type: ignore

from apps.study_groups.models import GroupMember


class PresenceService:
    @staticmethod
    def add(group_id: int, user_id: int) -> None:
        redis = get_redis_connection("default")
        redis.sadd(f"chat_online:{group_id}", user_id)

    @staticmethod
    def remove(group_id: int, user_id: int) -> None:
        redis = get_redis_connection("default")
        redis.srem(f"chat_online:{group_id}", user_id)

    @staticmethod
    def get_members(group_id: int) -> List[Dict[str, Any]]:
        members = GroupMember.objects.filter(study_group_id=group_id).select_related("user_id")

        redis = get_redis_connection("default")
        online_ids = {int(uid) for uid in redis.smembers(f"chat_online:{group_id}")}

        return [
            {
                "id": m.user_id.id,
                "nickname": m.user_id.nickname,
                "is_online": m.user_id.id in online_ids,
                "is_host": m.is_leader,
            }
            for m in members
        ]
