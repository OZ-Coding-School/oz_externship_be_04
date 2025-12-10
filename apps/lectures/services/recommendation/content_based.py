import re
from typing import List, Optional, Tuple

import numpy as np
from numpy._typing import NDArray
from sentence_transformers import SentenceTransformer

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyLecture
from apps.users.models import User

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

STOPWORDS = {"강의", "수업", "소개", "배우기", "공부", "사용법"}


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

    vec: NDArray[np.float32] = embedding_model.encode([text])[0]

    norm = np.float32(np.linalg.norm(vec))
    if norm == 0:
        return vec
    return vec / norm


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
    for lec_id in user_lecture_ids:
        idx = id_to_idx.get(lec_id)
        if idx is not None:
            vectors.append(lecture_vectors[idx])

    if not vectors:
        return None

    mean_vec: NDArray[np.float32] = np.mean(np.vstack(vectors), axis=0)

    norm = np.float32(np.linalg.norm(mean_vec))
    if norm == 0:
        return mean_vec
    return mean_vec / norm


def recommend_lectures(user: User, top_n: int = 3) -> Tuple[List[CrawledLecture], str]:
    lectures = list(CrawledLecture.objects.prefetch_related("categories").all())
    if not lectures:
        return [], "lecture not crawled"

    lecture_ids = [lec.id for lec in lectures]
    lecture_vectors = np.vstack([build_lecture_embedding_vector(lec) for lec in lectures])

    user_vec = build_user_vector(user, lecture_vectors, lecture_ids)

    if user_vec is not None:
        sims = lecture_vectors @ user_vec
        top_idx = np.argsort(sims)[::-1][:top_n]
        recommended = [lectures[i] for i in top_idx]
        return recommended, "personalized"
    else:
        import random

        recommended = random.sample(lectures, min(top_n, len(lectures)))
        return recommended, "random"
