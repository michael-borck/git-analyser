from pydantic import BaseModel


class CommitSummary(BaseModel):
    hash: str
    date: str
    subject: str
    additions: int
    deletions: int
    file_count: int


class LearningSignals(BaseModel):
    commit_count: int
    total_additions: int
    total_deletions: int
    add_delete_ratio: float
    avg_message_length: float
    generic_message_ratio: float
    time_span_hours: float
    max_gap_hours: float
    commit_regularity_cv: float


class GitAnalysisResult(BaseModel):
    repo: str
    commit_count: int
    authors: list[str]
    timeline: list[CommitSummary]
    suspicious_flags: list[str]
    learning_signals: LearningSignals
    error: str | None = None
