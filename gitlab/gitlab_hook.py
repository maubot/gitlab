from types import List


class GitlabPushEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.before = body['before']
        self.after = body['after']
        self.ref = body['ref']
        self.checkout_sha = body['checkout_sha']
        self.user_id = body['user_id']
        self.user_name = body['user_name']
        self.user_email = body['user_email']
        self.user_avatar = body['user_avatar']
        self.project_id = body['project_id']
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.commits = [GitlabCommit(commit) for commit in body['commits']]
        self.total_commits_count: int = int(body['total_commits_count'])

    def handle(self) -> str:
        branch = self.ref.replace('refs/heads/', '')

        if self.total_commits_count == 0:
            msg = "\[{2!s}/{3!s}\] {4!s} force pushed to" \
                    "or deleted branch [{1!s}]({0!s}/tree/{1!s})"  # noqa: W605
            return msg.format(self.project.web_url,
                              branch,
                              self.project.namespace,
                              self.project.name,
                              self.user_name
                              )

            pluralizer: str = ''
        if self.total_commits_count != 1:
            pluralizer = 's'

        msg = "\[[{2!s}/{3!s}]({0!s}/tree/{1!s})\] " \
                "{4:d} new commit{6!s} by {5!s}\n\n"  # noqa: W605
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


class GitlabTagEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.before = body['before']
        self.after = body['after']
        self.ref = body['ref']
        self.checkout_sha = body['checkout_sha']
        self.user_id = body['user_id']
        self.user_name = body['user_name']
        self.user_email = body['user_email']
        self.user_avatar = body['user_avatar']
        self.project_id = body['project_id']
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.commits = [GitlabCommit(commit) for commit in body['commits']]
        self.total_commits_count: int = int(body['total_commits_count'])


class GitlabIssueEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.user = GitlabUser(body['user'])
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.object_attributes = GitlabObjectAttributes(body['object_attributes'])  # noqa: E501
        self.assignees = [GitlabAssignee(assignee) for assignee in body['assignees']]  # noqa: E501
        self.changes = [GitlabChange(change) for change in body['changes']]


class GitlabUser:

    def __init__(self, user: dict):

        self.name = user['name']
        self.user_name = user['username']
        self.avatar_url = user['avatar_url']


class GitlabObjectAttributes:

    def __init__(self, obj: dict):

        self.id: int = int(obj['id'])
        self.title = obj['title']
        self.assignee_ids: List[int] = [int(assignee_id) for assignee_id in obj['assignee_ids']]  # noqa: E501
        self.author_id: int = int(obj['author_id'])
        self.project_id: int = int(obj['project_id'])
        self.created_at = obj['created_at']
        self.updated_at = obj['updated_at']
        self.position: int = int(obj['position']) or 0
        self.branch_name = obj['branch_name'] or None
        self.description = obj['description']
        self.milestone_id: int = int(obj['milestone_id'])
        self.state = obj['state']
        self.iid: int = int(obj['iid'])
        self.url = obj['url']
        self.action = obj['action'] or None
        self.target_branch = obj['target_branch'] or None
        self.source_branch = obj['source_branch'] or None
        self.source_project_id: int = int(obj['source_project_id']) or None
        self.target_project_id: int = int(obj['target_project_id']) or None
        self.st_commits = obj['st_commits'] or None
        self.merge_status = obj['merge_status'] or None
        self.content = obj['content'] or None
        self.format = obj['format'] or None
        self.message = obj['message'] or None
        self.slug = obj['slug'] or None
        self.ref = obj['ref'] or None
        self.tag = obj['tag'] or None
        self.sha = obj['sha'] or None
        self.before_sha = obj['before_sha'] or None
        self.status = obj['status'] or None
        self.stages = obj['stages'] or None
        self.duration: int = int(obj['duration']) or 0
        self.note = obj['note'] or None
        self.noteable_type = obj['noteable_type'] or None
        self.attachment = obj['attachment'] or None
        self.line_code = obj['line_code'] or None
        self.commit_id = obj['commit_id'] or None
        self.noteable_id: int = int(obj['noteable_id']) or 0
        self.system = obj['system'] or None
        self.work_in_progress = obj['work_in_progress'] or None
        self.st_diffs = [GitlabStDiff(st_diff) for st_diff in obj['st_diffs']]
        self.source = GitlabSource(obj['source'] or None)
        self.target = GitlabTarget(obj['target'] or None)
        self.last_commit = GitlabLastCommit(obj['last_commit'] or None)
        self.assignee = GitlabAssignee(obj['assignee'] or None)


