import re
from typing import List, Optional, Tuple

import numpy as np
from scipy.sparse import spmatrix, vstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyLecture
from apps.users.models import User

TECH_MAP = {
    r"(?i)\bpython\b": "python",
    r"(?i)\bpy\b": "python",
    r"파이썬": "python",
    r"pyhton": "python",
    r"(?i)\bjavascript\b": "javascript",
    r"(?i)\bjs\b": "javascript",
    r"자바스크립트": "javascript",
    r"(?i)\btypescript\b": "typescript",
    r"타입스크립트": "typescript",
    r"ts\b": "typescript",
    r"(?i)\breact\b": "react",
    r"리액트": "react",
    r"(?i)\breact[\s\.-]*js\b": "react",
    r"(?i)\bvue\b": "vue",
    r"뷰": "vue",
    r"(?i)\bangular\b": "angular",
    r"앵귤러": "angular",
    r"(?i)\bdjango\b": "django",
    r"장고": "django",
    r"(?i)\bflask\b": "flask",
    r"플라스크": "flask",
    r"(?i)\bfastapi\b": "fastapi",
    r"패스트api": "fastapi",
    r"(?i)\bnode\.?js\b": "nodejs",
    r"노드": "nodejs",
    r"(?i)\bmysql\b": "mysql",
    r"마이에스큐엘": "mysql",
    r"(?i)\bpostgresql\b": "postgresql",
    r"포스트그레스": "postgresql",
    r"(?i)\bmongodb\b": "mongodb",
    r"몽고db": "mongodb",
    r"(?i)\bmachine\s+learning\b": "machine learning",
    r"(?i)\bml\b": "machine learning",
    r"머신러닝": "machine learning",
    r"(?i)\bdeep\s+learning\b": "deep learning",
    r"딥러닝": "deep learning",
    r"(?i)\btensorflow\b": "tensorflow",
    r"텐서플로": "tensorflow",
    r"(?i)\btorch\b": "pytorch",
    r"파이토치": "pytorch",
    r"(?i)\bscikit[-\s]?learn\b": "scikit-learn",
    r"사이킷런": "scikit-learn",
    r"(?i)\baws\b": "aws",
    r"아마존\s*웹\s*서비스": "aws",
    r"(?i)\bazure\b": "azure",
    r"애저": "azure",
    r"(?i)\bgcp\b": "gcp",
    r"구글\s*클라우드": "gcp",
    r"(?i)\bdocker\b": "docker",
    r"도커": "docker",
    r"(?i)\bkubernetes\b": "kubernetes",
    r"쿠버네티스": "kubernetes",
    r"(?i)\bpandas\b": "pandas",
    r"판다스": "pandas",
    r"(?i)\bnumpy\b": "numpy",
    r"넘파이": "numpy",
    r"(?i)\bmatplotlib\b": "matplotlib",
    r"맷플롯립": "matplotlib",
    r"(?i)\bseaborn\b": "seaborn",
    r"시본": "seaborn",
    r"git\b": "git",
    r"깃": "git",
    r"linux\b": "linux",
    r"리눅스": "linux",
}

STOPWORDS = {"강의", "수업", "소개", "배우기", "공부", "사용법"}


def remove_stopwords(text: str) -> str:
    for word in STOPWORDS:
        text = text.replace(word, "")
    return text


def normalize_tech(text: str) -> str:
    if not text:
        return ""
    for pattern, replacement in TECH_MAP.items():
        text = re.sub(pattern, replacement, text)
    return text


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_lecture_corpus(lecture: CrawledLecture) -> str:
    title = lecture.title or ""
    description = lecture.description or ""
    instructor = lecture.instructor or ""
    category_names = " ".join(cat.name for cat in lecture.categories.all())
    return f"{title} {description} {instructor} {category_names}"


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
    return stacked.mean(axis=0)


def recommend_lectures(user: User, top_n: int = 3) -> Tuple[List[CrawledLecture], str]:
    lectures = CrawledLecture.objects.prefetch_related("categories").all()
    if not lectures:
        return [], "lecture not crawled"

    corpus = [remove_stopwords(normalize_tech(clean_text(build_lecture_corpus(lec)))) for lec in lectures]
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
