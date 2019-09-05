from typing import List, Union, Dict, Optional, Type

from attr import dataclass

from datetime import datetime

from mautrix.types import JSON, SerializableAttrs, serializer, deserializer


@serializer(datetime)
def datetime_serializer(dt: datetime) -> JSON:
    return dt.strftime('%Y-%m-%dT%H:%M:%S%z')


@deserializer(datetime)
def datetime_deserializer(data: JSON) -> datetime:
    try:
        return datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError:
        pass

    try:
        return datetime.strptime(data, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        pass

    try:
        return datetime.strptime(data, '%Y-%m-%d %H:%M:%S %z')
    except ValueError:
        pass

    try:
        return datetime.strptime(data, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        pass

    try:
        return datetime.strptime(data, '%Y-%m-%d %H:%M:%S %Z')
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


@dataclass
class GitlabTarget(SerializableAttrs['GitlabTarget']):

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


@dataclass
class GitlabChange(SerializableAttrs['GitlabChange']):

    previous: Union[GitlabLabel, str, int]
    current: Union[GitlabLabel, str, int]


@dataclass
class GitlabLabelChanges(SerializableAttrs['GitlabLabelChanges']):

    previous: List[GitlabLabel]
    current: List[GitlabLabel]


@dataclass
class GitlabIssue(SerializableAttrs['GitlabIssue']):

    id: Optional[int] = None
    title: Optional[str] = None
    assignee_id: Optional[int] = None
    author_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    relative_position: Optional[int] = None
    branch_name: Optional[str] = None
    description: Optional[str] = None
    milestone_id: Optional[int] = None
    state: Optional[str] = None
    iid: Optional[int] = None


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
class GitlabObjectAttributes(SerializableAttrs['GitlabObjectAttributes']):

    action: Optional[str] = None
    id: Optional[int] = None
    author_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: Optional[str] = None
    note: Optional[str] = None
    noteable_type: Optional[str] = None
    project_id: Optional[int] = None
    attachment: Optional[str] = None
    line_code: Optional[str] = None
    commit_id: Optional[int] = None
    noteable_id: Optional[int] = None
    system: Optional[str] = None
    st_diff: Optional[GitlabStDiff] = None
    title: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None
    message: Optional[str] = None
    slug: Optional[str] = None
    target_branch: Optional[str] = None
    source_branch: Optional[str] = None
    source_project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    milestone_id: Optional[int] = None
    state: Optional[str] = None
    merge_status: Optional[str] = None
    target_project_id: Optional[int] = None
    iid: Optional[int] = None
    description: Optional[str] = None
    source: Optional[GitlabSource] = None
    target: Optional[GitlabTarget] = None
    last_commit: Optional[GitlabCommit] = None
    work_in_progress: Optional[bool] = None
    assignee: Optional[str] = None
    ref: Optional[str] = None
    tag: Optional[str] = None
    sha: Optional[str] = None
    before_sha: Optional[str] = None
    status: Optional[str] = None
    stages: Optional[List[str]] = None
    finished_at: Optional[datetime] = None
    duration: Optional[float] = None
    variables: Optional[List[dict]] = None
    assignee_ids: Optional[List[int]] = None
    relative_position: Optional[int] = None
    branch_name: Optional[str] = None
    confidential: Optional[bool] = None
    total_time_spent: Optional[int] = None


@dataclass
class GitlabArtifact(SerializableAttrs['GitlabArtifact']):

    file_name: str
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
    iid: int
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


@dataclass
class GitlabPushEvent(SerializableAttrs['GitlabPushEvent']):

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

    def handle(self) -> str:
        branch = self.ref.replace('refs/heads/', '')

        if self.total_commits_count == 0:
            msg = ("\[{2!s}/{3!s}\] {4!s} force pushed to "  # noqa: W605
                   "or deleted branch [{1!s}]({0!s}/tree/{1!s})")
            return msg.format(self.project.web_url,
                              branch,
                              self.project.namespace,
                              self.project.name,
                              self.user_name
                              )

            pluralizer: str = ''
        if self.total_commits_count != 1:
            pluralizer = 's'

        msg = ("\[[{2!s}/{3!s}]({0!s}/tree/{1!s})\] "  # noqa: W605
               "{4:d} new commit{6!s} by {5!s}\n\n")
        msg = msg.format(self.project.web_url,
                         branch,
                         self.project.namespace,
                         self.project.name,
                         self.total_commits_count,
                         self.user_name,
                         pluralizer
                         )

        for commit in reversed(self.commits):
            lines = commit.message.split('\n')
            if len(lines) > 1 and len(''.join(lines[1:])) > 0:
                lines[0] += " (...)"
            msg += "+ {0!s} ({1!s})\n".format(lines[0], commit.id[:8])

        return msg


@dataclass
class GitlabTagEvent(SerializableAttrs['GitlabTagEvent']):

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

    def handle(self) -> Optional[str]:

        if self.object_kind != 'tag_push':
            return None

        tag = self.ref.replace('refs/tags', '')

        msg = ("\[{0!s}/{1!s}\] {2!s} created tag "  # noqa: W605
               "[{4!s}]({3!s}/tags/{4!s})")
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user_name,
                          self.project.web_url,
                          tag
                          )


@dataclass
class GitlabIssueEvent(SerializableAttrs['GitlabIssueEvent']):

    object_kind: str
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabObjectAttributes
    assignees: Optional[List[GitlabAssignee]] = None
    labels: Optional[List[GitlabLabel]] = None
    changes: Optional[Dict[str, GitlabChange]] = None

    def handle(self) -> Optional[str]:

        action = self.object_attributes.action
        if not action or action == 'update' or len(action) == 0:
            return None
        elif not action[-2:-1] == 'ed':
            action += 'ed'

        confidential = ''
        if self.object_attributes.confidential:
            confidential = 'confidential '

        msg = ("\[{0!s}/{1!s}\] {2!s} {3!s} {4!s}issue "  # noqa: W605
               "[{6!s} (#{7:d})]({5!s})")
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user.name,
                          action,
                          confidential,
                          self.object_attributes.url,
                          self.object_attributes.title,
                          self.object_attributes.iid
                          )