class GitlabStDiff:

    def __init__(self, st_diff: dict):

        self.diff = st_diff['diff']
        self.new_path = st_diff['new_path']
        self.old_path = st_diff['old_path']
        self.a_mode = st_diff['a_mode']
        self.b_mode = st_diff['b_mode']
        self.new_file = st_diff['new_file']
        self.renamed_file = st_diff['renamed_file']
        self.deleted_file = st_diff['deleted_file']


class GitlabSource:

    def __init__(self, source: dict):

        self.name = source['name']
        self.description = source['description']
        self.web_url = source['web_url']
        self.avatar_url = source['avatar_url']
        self.git_ssh_url = source['git_ssh_url']
        self.git_http_url = source['git_http_url']
        self.namespace = source['namespace']
        self.visibility_level: int = int(source['visibility_level'])
        self.path_with_namespace = source['path_with_namespace']
        self.default_branch = source['default_branch']
        self.homepage = source['homepage']
        self.url = source['url']
        self.ssh_url = source['ssh_url']
        self.http_url = source['http_url']


class GitlabTarget:

    def __init__(self, source: dict):

        self.name = source['name']
        self.description = source['description']
        self.web_url = source['web_url']
        self.avatar_url = source['avatar_url']
        self.git_ssh_url = source['git_ssh_url']
        self.git_http_url = source['git_http_url']
        self.namespace = source['namespace']
        self.visibility_level: int = int(source['visibility_level'])
        self.path_with_namespace = source['path_with_namespace']
        self.default_branch = source['default_branch']
        self.homepage = source['homepage']
        self.url = source['url']
        self.ssh_url = source['ssh_url']
        self.http_url = source['http_url']


class GitlabLastCommit:

    def __init__(self, commit: dict):

        self.id = commit['id']
        self.message = commit['message']
        self.timestamp = commit['timestamp']
        self.url = commit['url']
        self.author = GitlabAuthor(commit['author'])


class GitlabChange:

    def __init__(self, change: dict):

        self.labels = GitlabLabelChanges(change['labels'])


class GitlabLabelChanges:

    def __init__(self, labels: dict):

        self.previous = [GitlabLabel(label) for label in labels['previous']]
        self.current = [GitlabLabel(label) for label in labels['current']]


class GitlabLabel:

    def __init__(self, label: dict):

        self.id: int = int(label['id'])
        self.title = label['title']
        self.color = label['color']
        self.project_id: int = int(label['project_id'])
        self.created_at = label['created_at']
        self.updated_at = label['updated_at']
        self.template = label['template']
        self.description = label['description']
        self.type = label['type']
        self.group_id: int = int(label['group_id'])


class GitlabAssignee:

    def __init__(self, assignee: dict):

        self.name = assignee['name']
        self.user_name = assignee['username']
        self.avatar_url = assignee['avatar_url']


class GitlabProject:

    def __init__(self, project: dict):
        self.id: int = int(project['id'])
        self.name = project['name']
        self.description = project['description']
        self.web_url = project['web_url']
        self.avatar_url = project['avatar_url']
        self.git_ssh_url = project['git_ssh_url']
        self.git_http_url = project['git_http_url']
        self.namespace = project['namespace']
        self.visibility_level: int = int(project['visibility_level'])
        self.path_with_namespace = project['path_with_namespace']
        self.default_branch = project['default_branch']
        self.homepage = project['homepage']
        self.url = project['url']
        self.ssh_url = project['ssh_url']
        self.http_url = project['http_url']


class GitlabCommit:

    def __init__(self, commit: dict):

        self.id = commit['id']
        self.message = commit['message']
        self.timestamp = commit['timestamp']
        self.url = commit['url']
        self.author = GitlabAuthor(commit['author'])
        self.added = commit['added']
        self.modified = commit['modified']
        self.removed = commit['removed']


class GitlabAuthor:

    def __init__(self, author: dict):
        self.name = author['name']
        self.email = author['email']


class GitlabRepository:

    def __init__(self, repo: dict):
        self.name = repo['name']
        self.url = repo['url']
        self.description = repo['description']
        self.homepage = repo['homepage']
