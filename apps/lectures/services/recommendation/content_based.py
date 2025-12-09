import re
from typing import List, Optional, Tuple

import numpy as np
from scipy.sparse import spmatrix, vstack
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def embed_normalize(text: str) -> str:
    if not text:
        return ""
    vec = embedding_model.encode([text])[0]
    return " ".join([f"{v:.4f}" for v in vec])


def build_lecture_corpus(lecture: CrawledLecture) -> str:
    title = lecture.title or ""
    description = lecture.description or ""
    instructor = lecture.instructor or ""
    category_names = " ".join(cat.name for cat in lecture.categories.all())
    text = f"{title} {description} {instructor} {category_names}"
    text = clean_text(text)
    text = remove_stopwords(text)
    text = embed_normalize(text)
    return text


def build_user_vector(
    user: User,
    lecture_vectors: spmatrix,
    lecture_ids: List[int],
) -> Optional[np.ndarray]:
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
            vectors.append(lecture_vectors.getrow(idx))

    if not vectors:
        return None

    stacked = vstack(vectors)
    mean_vec = stacked.mean(axis=0)
    return np.asarray(mean_vec).ravel()


def recommend_lectures(user: User, top_n: int = 3) -> Tuple[List[CrawledLecture], str]:
    lectures = CrawledLecture.objects.prefetch_related("categories").all()
    if not lectures:
        return [], "lecture not crawled"

    corpus = [build_lecture_corpus(lec) for lec in lectures]
    lecture_ids = [lec.id for lec in lectures]

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    lecture_vectors = vectorizer.fit_transform(corpus)

    user_vec = build_user_vector(user, lecture_vectors, lecture_ids)

    if user_vec is not None:
        sims = cosine_similarity(user_vec, lecture_vectors).flatten()
        top_idx = sims.argsort()[::-1][:top_n]
        recommended = [lectures[i] for i in top_idx]
        return recommended, "personalized"
    else:
        import random

        recommended = random.sample(list(lectures), min(top_n, len(lectures)))
        return recommended, "random"
