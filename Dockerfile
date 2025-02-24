# 베이스 이미지
FROM python:3.11-slim as python-base

# # Python 관련 환경 변수 설정
# ENV PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     PIP_NO_CACHE_DIR=off \
#     PIP_DISABLE_PIP_VERSION_CHECK=on \
#     PIP_DEFAULT_TIMEOUT=100 \
#     POETRY_VERSION=1.7.1 \
#     POETRY_HOME="/opt/poetry" \
#     POETRY_VIRTUALENVS_IN_PROJECT=true \
#     POETRY_NO_INTERACTION=1 \
#     PYSETUP_PATH="/opt/pysetup" \
#     VENV_PATH="/opt/pysetup/.venv"

# # PATH에 Poetry와 venv 추가
# ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# # 빌더 이미지
# FROM python-base as builder-base
# RUN apt-get update \
#     && apt-get install --no-install-recommends -y \
#         curl \
#         build-essential

# # Poetry 설치
# RUN curl -sSL https://install.python-poetry.org | python3 -

# # 프로젝트 의존성 설치
# WORKDIR $PYSETUP_PATH

RUN pip install poetry
WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root 

# 실행 이미지
# FROM python-base as production
# COPY --from=builder-base $POETRY_HOME $POETRY_HOME
# COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY . .

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]