@dataclass
class GitlabCommentEvent(SerializableAttrs['GitlabCommentEvent']):

    object_kind: str
    user: GitlabUser
    project_id: int
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabObjectAttributes
    merge_request: Optional[GitlabMergeRequest] = None
    commit: Optional[GitlabCommit] = None
    issue: Optional[GitlabIssue] = None
    snippet: Optional[GitlabSnippet] = None

    def handle(self) -> Optional[str]:

        noteable_type = self.object_attributes.noteable_type
        if self.issue and noteable_type == 'Issue':
            note_type = 'issue'
            note_identifier = '#'
            title = self.issue.title
            id = self.issue.iid
        elif self.merge_request and noteable_type == 'MergeRequest':
            note_type = 'merge request'
            note_identifier = '!'
            title = self.merge_request.title
            id = self.merge_request.iid
        else:
            return None

        msg = ("\[{0!s}/{1!s}\] {2!s} [commented]({4!s}) on "  # noqa: W605
               "{3!s} {5!s} ({7!s}{6:d}):\n\n{8!s}")
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user.name,
                          note_type,
                          self.object_attributes.url,
                          title,
                          id,
                          note_identifier,
                          self.object_attributes.note
                          )


@dataclass
class GitlabMergeRequestEvent(SerializableAttrs['GitlabMergeRequestEvent']):

    object_kind: str
    user: GitlabUser
    project: GitlabProject
    repository: GitlabRepository
    object_attributes: GitlabObjectAttributes
    labels: List[GitlabLabel]
    changes: Dict[str, GitlabChange]

    def handle(self) -> Optional[str]:

        action = self.object_attributes.action

        if (not action or action == 'update'
                or not self.object_attributes.target):
            return None
        elif not action[-2:-1] == 'ed':
            action += 'ed'

        msg = ("\[{0!s}/{1!s}\] {2!s} {3!s} merge request "  # noqa W605
               "[{5!s} (!{6:d})]({4!s})")
        return msg.format(self.object_attributes.target.namespace,
                          self.object_attributes.target.name,
                          self.user.name,
                          action,
                          self.object_attributes.url,
                          self.object_attributes.title,
                          self.object_attributes.iid
                          )


