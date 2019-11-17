# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2019 Tulir Asokan
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
from typing import List, Union, Dict, Optional, Type, NewType
from datetime import datetime

from attr import dataclass
import attr

from mautrix.types import JSON, SerializableAttrs, SerializerError, Obj, serializer, deserializer


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

    raise ValueError(data)


@dataclass
class GitlabLabel(SerializableAttrs['GitlabLabel']):
    id: int
    title: str
    color: str
    project_id: int
    created_at: datetime
    updated_at: datetime
    template: bool
    description: str
    type: str
    group_id: int


@dataclass
class GitlabAssignee(SerializableAttrs['GitlabAssignee']):
    name: str
    username: str
    avatar_url: str


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


@dataclass
class GitlabCommit(SerializableAttrs['GitlabCommit']):
    id: str
    message: str
    timestamp: Optional[datetime] = None
    url: Optional[str] = None
    author: Optional[str] = None
    added: Optional[List[str]] = None
    modified: Optional[List[str]] = None
    removed: Optional[List[str]] = None


@dataclass
class GitlabAuthor(SerializableAttrs['GitlabAuthor']):
    name: str
    email: str


@dataclass
class GitlabRepository(SerializableAttrs['GitlabRepository']):
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    git_http_url: Optional[str] = None
    git_ssh_url: Optional[str] = None
    visibility_level: Optional[int] = None


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

GitlabChangeState = NewType('GitlabChangeState', Union[List[GitlabLabel], List[GitlabAssignee],
                                                       str, int])


@deserializer(GitlabChangeState)
def deserialize_change_state(val: JSON) -> GitlabChangeState:
    if isinstance(val, list):
        return [deserialize_change_state(item) for item in val]
    elif isinstance(val, dict):
        try:
            return GitlabLabel.deserialize(val)
        except SerializerError:
            pass
        try:
            return GitlabAssignee.deserialize(val)
        except SerializerError:
            pass
        return Obj(**val)
    return val


@dataclass
class GitlabChange(SerializableAttrs['GitlabChange']):
    previous: GitlabChangeState
    current: GitlabChangeState


@dataclass
class GitlabLabelChanges(SerializableAttrs['GitlabLabelChanges']):
    previous: List[GitlabLabel]
    current: List[GitlabLabel]


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


@dataclass
class GitlabUser(SerializableAttrs['GitlabUser']):
    name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    id: Optional[int] = None
    email: Optional[str] = None


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

    action: Optional[str] = None
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
    noteable_type: str
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
    action: Optional[str] = None


@dataclass
class GitlabWikiPageAttributes(SerializableAttrs['GitlabWikiAttributes']):
    title: str
    content: str
    format: str
    slug: str
    url: str
    action: str
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
    assignee: GitlabAssignee


@dataclass
class GitlabBuild(SerializableAttrs['GitlabBuild']):
    id: int
    stage: str
    name: str
    status: str
    created_at: datetime
    started_at: datetime
    finished_at: datetime
    when: str
    manual: bool
    user: GitlabUser
    runner: str
    artifacts_file: GitlabArtifact


class GitlabEvent:
    @property
    def has_matrix_message(self) -> bool:
        return True

    @property
    def matrix_message(self) -> Optional[str]:
        return "Missing message content"

    @property
    def matrix_message_edit_id(self) -> Optional[str]:
        return None


@dataclass
class GitlabPushEvent(SerializableAttrs['GitlabPushEvent'], GitlabEvent):
    object_kind: str
    before: str
    after: str
    ref: str
    checkout_sha: str
    user_id: int
    user_name: str
    user_email: str
    user_avatar: str
    project_id: int
    project: GitlabProject
    repository: GitlabRepository
    commits: List[GitlabCommit]
    total_commits_count: int

    def format_commit(self, commit: GitlabCommit) -> str:
        lines = commit.message.strip().split("\n")
        message = lines[0][:80]
        if len(lines[0]) > 80:
            message += "…"
        elif len(lines) > 1:
            message += " (…)"
        return f"* [{commit.id[:8]}]({self.project.web_url}/commit/{commit.id}): {message}"

    @property
    def pluralizer(self) -> str:
        return "s" if self.total_commits_count != 1 else ""

    @property
    def branch(self) -> str:
        return self.ref.replace("refs/heads/", "")

    @property
    def has_matrix_message(self) -> bool:
        return True

    @property
    def matrix_message(self) -> str:
        branch = self.branch

        if self.total_commits_count == 0:
            return (f"[{self.project.namespace} / {self.project.name}] {self.user_name}"
                    " force pushed to, created or deleted branch"
                    f" [{branch}]({self.project.web_url}/tree/{branch})")

        return (f"[{self.project.namespace} / {self.project.name}] "
                f"{self.total_commits_count} new commit{self.pluralizer} "
                f"to [{branch}]({self.project.web_url}/tree/{branch}) "
                f"by {self.user_name}\n\n"
                + "\n".join(self.format_commit(commit) for commit in reversed(self.commits)))


