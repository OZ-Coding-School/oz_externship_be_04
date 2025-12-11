import logging
import os
import re
from typing import List, Optional, Tuple

import numpy as np
import redis
from dotenv import load_dotenv
from numpy._typing import NDArray
from sentence_transformers import SentenceTransformer

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyLecture
from apps.users.models import User

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

STOPWORDS = {"강의", "수업", "소개", "배우기", "공부", "사용법"}

EMBED_TTL = int(os.getenv("EMBED_TTL", 86400))
EMBED_DIM = int(os.getenv("EMBED_DIM", 384))


def lecture_embed_key(lecture_id: int) -> str:
    return f"lecture:embed:{lecture_id}"

def user_embed_key(user_id: int) -> str:
    return f"user:embed:{user_id}"

def remove_stopwords(text: str) -> str:
    tokens = text.split()
    tokens = [tok for tok in tokens if tok not in STOPWORDS]
    return " ".join(tokens)


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"[^가-힣a-z0-9\s]", " ", text)
    text = re.sub(r"\b\d{3,}\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_lecture_embedding_vector(lecture: CrawledLecture) -> NDArray[np.float32]:
    title = lecture.title or ""
    description = lecture.description or ""
    instructor = lecture.instructor or ""
    category_names = " ".join(cat.name for cat in lecture.categories.all())
    text = f"{title} {description} {instructor} {category_names}"

    text = clean_text(text)
    text = remove_stopwords(text)

    vec: NDArray[np.float32] = embedding_model.encode([text])[0].astype(np.float32)

    norm = np.float32(np.linalg.norm(vec))
    if norm == 0:
        return vec
    return vec / norm


def get_lecture_embedding_vector(lecture: CrawledLecture) -> NDArray[np.float32]:
    key = lecture_embed_key(lecture.id)

    cached = None
    try:
        cached = redis_client.get(key)
    except redis.exceptions.ConnectionError:
        logger.exception(f"Redis 연결 실패: 키 {key} 조회 중 오류 발생")
    except redis.exceptions.TimeoutError as e:
        logger.warning(f"Redis 타임아웃: 키 {key} 조회 중 {e} 발생")
    except redis.exceptions.RedisError as e:
        logger.warning(f"Redis 일반 오류: 키 {key} 조회 중 {e} 발생")

    if cached:
        try:
            arr = np.frombuffer(cached, dtype=np.float32)
            if arr.size == EMBED_DIM:
                return arr
            else:
                logger.warning(f"캐시된 벡터 크기 불일치: 키 {key}, 예상 {EMBED_DIM}, 실제 {arr.size}")
        except ValueError:
            logger.exception(f"캐시된 벡터 역직렬화 실패: 키 {key}")
        except Exception as e:
            logger.warning(f"캐시된 벡터 읽기 중 예상치 못한 오류: 키 {key}, 오류 {e}")

    vec = build_lecture_embedding_vector(lecture)

    try:
        redis_client.set(key, vec.tobytes(), ex=EMBED_TTL)
    except redis.exceptions.ConnectionError:
        logger.exception(f"Redis 연결 실패: 키 {key} 저장 중 오류 발생")
    except redis.exceptions.TimeoutError as e:
        logger.warning(f"Redis 타임아웃: 키 {key} 저장 중 {e} 발생")
    except redis.exceptions.RedisError as e:
        logger.warning(f"Redis 일반 오류: 키 {key} 저장 중 {e} 발생")

    return vec


def get_user_embedding_vector(user: User, lecture_vectors: NDArray[np.float32], lecture_ids: List[int]) -> Optional[NDArray[np.float32]]:
    key = user_embed_key(user.id)

    cached = None
    try:
        cached = redis_client.get(key)
    except redis.exceptions.ConnectionError:
        logger.exception(f"Redis 연결 실패: 키 {key} 조회 중 오류 발생")
    except redis.exceptions.TimeoutError as e:
        logger.warning(f"Redis 타임아웃: 키 {key} 조회 중 {e} 발생")
    except redis.exceptions.RedisError as e:
        logger.warning(f"Redis 일반 오류: 키 {key} 조회 중 {e} 발생")

    if cached:
        try:
            arr = np.frombuffer(cached, dtype=np.float32)
            if arr.size == EMBED_DIM:
                return arr
            else:
                logger.warning(f"캐시된 유저 벡터 크기 불일치: 키 {key}, 예상 {EMBED_DIM}, 실제 {arr.size}")
        except ValueError:
            logger.exception(f"캐시된 유저 벡터 역직렬화 실패: 키 {key}")
        except Exception as e:
            logger.warning(f"캐시된 유저 벡터 읽기 중 예상치 못한 오류: 키 {key}, 오류 {e}")

    user_vec = build_user_vector(user, lecture_vectors, lecture_ids)
    if user_vec is None:
        return None

    try:
        redis_client.set(key, user_vec.tobytes(), ex=EMBED_TTL)
    except redis.exceptions.ConnectionError:
        logger.exception(f"Redis 연결 실패: 키 {key} 저장 중 오류 발생")
    except redis.exceptions.TimeoutError as e:
        logger.warning(f"Redis 타임아웃: 키 {key} 저장 중 {e} 발생")
    except redis.exceptions.RedisError as e:
        logger.warning(f"Redis 일반 오류: 키 {key} 저장 중 {e} 발생")

    return user_vec


def build_user_vector(
    user: User,
    lecture_vectors: NDArray[np.float32],
    lecture_ids: List[int],
) -> Optional[NDArray[np.float32]]:
    bookmark_ids = set(user.lecture_bookmarks.values_list("lecture_id", flat=True))

    group_ids = GroupMember.objects.filter(user_id=user.id).values_list("study_group_id", flat=True)
    group_lecture_ids = set(
        StudyLecture.objects.filter(study_group_id__in=group_ids).values_list("lecture_id", flat=True)
    )

    preferred_cats = user.preferred_categories.values_list("category_id", flat=True)
    category_lecture_ids = set(
        CrawledLecture.objects.filter(categories__id__in=preferred_cats).values_list("id", flat=True)
    )

    user_lecture_ids = bookmark_ids | group_lecture_ids | category_lecture_ids
    if not user_lecture_ids:
        return None

    id_to_idx = {lec_id: idx for idx, lec_id in enumerate(lecture_ids)}

    vectors = []
    weights = []

    for lec_id in user_lecture_ids:
        idx = id_to_idx.get(lec_id)
        if idx is None:
            continue

        vec = lecture_vectors[idx]

        if lec_id in bookmark_ids:
            w = 5.0
        elif lec_id in group_lecture_ids:
            w = 3.0
        else:
            w = 1.0

        vectors.append(vec)
        weights.append(w)

    if not vectors:
        return None

    vecs = np.vstack(vectors)
    w_array = np.array(weights, dtype=np.float32).reshape(-1, 1)

    weighted_sum: NDArray[np.float32] = np.sum(vecs * w_array, axis=0)
    weight_total = np.sum(w_array)

    user_vec = weighted_sum / weight_total

    norm = np.float32(np.linalg.norm(user_vec))
    if norm == 0:
        return user_vec
    return user_vec / norm


def recommend_lectures(user: User, top_n: int = 3) -> Tuple[List[CrawledLecture], str]:
    lectures = list(CrawledLecture.objects.prefetch_related("categories").all())
    if not lectures:
        return [], "lecture not crawled"

    lecture_ids = [lec.id for lec in lectures]
    lecture_vectors = np.vstack([get_lecture_embedding_vector(lec) for lec in lectures])

    user_vec = get_user_embedding_vector(user, lecture_vectors, lecture_ids)

    if user_vec is not None:
        sims = lecture_vectors @ user_vec
        top_idx = np.argsort(sims)[::-1][:top_n]
        recommended = [lectures[i] for i in top_idx]
        return recommended, "personalized"
    else:
        import random

        recommended = random.sample(lectures, min(top_n, len(lectures)))
        return recommended, "random"