@dataclass
class GitlabWikiPageEvent(SerializableAttrs['GitlabWikiPageEvent']):

    object_kind: str
    user: GitlabUser
    project: GitlabProject
    wiki: GitlabWiki
    object_attributes: GitlabObjectAttributes

    def handle(self) -> Optional[str]:

        action = self.object_attributes.action

        if not action:
            return None
        if not action[-2:-1] == 'ed':
            action += 'ed'

        msg = ("\[{0!s}/{1!s}\] {2!s} {3!s}d page on wiki "  # noqa W605
               "[{5!s} (#{6:d})]({5!s})")
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user.name,
                          action,
                          self.object_attributes.url,
                          self.object_attributes.title,
                          self.object_attributes.iid
                          )


@dataclass
class GitlabPipelineEvent(SerializableAttrs['GitlabPipelineEvent']):

    object_kind: str
    object_attributes: GitlabObjectAttributes
    user: GitlabUser
    project: GitlabProject
    commit: GitlabCommit
    builds: List[GitlabBuild]

    def handle(self) -> str:

        pluralizer = ''
        if not len(self.builds) == 1:
            pluralizer = 's'

        duration = self.object_attributes.duration

        msg = ("\[{0!s}/{1!s}\] {2} pipeline{3!s} "  # noqa: W605
               "completed in {4!s}\n\n")
        msg = msg.format(self.project.namespace,
                         self.project.name,
                         len(self.builds),
                         pluralizer,
                         duration
                         )

        for build in self.builds:
            msg += "+ [{2!s}:{3!s} ({1})]({0!s}/-/jobs/{1}) {4!s}\n"
            msg = msg.format(self.project.web_url,
                             build.id,
                             build.name,
                             build.stage,
                             build.status
                             )

        return msg


@dataclass
class GitlabJobEvent(SerializableAttrs['GitlabJobEvent']):

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
    build_duration: float
    build_allow_failure: bool
    build_failure_reason: str
    project_id: int
    project_name: str
    user: GitlabUser
    commit: GitlabCommit
    repository: GitlabRepository

    def handle(self) -> str:

        namespace = self.project_name.replace(' ', '').split('/')[1]
        name = self.project_name.replace(' ', '').split('/')[2]

        msg = ("\[{0!s}/{1!s}\] job "  # noqa: W605
               "[{2!s}:{3!s} ({4})]({5!s}/-/jobs/{4}) {6!s}")
        return msg.format(namespace,
                          name,
                          self.build_name,
                          self.build_stage,
                          self.build_id,
                          self.repository.homepage,
                          self.build_status
                          )


GitlabEventType = Union[Type[GitlabPushEvent],
                        Type[GitlabTagEvent],
                        Type[GitlabIssueEvent],
                        Type[GitlabCommentEvent],
                        Type[GitlabMergeRequestEvent],
                        Type[GitlabWikiPageEvent],
                        Type[GitlabPipelineEvent],
                        Type[GitlabJobEvent]
                        ]


EventParse: Dict[str, GitlabEventType] = {
        'Push Hook': GitlabPushEvent,
        'Tag Push Hook': GitlabTagEvent,
        'Issue Hook': GitlabIssueEvent,
        'Note Hook': GitlabCommentEvent,
        'Merge Request Hook': GitlabMergeRequestEvent,
        'Wiki Page Hook': GitlabWikiPageEvent,
        'Pipeline Hook': GitlabPipelineEvent,
        'Job Hook': GitlabJobEvent
        }
