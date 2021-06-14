# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2021 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import List, Union, Dict, Optional, Type, NewType, ClassVar, Tuple, Iterable
from datetime import datetime

from jinja2 import TemplateNotFound
from attr import dataclass
from yarl import URL
import attr

from mautrix.types import JSON, ExtensibleEnum, SerializableAttrs, serializer, deserializer

from .util import contrast, hex_to_rgb


@serializer(datetime)
def datetime_serializer(dt: datetime) -> JSON:
    return dt.strftime('%Y-%m-%dT%H:%M:%S%z')


@deserializer(datetime)
def datetime_deserializer(data: JSON) -> datetime:
    try:
        return datetime.strptime(data, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        pass

    try:
        return datetime.strptime(data, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        pass

    try:
        return datetime.strptime(data, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        pass

    try:
        return datetime.strptime(data, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pass

    try:
        return datetime.strptime(data, "%Y-%m-%d %H:%M:%S %Z")
    except ValueError:
        pass

    try:
        return datetime.strptime(data, "%Y-%m-%d")
    except ValueError:
        pass

    raise ValueError(data)


class LabelType(ExtensibleEnum):
    PROJECT = "ProjectLabel"
    # TODO group?


@dataclass(frozen=True)
class GitlabLabel(SerializableAttrs['GitlabLabel']):
    contrast_threshold: ClassVar[float] = 1.5
    white_rgb: ClassVar[Tuple[int, int, int]] = (1, 1, 1)
    white_hex: ClassVar[str] = "#ffffff"
    black_hex: ClassVar[str] = "#000000"

    id: int
    title: str
    color: str
    project_id: int
    created_at: datetime
    updated_at: datetime
    template: bool
    description: str
    type: LabelType
    group_id: Optional[int]
    remove_on_close: bool

    @property
    def foreground_color(self) -> str:
        return (self.white_hex
                if contrast(hex_to_rgb(self.color), self.white_rgb) >= self.contrast_threshold
                else self.black_hex)


@dataclass
class GitlabProject(SerializableAttrs['GitlabProject']):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    web_url: Optional[str] = None
    avatar_url: Optional[str] = None
    git_ssh_url: Optional[str] = None
    git_http_url: Optional[str] = None
    namespace: Optional[str] = None
    visibility_level: Optional[int] = None
    path_with_namespace: Optional[str] = None
    default_branch: Optional[str] = None
    homepage: Optional[str] = None
    url: Optional[str] = None
    ssh_url: Optional[str] = None
    http_url: Optional[str] = None

    @property
    def gitlab_base_url(self) -> str:
        return self.web_url.split(self.path_with_namespace)[0].rstrip("/")


@dataclass(eq=False, hash=False)
class GitlabUser(SerializableAttrs['GitlabUser']):
    name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    id: Optional[int] = None
    web_url: Optional[str] = None

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, other: 'GitlabUser') -> bool:
        if not isinstance(other, GitlabUser):
            return False
        return self.id == other.id


@dataclass
class GitlabAuthor(SerializableAttrs['GitlabAuthor']):
    name: str
    email: str


@dataclass
class BaseCommit:
    message: str

    @property
    def cut_message(self) -> str:
        max_len = 72
        message = self.message.strip()
        if "\n" in message:
            message = message.split("\n")[0]
            if len(message) <= max_len:
                message += " […]"
                return message
        if len(message) > max_len:
            message = message[:max_len] + "…"
        return message


@dataclass
class GitlabCommit(BaseCommit, SerializableAttrs['GitlabCommit']):
    id: str
    timestamp: Optional[datetime] = None
    url: Optional[str] = None
    author: Optional[GitlabAuthor] = None

    added: Optional[List[str]] = None
    modified: Optional[List[str]] = None
    removed: Optional[List[str]] = None


@dataclass
class GitlabRepository(SerializableAttrs['GitlabRepository']):
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    git_http_url: Optional[str] = None
    git_ssh_url: Optional[str] = None
    visibility_level: Optional[int] = None

    @property
    def path(self) -> str:
        return URL(self.homepage).path.strip("/")


@dataclass
class GitlabStDiff(SerializableAttrs['GitlabStDiff']):
    diff: str
    new_path: str
    old_path: str
    a_mode: str
    b_mode: str
    new_file: bool
    renamed_file: bool
    deleted_file: bool


@dataclass
class GitlabSource(SerializableAttrs['GitlabSource']):
    name: str
    namespace: str

    description: Optional[str] = None
    web_url: Optional[str] = None
    avatar_url: Optional[str] = None
    git_ssh_url: Optional[str] = None
    git_http_url: Optional[str] = None
    visibility_level: Optional[int] = None
    path_with_namespace: Optional[str] = None
    default_branch: Optional[str] = None
    homepage: Optional[str] = None
    url: Optional[str] = None
    ssh_url: Optional[str] = None
    http_url: Optional[str] = None


GitlabTarget = NewType('GitlabTarget', GitlabSource)


class GitlabChangeWrapper:
    previous: list
    current: list

    @property
    def added(self) -> list:
        previous_set = set(self.previous)
        return [item for item in self.current if item not in previous_set]

    @property
    def removed(self) -> list:
        current_set = set(self.current)
        return [item for item in self.previous if item not in current_set]


@dataclass
class GitlabDatetimeChange(SerializableAttrs['GitlabDatetimeChange']):
    previous: Optional[datetime]
    current: datetime


@dataclass
class GitlabAssigneeChanges(GitlabChangeWrapper, SerializableAttrs['GitlabAssigneeChanges']):
    previous: List[GitlabUser]
    current: List[GitlabUser]


@dataclass
class GitlabLabelChanges(GitlabChangeWrapper, SerializableAttrs['GitlabLabelChanges']):
    previous: List[GitlabLabel]
    current: List[GitlabLabel]


@dataclass
class GitlabIntChange(SerializableAttrs['GitlabIntChange']):
    previous: Optional[int]
    current: Optional[int]


@dataclass
class GitlabBoolChange(SerializableAttrs['GitlabBoolChange']):
    previous: Optional[bool]
    current: Optional[bool]


@dataclass
class GitlabStringChange(SerializableAttrs['GitlabStringChange']):
    previous: Optional[str]
    current: Optional[str]


@dataclass
class GitlabChanges(SerializableAttrs['GitlabChanges']):
    created_at: Optional[GitlabDatetimeChange] = None
    updated_at: Optional[GitlabDatetimeChange] = None
    updated_by: Optional[GitlabIntChange] = None
    author_id: Optional[GitlabIntChange] = None
    id: Optional[GitlabIntChange] = None
    iid: Optional[GitlabIntChange] = None
    project_id: Optional[GitlabIntChange] = None
    milestone_id: Optional[GitlabIntChange] = None
    description: Optional[GitlabStringChange] = None
    title: Optional[GitlabStringChange] = None
    labels: Optional[GitlabLabelChanges] = None
    assignees: Optional[GitlabAssigneeChanges] = None
    time_estimate: Optional[GitlabIntChange] = None
    total_time_spent: Optional[GitlabIntChange] = None
    weight: Optional[GitlabIntChange] = None
    due_date: Optional[GitlabDatetimeChange] = None
    confidential: Optional[GitlabBoolChange] = None
    discussion_locked: Optional[GitlabBoolChange] = None


@dataclass
class GitlabIssue(SerializableAttrs['GitlabIssue']):
    id: int
    issue_id: int = attr.ib(metadata={"json": "iid"})
    title: str
    description: str
    author_id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    assignee_id: Optional[int] = None
    assignee_ids: Optional[List[int]] = None
    relative_position: Optional[int] = None
    branch_name: Optional[str] = None
    milestone_id: Optional[int] = None
    state: Optional[str] = None


@dataclass
class GitlabSnippet(SerializableAttrs['GitlabSnippet']):
    id: int
    title: str
    content: str
    author_id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    file_name: str
    expires_at: datetime
    type: str
    visibility_level: int


class Action(ExtensibleEnum):
    OPEN = "open"
    CLOSE = "close"
    UPDATE = "update"
    CREATE = "create"
    DELETE = "delete"

    @property
    def past_tense(self) -> str:
        action = self.value
        if not action:
            return action
        elif action[-2:] != "ed":
            if action[-1] == "e":
                return f"{action}d"
            return f"{action}ed"
        return action


class NoteableType(ExtensibleEnum):
    ISSUE = "Issue"
    MERGE_REQUEST = "MergeRequest"


@dataclass
class GitlabIssueAttributes(SerializableAttrs['GitlabIssueAttributes']):
    id: int
    project_id: int
    issue_id: int = attr.ib(metadata={"json": "iid"})
    state: str
    url: str
    author_id: int
    title: str
    description: str

    created_at: datetime
    updated_at: datetime
    updated_by_id: Optional[int] = None
    due_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    time_estimate: Optional[int] = None
    total_time_spent: Optional[int] = None
    human_time_estimate: Optional[str] = None
    human_total_time_spent: Optional[str] = None

    action: Optional[Action] = None
    assignee_id: Optional[int] = None
    assignee_ids: Optional[List[int]] = None
    branch_name: Optional[str] = None
    confidential: bool = False
    duplicated_to_id: Optional[int] = None
    moved_to_id: Optional[int] = None
    state_id: Optional[int] = None
    milestone_id: Optional[int] = None
    labels: Optional[List[GitlabLabel]] = None
    position: Optional[int] = None
    original_position: Optional[int] = None


@dataclass
class GitlabCommentAttributes(SerializableAttrs['GitlabCommentAttributes']):
    id: int
    note: str
    noteable_type: NoteableType
    project_id: int
    url: str
    author_id: int

    created_at: datetime
    updated_at: datetime
    updated_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None

    commit_id: Optional[str] = None
    noteable_id: Optional[int] = None
    discussion_id: Optional[str] = None

    system: Optional[bool] = None
    line_code: Optional[str] = None
    st_diff: Optional[GitlabStDiff] = None
    attachment: Optional[str] = None
    position: Optional[int] = None
    original_position: Optional[int] = None


@dataclass
class GitlabMergeRequestAttributes(SerializableAttrs['GitlabMergeRequestAttributes']):
    id: int
    merge_request_id: int = attr.ib(metadata={"json": "iid"})
    target_branch: str
    source_branch: str
    source: GitlabProject
    source_project_id: int
    target: GitlabProject
    target_project_id: int
    last_commit: GitlabCommit
    author_id: int
    title: str
    description: str
    work_in_progress: bool
    url: str
    state: str

    created_at: datetime
    updated_at: datetime
    updated_by_id: Optional[int] = None
    last_edited_at: Optional[datetime] = None
    last_edited_by_id: Optional[int] = None

    merge_commit_sha: Optional[str] = None
    merge_error: Optional[str] = None
    merge_status: Optional[str] = None
    merge_user_id: Optional[int] = None
    merge_when_pipeline_succeeds: Optional[bool] = False

    time_estimate: Optional[int] = None
    total_time_spent: Optional[int] = None
    human_time_estimate: Optional[str] = None
    human_total_time_spent: Optional[str] = None

    head_pipeline_id: Optional[int] = None
    milestone_id: Optional[int] = None
    assignee_id: Optional[int] = None
    assignee_ids: Optional[List[int]] = None
    assignee: Optional[GitlabUser] = None
    action: Optional[Action] = None


@dataclass
class GitlabWikiPageAttributes(SerializableAttrs['GitlabWikiAttributes']):
    title: str
    content: str
    format: str
    slug: str
    url: str
    action: Action
    message: Optional[str] = None


@dataclass
class GitlabVariable(SerializableAttrs['GitlabVariable']):
    key: str
    value: str


@dataclass
class GitlabPipelineAttributes(SerializableAttrs['GitlabPipelineAttributes']):
    id: int
    ref: str
    tag: bool
    sha: str
    before_sha: str
    source: str
    status: str
    stages: List[str]

    created_at: datetime
    finished_at: datetime
    duration: int
    variables: List[GitlabVariable]


@dataclass
class GitlabArtifact(SerializableAttrs['GitlabArtifact']):
    filename: str
    size: int


@dataclass
class GitlabWiki(SerializableAttrs['GitlabWiki']):
    web_url: str
    git_ssh_url: str
    git_http_url: str
    path_with_namespace: str
    default_branch: str


@dataclass
class GitlabMergeRequest(SerializableAttrs['GitlabMergeRequest']):
    id: int
    merge_request_id: int = attr.ib(metadata={"json": "iid"})
    target_branch: str
    source_branch: str
    source_project_id: int
    assignee_id: int
    author_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    milestone_id: int
    state: str
    merge_status: str
    target_project_id: int
    description: str
    position: int
    locked_at: datetime
    source: GitlabSource
    target: GitlabTarget
    last_commit: GitlabCommit
    work_in_progress: bool
    assignee: GitlabUser


class BuildStatus(ExtensibleEnum):
    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    @property
    def color_circle(self) -> str:
        return _build_status_circles[self]


_build_status_circles: Dict[BuildStatus, str] = {
    BuildStatus.CREATED: "🟡",
    BuildStatus.RUNNING: "🔵",
    BuildStatus.SUCCESS: "🟢",
    BuildStatus.FAILED: "🔴",
}


class FailureReason(ExtensibleEnum):
    UNKNOWN = "unknown_failure"
    SCRIPT = "script_failure"


@dataclass
class GitlabJobCommit(BaseCommit, SerializableAttrs['GitlabJobCommit']):
    author_email: str
    author_name: str
    author_url: Optional[str]

    id: int
    sha: str
    status: BuildStatus
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration: Optional[int]


@dataclass
class GitlabBuild(SerializableAttrs['GitlabBuild']):
    id: int
    stage: str
    name: str
    status: BuildStatus
    created_at: datetime
    started_at: datetime
    finished_at: datetime
    when: str
    manual: bool
    user: GitlabUser
    runner: str
    artifacts_file: GitlabArtifact


@dataclass
class GitlabEvent:
    def preprocess(self) -> List['GitlabEvent']:
        return [self]

    @property
    def template_name(self) -> str:
        raise TemplateNotFound("")

    @property
    def meta(self) -> JSON:
        return {}

    @property
    def event_properties(self) -> Iterable[str]:
        return []

    @property
    def message_id(self) -> Optional[str]:
        return None


@dataclass
class GitlabPushEvent(SerializableAttrs['GitlabPushEvent'], GitlabEvent):
    object_kind: str
    before: str
    after: str
    ref: str
    checkout_sha: str
    message: Optional[str]
    user_id: int
    user_name: str
    user_username: str
    user_email: str
    user_avatar: str
    project_id: int
    project: GitlabProject
    repository: GitlabRepository
    commits: List[GitlabCommit]
    total_commits_count: int

    @property
    def user(self) -> GitlabUser:
        return GitlabUser(id=self.user_id, name=self.user_name, email=self.user_email,
                          username=self.user_username, avatar_url=self.user_avatar,
                          web_url=f"{self.project.gitlab_base_url}/{self.user_username}")

    @property
    def template_name(self) -> str:
        return "tag" if self.ref_type == "tag" else "push"

    @property
    def event_properties(self) -> Iterable[str]:
        return ("user", "is_new_ref", "is_deleted_ref", "ref_name", "ref_type", "ref_url",
                "diff_url")

    @property
    def diff_url(self) -> str:
        before = self.project.default_branch if self.is_new_ref else self.before
        after = self.after
        return f"{self.project.web_url}/-/compare/{before}...{after}"

    @property
    def is_new_ref(self) -> bool:
        return self.before == "0" * len(self.before)

    @property
    def is_deleted_ref(self) -> bool:
        return self.after == "0" * len(self.after)

    @property
    def ref_type(self) -> str:
        if self.ref.startswith("refs/heads/"):
            return "branch"
        elif self.ref.startswith("refs/tags/"):
            return "tag"
        else:
            return "ref"

    @property
    def ref_name(self) -> str:
        return self.ref.split("/", 2)[2]

    @property
    def ref_url(self) -> Optional[str]:
        if self.ref.startswith("refs/heads/"):
            return f"{self.project.web_url}/-/branches/{self.ref_name}"
        elif self.ref.startswith("refs/tags/"):
            return f"{self.project.web_url}/-/tags/{self.ref_name}"
        else:
            return None

    @property
    def message_id(self) -> str:
        return f"push-{self.checkout_sha}-{self.ref_name}"


def split_updates(evt: Union['GitlabIssueEvent', 'GitlabMergeRequestEvent']) -> List[GitlabEvent]:
    output = []
    # We don't want to handle multiple issue change types in a single Matrix message,
    # so split each change into a separate event.
    for field in attr.fields(GitlabChanges):
        value = getattr(evt.changes, field.name)
        if value:
            output.append(attr.evolve(evt, changes=GitlabChanges(**{field.name: value})))
    return output


@dataclass
class GitlabIssueEvent(SerializableAttrs['GitlabIssueEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabIssueAttributes
    assignees: Optional[List[GitlabUser]] = None
    labels: Optional[List[GitlabLabel]] = None
    changes: Optional[GitlabChanges] = None

    def preprocess(self) -> List['GitlabIssueEvent']:
        users_to_mutate = [self.user]
        if self.changes.assignees:
            users_to_mutate += self.changes.assignees.previous
            users_to_mutate += self.changes.assignees.current
        if self.assignees:
            users_to_mutate += self.assignees
        for user in users_to_mutate:
            user.web_url = f"{self.project.gitlab_base_url}/{user.username}"

        return split_updates(self) if self.action == Action.UPDATE else [self]

    @property
    def template_name(self) -> str:
        return f"issue_{self.action.key.lower()}"

    @property
    def event_properties(self) -> Iterable[str]:
        return "action",

    @property
    def action(self) -> Action:
        return self.object_attributes.action


@dataclass
class GitlabCommentEvent(SerializableAttrs['GitlabCommentEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project_id: int
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabCommentAttributes
    merge_request: Optional[GitlabMergeRequest] = None
    commit: Optional[GitlabCommit] = None
    issue: Optional[GitlabIssue] = None
    snippet: Optional[GitlabSnippet] = None

    def preprocess(self) -> List['GitlabCommentEvent']:
        self.user.web_url = f"{self.project.gitlab_base_url}/{self.user.username}"
        return [self]

    @property
    def template_name(self) -> str:
        return "comment"


@dataclass
class GitlabMergeRequestEvent(SerializableAttrs['GitlabMergeRequestEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabMergeRequestAttributes
    labels: List[GitlabLabel]
    changes: GitlabChanges

    def preprocess(self) -> List['GitlabMergeRequestEvent']:
        users_to_mutate = [self.user]
        if self.changes.assignees:
            users_to_mutate += self.changes.assignees.previous
            users_to_mutate += self.changes.assignees.current
        for user in users_to_mutate:
            user.web_url = f"{self.project.gitlab_base_url}/{user.username}"

        return split_updates(self) if self.action == Action.UPDATE else [self]

    @property
    def template_name(self) -> str:
        return "issue_update" if self.action == Action.UPDATE else "merge_request"

    @property
    def event_properties(self) -> Iterable[str]:
        return "action",

    @property
    def action(self) -> Action:
        return self.object_attributes.action


@dataclass
class GitlabWikiPageEvent(SerializableAttrs['GitlabWikiPageEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project: GitlabProject
    wiki: GitlabWiki
    object_attributes: GitlabWikiPageAttributes

    def preprocess(self) -> List['GitlabWikiPageEvent']:
        self.user.web_url = f"{self.project.gitlab_base_url}/{self.user.username}"
        return [self]

    @property
    def template_name(self) -> str:
        return "wiki"


@dataclass
class GitlabPipelineEvent(SerializableAttrs['GitlabPipelineEvent'], GitlabEvent):
    object_kind: str
    object_attributes: GitlabPipelineAttributes
    user: GitlabUser
    project: GitlabProject
    commit: GitlabCommit
    builds: List[GitlabBuild]

    @property
    def message_id(self) -> str:
        return f"pipeline-{self.object_attributes.id}"


@dataclass
class GitlabRunner(SerializableAttrs['GitlabRunner']):
    active: bool
    description: str
    id: int
    tags: List[str]


@dataclass
class GitlabJobEvent(SerializableAttrs['GitlabJobEvent'], GitlabEvent):
    object_kind: str
    ref: str
    tag: str
    before_sha: str
    sha: str
    pipeline_id: int
    build_id: int
    build_name: str
    build_stage: str
    build_status: BuildStatus
    build_started_at: datetime
    build_finished_at: datetime
    build_duration: int
    build_allow_failure: bool
    build_failure_reason: FailureReason
    project_id: int
    project_name: str
    user: GitlabUser
    commit: GitlabJobCommit
    repository: GitlabRepository
    runner: Optional[GitlabRunner]

    def preprocess(self) -> List['GitlabJobEvent']:
        base_url = str(URL(self.repository.homepage).with_path(""))
        self.user.web_url = f"{base_url}/{self.user.username}"
        return [self]

    @property
    def template_name(self) -> str:
        return "job"

    @property
    def push_id(self) -> str:
        return f"push-{self.sha}-{self.ref}"

    @property
    def reaction_id(self) -> str:
        return f"job-{self.sha}-{self.ref}-{self.build_name}"

    @property
    def meta(self) -> JSON:
        return {
            "build": {
                "pipeline_id": self.pipeline_id,
                "id": self.build_id,
                "name": self.build_name,
                "stage": self.build_stage,
                "status": self.build_status.value,
                "url": self.build_url,
            },
        }

    @property
    def event_properties(self) -> Iterable[str]:
        return "build_url",

    @property
    def build_url(self) -> str:
        return f"{self.repository.homepage}/-/jobs/{self.build_id}"


GitlabEventType = Union[Type[GitlabPushEvent],
                        Type[GitlabIssueEvent],
                        Type[GitlabCommentEvent],
                        Type[GitlabMergeRequestEvent],
                        Type[GitlabWikiPageEvent],
                        Type[GitlabPipelineEvent],
                        Type[GitlabJobEvent]]

EventParse: Dict[str, GitlabEventType] = {
    "Push Hook": GitlabPushEvent,
    "Tag Push Hook": GitlabPushEvent,
    "Issue Hook": GitlabIssueEvent,
    "Confidential Issue Hook": GitlabIssueEvent,
    "Note Hook": GitlabCommentEvent,
    "Confidential Note Hook": GitlabCommentEvent,
    "Merge Request Hook": GitlabMergeRequestEvent,
    "Wiki Page Hook": GitlabWikiPageEvent,
    "Pipeline Hook": GitlabPipelineEvent,
    "Job Hook": GitlabJobEvent
}

OTHER_ENUMS = {
    "NoteableType": NoteableType,
    "BuildStatus": BuildStatus,
    "FailureReason": FailureReason,
}