@dataclass
class GitlabTagEvent(SerializableAttrs['GitlabTagEvent'], GitlabEvent):
    object_kind: int
    before: str
    after: str
    ref: str
    checkout_sha: str
    user_id: int
    user_name: str
    user_avatar: str
    project_id: int
    project: GitlabProject
    repository: GitlabRepository
    commits: List[GitlabCommit]
    total_commits_count: int

    @property
    def tag(self) -> str:
        return self.ref.replace("refs/tags/", "")

    @property
    def has_matrix_message(self) -> bool:
        return self.object_kind == "tag_push"

    @property
    def matrix_message(self) -> Optional[str]:
        if self.object_kind != "tag_push":
            return None

        tag = self.tag
        return (f"[{self.project.namespace} / {self.project.name}] {self.user_name} created tag "
                f"[{tag}]({self.project.web_url}/tags/{tag}) at commit {self.checkout_sha[:8]}")


def past_tense(action: str) -> str:
    if not action:
        return action
    elif action[-2:-1] != "ed":
        if action[-1] == "e":
            return f"{action}d"
        return f"{action}ed"
    return action


@dataclass
class GitlabIssueEvent(SerializableAttrs['GitlabIssueEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabIssueAttributes
    assignees: Optional[List[GitlabAssignee]] = None
    labels: Optional[List[GitlabLabel]] = None
    changes: Optional[Dict[str, GitlabChange]] = None

    @property
    def has_matrix_message(self) -> bool:
        return bool(self.object_attributes.action and self.object_attributes.action != "update")

    @property
    def matrix_message(self) -> Optional[str]:
        action = past_tense(self.object_attributes.action)
        if not action or action == "updated":
            return None

        confidential = ""
        if self.object_attributes.confidential:
            confidential = "confidential "

        return (f"[{self.project.namespace} / {self.project.name}] {self.user.name} {action} "
                f"{confidential}issue [{self.object_attributes.title} "
                f"(#{self.object_attributes.issue_id})]({self.object_attributes.url})")


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

    @property
    def has_matrix_message(self) -> bool:
        nt = self.object_attributes.noteable_type
        return (nt == "Issue" and self.issue) or (nt == "MergeRequest" and self.merge_request)

    @property
    def matrix_message(self) -> Optional[str]:
        noteable_type = self.object_attributes.noteable_type
        if self.issue and noteable_type == "Issue":
            note_type = "issue"
            id = f"#{self.issue.issue_id}"
            title = self.issue.title
        elif self.merge_request and noteable_type == "MergeRequest":
            note_type = "merge request"
            id = f"!{self.merge_request.merge_request_id}"
            title = self.merge_request.title
        else:
            return None

        note = "\n".join(f"> {line}" for line in self.object_attributes.note.split("\n"))

        return (f"[{self.project.namespace} / {self.project.name}] {self.user.name} "
                f"[commented]({self.object_attributes.url}) on {note_type} {title} ({id}):\n\n"
                f"{note}")


@dataclass
class GitlabMergeRequestEvent(SerializableAttrs['GitlabMergeRequestEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabMergeRequestAttributes
    labels: List[GitlabLabel]
    changes: Dict[str, GitlabChange]

    @property
    def has_matrix_message(self) -> bool:
        return self.object_attributes.action != "update"

    @property
    def matrix_message(self) -> Optional[str]:
        action = past_tense(self.object_attributes.action)

        if not action or action == "updated" or not self.object_attributes.target:
            return None

        return (f"[{self.project.namespace} / {self.project.name}] {self.user.name} {action} "
                f"merge request [{self.object_attributes.title} "
                f"(!{self.object_attributes.merge_request_id})]({self.object_attributes.url})")


@dataclass
class GitlabWikiPageEvent(SerializableAttrs['GitlabWikiPageEvent'], GitlabEvent):
    object_kind: str
    user: GitlabUser
    project: GitlabProject
    wiki: GitlabWiki
    object_attributes: GitlabWikiPageAttributes

    @property
    def has_matrix_message(self) -> bool:
        return bool(self.object_attributes.action)

    @property
    def matrix_message(self) -> Optional[str]:
        action = past_tense(self.object_attributes.action)

        if not action:
            return None

        return (f"[{self.project.namespace} / {self.project.name}] {self.user.name} {action} "
                f"page on wiki [{self.object_attributes.title}]({self.object_attributes.url})")


def pluralize(val: int, unit: str) -> str:
    if val == 1:
        return f"{val} {unit}"
    return f"{val} {unit}s"


def format_duration(seconds: Union[int, float]) -> str:
    seconds = round(seconds, 1)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days > 0:
        parts.append(pluralize(days, "day"))
    if hours > 0:
        parts.append(pluralize(hours, "hour"))
    if minutes > 0:
        parts.append(pluralize(minutes, "minute"))
    if seconds > 0:
        parts.append(pluralize(seconds, "second"))

    if len(parts) == 1:
        return "in " + parts[0]
    return "in " + ", ".join(parts[:-1]) + f" and {parts[-1]}"


@dataclass
class GitlabPipelineEvent(SerializableAttrs['GitlabPipelineEvent'], GitlabEvent):
    object_kind: str
    object_attributes: GitlabPipelineAttributes
    user: GitlabUser
    project: GitlabProject
    commit: GitlabCommit
    builds: List[GitlabBuild]

    @property
    def formatted_duration(self) -> str:
        return format_duration(self.object_attributes.duration)

    @property
    def matrix_message_edit_id(self) -> str:
        return f"pipeline-{self.object_attributes.id}"

    @property
    def has_matrix_message(self) -> bool:
        return self.object_attributes.status in ("pending", "running", "success", "failed")

    @property
    def matrix_message(self) -> str:
        type = "tag" if self.object_attributes.tag else "branch"
        prefix = (f"[{self.project.namespace} / {self.project.name}] "
                  f"Pipeline {self.object_attributes.id} on {type} {self.object_attributes.ref}")

        if self.object_attributes.status == "pending":
            return f"{prefix} pending"
        elif self.object_attributes.status == "running":
            return f"{prefix} started"

        builds = "\n".join(f"* [{build.name}:{build.stage} ({build.id})]"
                           f"({self.project.web_url}/-/jobs/{build.id}) - {build.status}"
                           for build in self.builds)

        if self.object_attributes.status == "success":
            return f"{prefix} successfully completed in {self.formatted_duration}\n\n{builds}"
        elif self.object_attributes.status == "failed":
            return f"{prefix} failed in {self.formatted_duration}\n\n{builds}"


@dataclass
class GitlabJobEvent(SerializableAttrs['GitlabJobEvent'], GitlabEvent):
    object_kind: str
    ref: str
    tag: str
    before_sha: str
    sha: str
    build_id: int
    build_name: str
    build_stage: str
    build_status: str
    build_started_at: datetime
    build_finished_at: datetime
    build_duration: int
    build_allow_failure: bool
    build_failure_reason: str
    project_id: int
    project_name: str
    user: GitlabUser
    commit: GitlabCommit
    repository: GitlabRepository

    @property
    def formatted_build_duration(self) -> str:
        return format_duration(self.build_duration)

    @property
    def matrix_message_edit_id(self) -> str:
        return f"job-{self.build_id}"

    @property
    def has_matrix_message(self) -> bool:
        return self.build_status in ("pending", "running", "skipped", "success", "failed")

    @property
    def matrix_message(self) -> str:
        prefix = (f"[{self.project_name}] Job [{self.build_name}:{self.build_stage} "
                  f"({self.build_id})]({self.repository.homepage}/-/jobs/{self.build_id}) ")
        if self.build_status == "pending":
            return f"{prefix} pending"
        elif self.build_status == "running":
            return f"{prefix} started"
        elif self.build_status == "skipped":
            return f"{prefix} skipped"
        elif self.build_status == "success":
            return f"{prefix} successfully completed in {self.formatted_build_duration}"
        elif self.build_status == "failed":
            return f"{prefix} failed in {self.formatted_build_duration}"


GitlabEventType = Union[Type[GitlabPushEvent],
                        Type[GitlabTagEvent],
                        Type[GitlabIssueEvent],
                        Type[GitlabCommentEvent],
                        Type[GitlabMergeRequestEvent],
                        Type[GitlabWikiPageEvent],
                        Type[GitlabPipelineEvent],
                        Type[GitlabJobEvent]]

EventParse: Dict[str, GitlabEventType] = {
    "Push Hook": GitlabPushEvent,
    "Tag Push Hook": GitlabTagEvent,
    "Issue Hook": GitlabIssueEvent,
    "Confidential Issue Hook": GitlabIssueEvent,
    "Note Hook": GitlabCommentEvent,
    "Merge Request Hook": GitlabMergeRequestEvent,
    "Wiki Page Hook": GitlabWikiPageEvent,
    "Pipeline Hook": GitlabPipelineEvent,
    "Job Hook": GitlabJobEvent
}
