
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
        self.user_avatar = body['user_avatar']
        self.project_id = body['project_id']
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.commits = [GitlabCommit(commit) for commit in body['commits']]
        self.total_commits_count: int = int(body['total_commits_count'])

    def handle(self) -> str:

        if self.object_kind != 'tag_push':
            return None

        tag = self.ref.replace('refs/tags', '')

        msg = "\[{0!s}/{1!s}\] {2!s} created tag [{4!s}]({3!s}/tags/{4!s})"  # noqa: W605 E501
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user_name,
                          self.project.web_url,
                          tag
                          )


class GitlabIssueEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.user = GitlabUser(body['user'])
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.object_attributes = GitlabObjectAttributes(body['object_attributes'])  # noqa: E501
        if 'assignees' in body:
            self.assignees = [GitlabAssignee(assignee) for assignee in body['assignees']]  # noqa: E501
        self.labels = [GitlabLabel(label) for label in body['labels']]
        self.changes = [GitlabChange(name, change) for name, change in body['changes'].items()]  # noqa: E501

    def handle(self) -> str:

        action = self.object_attributes.action
        if action == 'update' or len(action) == 0:
            return None
        elif not action[-1] == 'e':
            action += 'e'

        confidential = ''
        if self.object_attributes.confidential:
            confidential = 'confidential '

        msg = '\[{0!s}/{1!s}\] {2!s} {3!s}d {4!s}issue [{6!s} (#{7:d})]({5!s})'  # noqa: W605 E501
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user.name,
                          action,
                          confidential,
                          self.object_attributes.url,
                          self.object_attributes.title,
                          self.object_attributes.iid
                          )


class GitlabCommentEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.user = GitlabUser(body['user'])
        self.project_id: int = int(body['project_id'])
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.object_attributes = GitlabObjectAttributes(body['object_attributes'])  # noqa: E501
        if 'merge_request' in body:
            self.merge_request = GitlabMergeRequest(body['merge_request'])
        if 'commit' in body:
            self.commit = GitlabCommit(body['commit'])
        if 'issue' in body:
            self.issue = GitlabIssue(body['issue'])
        if 'snippet' in body:
            self.snippet = GitlabSnippet(body['snippet'])

    def handle(self) -> str:

        noteable_type = self.object_attributes.noteable_type
        if noteable_type == 'Issue':
            note_type = 'issue'
            note_identifier = '#'
            title = self.issue.iid
        elif noteable_type == 'MergeRequest':
            note_type = 'merge request'
            note_identifier = '!'
            title = self.merge_request.title
            id = self.merge_request.iid
        else:
            return None

        msg = '\[{0!s}/{1!s}\] {2!s} [commented]({4!s}) on {3!s} {5!s} ({7!s}{6:d}):\n\n{8!s}'  # noqa: W605 E501
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


class GitlabMergeRequestEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.user = GitlabUser(body['user'])
        self.project = GitlabProject(body['project'])
        self.repository = GitlabRepository(body['repository'])
        self.object_attributes = GitlabObjectAttributes(body['object_attributes'])  # noqa: E501
        self.labels = [GitlabLabel(label) for label in body['labels']]
        self.changes = [GitlabChange(name, change) for name, change in body['changes'].items()]  # noqa: E501

    def handle(self) -> str:

        action = self.object_attributes.action

        if action == 'update':
            return None
        elif not action[-1] == 'e':
            action += 'e'

        msg = '\[{0!s}/{1!s}\] {2!s} {3!s}d merge request [{5!s} (!{6:d})]({4!s})'  # noqa W605 E501
        return msg.format(self.object_attributes.target.namespace,
                          self.object_attributes.target.name,
                          self.user.name,
                          action,
                          self.object_attributes.url,
                          self.object_attributes.title,
                          self.object_attributes.iid
                          )


class GitlabWikiPageEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.user = GitlabUser(body['user'])
        self.project = GitlabProject(body['project'])
        self.wiki = GitlabWiki(body['wiki'])
        self.object_attributes = GitlabObjectAttributes(body['object_attributes'])  # noqa: E501

    def handle(self) -> str:

        action = self.object_attributes.action

        if not action[-1] == 'e':
            action += 'e'

        msg = '\[{0!s}/{1!s}\] {2!s} {3!s}d page on wiki [{5!s} (#{6:d})]({5!s})'  # noqa W605 E501
        return msg.format(self.project.namespace,
                          self.project.name,
                          self.user.name,
                          action,
                          self.object_attributes.url,
                          self.object_attributes.title,
                          self.object_attributes.iid
                          )


class GitlabPipelineEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.object_attributes = GitlabObjectAttributes(body['object_attributes'])  # noqa: E501
        self.user = GitlabUser(body['user'])
        self.project = GitlabProject(body['project'])
        self.commit = GitlabCommit(body['commit'])
        self.builds = [GitlabBuild(build) for build in body['builds']]

    def handle(self) -> str:

        pluralizer = ''
        if not len(self.builds) == 1:
            pluralizer = 's'

        duration = self.object_attributes.duration

        msg = '\[{0!s}/{1!s}\] {2} pipeline{3!s} complete in {4!s}\n\n'  # noqa: W605 E501
        msg = msg.format(self.project.namespace,
                         self.project.name,
                         len(self.builds),
                         pluralizer,
                         duration
                         )

        for build in self.builds:
            msg += '+ [{2!s}:{3!s} ({1})]({0!s}/-/jobs/{1}) {4!s}\n'
            msg = msg.format(self.project.web_url,
                             build.id,
                             build.name,
                             build.stage,
                             build.status
                             )

        return msg


class GitlabJobEvent:

    def __init__(self, body: dict):

        self.object_kind = body['object_kind']
        self.ref = body['ref']
        self.tag = body['tag']
        self.before_sha = body['before_sha']
        self.sha = body['sha']
        self.build_id: int = int(body['build_id'])
        self.build_name = body['build_name']
        self.build_stage = body['build_stage']
        self.build_status = body['build_status']
        self.build_started_at = body['build_started_at']
        self.build_finished_at = body['build_finished_at']
        self.build_duration = body['build_duration']
        self.build_allow_failure = body['build_allow_failure']
        self.build_failure_reason = body['build_failure_reason']
        self.project_id: int = int(body['project_id'])
        self.project_name = body['project_name']
        self.user = GitlabUser(body['user'])
        self.commit = GitlabCommit(body['commit'])
        self.repository = GitlabRepository(body['repository'])

    def handle(self) -> str:

        namespace = self.project_name.replace(' ', '').split('/')[1]
        name = self.project_name.replace(' ', '').split('/')[2]

        msg = '\[{0!s}/{1!s}\] job [{2!s}:{3!s} ({4})]({5!s}/-/jobs/{4}) {6!s}'  # noqa: W605 E501
        return msg.format(namespace,
                          name,
                          self.build_name,
                          self.build_stage,
                          self.build_id,
                          self.repository.homepage,
                          self.build_status
                          )


class GitlabBuild:

    def __init__(self, build: dict):

        self.id: int = int(build['id'])
        self.stage = build['stage']
        self.name = build['name']
        self.status = build['status']
        self.created_at = build['created_at']
        self.started_at = build['started_at']
        self.finished_at = build['finished_at']
        self.when = build['when']
        self.manual = build['manual']
        self.user = GitlabUser(build['user'])
        self.runner = build['runner']
        self.artifacts_file = GitlabArtifact(build['artifacts_file'])


class GitlabArtifact:

    def __init__(self, artifact: dict):

        self.file_name = artifact['filename']
        self.size = artifact['size']


class GitlabWiki:

    def __init__(self, wiki: dict):

        self.web_url = wiki['web_url']
        self.git_ssh_url = wiki['git_ssh_url']
        self.git_http_url = wiki['git_http_url']
        self.path_with_namespace = wiki['path_with_namespace']
        self.default_branch = wiki['default_branch']


class GitlabMergeRequest:

    def __init__(self, mreq: dict):

        self.id: int = int(mreq['id'])
        self.target_branch = mreq['target_branch']
        self.source_branch = mreq['source_branch']
        self.source_project_id: int = int(mreq['source_project_id'])
        self.assignee_id: int = int(mreq['assignee_id'])
        self.author_id: int = int(mreq['author_id'])
        self.title = mreq['title']
        self.created_at = mreq['created_at']
        self.updated_at = mreq['updated_at']
        self.milestone_id = mreq['milestone_id']
        self.state = mreq['state']
        self.merge_status = mreq['merge_status']
        self.target_project_id: int = int(mreq['target_project_id'])
        self.iid: int = int(mreq['iid'])
        self.description = mreq['description']
        if 'position' in mreq:
            self.position = mreq['position']
        if 'locked_at' in mreq:
            self.locked_at = mreq['locked_at']
        self.source = GitlabSource(mreq['source'])
        self.target = GitlabTarget(mreq['target'])
        self.last_commit = GitlabCommit(mreq['last_commit'])
        self.work_in_progress = mreq['work_in_progress']
        if 'assignee' in mreq:
            self.assignee = GitlabAssignee(mreq['assignee'])


class GitlabIssue:

    def __init__(self, issue: dict):

        self.id: int = int(issue['id'])
        self.title = issue['title']
        self.assignee_id: int = int(issue['assignee_id'])
        self.author_id: int = int(issue['author_id'])
        self.project_id: int = int(issue['project_id'])
        self.created_at = issue['created_at']
        self.updated_at = issue['updated_at']
        self.position: int = issue['position']
        self.branch_name = issue['branch_name']
        self.description = issue['description']
        self.milestone_id: int = int(issue['milestone_id'])
        self.state = issue['state']
        self.iid. int = int(issue['iid'])


class GitlabSnippet:

    def __init__(self, snippet: dict):

        self.id: int = int(snippet['id'])
        self.title = snippet['title']
        self.content = snippet['content']
        self.author_id: int = int(snippet['author_id'])
        self.project_id: int = int(snippet['project_id'])
        self.created_at = snippet['created_at']
        self.updated_at = snippet['updated_at']
        self.file_name = snippet['file_name']
        self.expires_at = snippet['expires_at']
        self.type = snippet['type']
        self.visibility_level: int = int(snippet['visibility_level'])


class GitlabUser:

    def __init__(self, user: dict):

        self.name = user['name']
        if 'username' in user:
            self.user_name = user['username']
        if 'avatar_url' in user:
            self.avatar_url = user['avatar_url']
        if 'id' in user:
            self.id: int = int(user['id'])
        if 'email' in user:
            self.email = user['email']


class GitlabObjectAttributes:

    def __init__(self, obj: dict):

        if 'note' in obj:
            self.id: int = int(obj['id'])
            self.author_id: int = int(obj['author_id'])
            self.created_at = obj['created_at']
            self.updated_at = obj['updated_at']
            self.url = obj['url']
            self.note = obj['note'] or None
            self.noteable_type = obj['noteable_type'] or None
            self.project_id: int = int(obj['project_id'])
            self.attachment = obj['attachment'] or None
            self.line_code = obj['line_code'] or None
            self.commit_id = obj['commit_id'] or None
            self.noteable_id: int = int(obj['noteable_id']) or 0
            self.system = obj['system'] or None
            if obj['st_diff']:
                self.st_diff = GitlabStDiff(obj['st_diff'])
            else:
                self.st_diff = obj['st_diff']
        elif 'slug' in obj:
            self.title = obj['title']
            self.content = obj['content']
            self.format = obj['markdown']
            self.message = obj['message']
            self.slug = obj['slug']
            self.url = obj['url']
            self.action = obj['action']
        elif 'merge_status' in obj:
            # TODO: maybe possible to merge with GitlabMergeRequest
            self.id: int = int(obj['id'])
            self.author_id: int = int(obj['author_id'])
            self.created_at = obj['created_at']
            self.updated_at = obj['updated_at']
            self.url = obj['url']
            self.target_branch = obj['target_branch']
            self.source_branch = obj['source_branch']
            self.source_project_id: int = int(obj['source_project_id'])
            self.assignee_id: int = int(obj['assignee_id'])
            self.title = obj['title']
            self.milestone_id = obj['milestone_id']
            self.state = obj['state']
            self.merge_status = obj['merge_status']
            self.target_project_id: int = int(obj['target_project_id'])
            self.iid: int = obj['iid']
            self.description = obj['description']
            self.source = GitlabSource(obj['source'])
            self.target = GitlabTarget(obj['target'])
            self.last_commit = GitlabCommit(obj['last_commit'])
            self.work_in_progress = obj['work_in_progress']
            self.action = obj['action']
            if 'assignee' in obj:
                self.assignee = GitlabAssignee(obj['assignee'])
        elif 'stages' in obj:
            self.id: int = int(obj['id'])
            self.ref = obj['ref']
            self.tag = obj['tag']
            self.sha = obj['sha']
            self.before_sha = obj['before_sha']
            self.status = obj['status']
            self.stages = obj['stages']
            self.created_at = obj['created_at']
            self.finished_at = obj['finished_at']
            self.duration = obj['duration']
            self.variables = obj['variables']
        elif 'assignee_ids' in obj:
            self.id: int = int(obj['id'])
            self.title = obj['title']
            self.assignee_ids = obj['assignee_ids']
            self.author_id: int = int(obj['author_id'])
            self.project_id: int = int(obj['project_id'])
            self.created_at = obj['created_at']
            self.updated_at = obj['updated_at']
            self.relative_position = obj['relative_position']
            if 'branch_name' in obj:
                self.branch_name = obj['branch_name']
            self.description = obj['description']
            self.milestone_id = obj['milestone_id']
            self.state = obj['state']
            self.iid: int = int(obj['iid'])
            self.url = obj['iid']
            self.action = obj['action']
            self.confidential = obj['confidential']


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


class GitlabChange:

    def __init__(self, name: str, change: dict):

        self.name = name

        if name == 'labels':
            self.previous = [GitlabLabel(label) for label in change['previous']]  # noqa: E501
            self.current = [GitlabLabel(label) for label in change['current']]
        else:
            self.previous = change['previous']
            self.current = change['current']


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
        if 'homepage' in project:
            self.homepage = project['homepage']
        if 'url' in project:
            self.url = project['url']
        if 'ssh_url' in project:
            self.ssh_url = project['ssh_url']
        if 'http_url' in project:
            self.http_url = project['http_url']


class GitlabCommit:

    def __init__(self, commit: dict):

        self.id = commit['id']
        self.message = commit['message']
        if 'timestamp' in commit:
            self.timestamp = commit['timestamp']
        if 'url' in commit:
            self.url = commit['url']
        if 'author' in commit:
            self.author = GitlabAuthor(commit['author'])
        if 'added' in commit:
            self.added = commit['added']
        if 'modified' in commit:
            self.modified = commit['modified']
        if 'removed' in commit:
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
        if 'git_http_url' in repo:
            self.git_http_url = repo['git_http_url']
        if 'git_ssh_url' in repo:
            self.git_ssh_url = repo['git_ssh_url']
        if 'visibility_level' in repo:
            self.visibility_level: int = int(repo['visibility_level'])


EventParse = {'Push Hook': GitlabPushEvent,
              'Tag Push Hook': GitlabTagEvent,
              'Issue Hook': GitlabIssueEvent,
              'Note Hook': GitlabCommentEvent,
              'Merge Request Hook': GitlabMergeRequestEvent,
              'Wiki Page Hook': GitlabWikiPageEvent,
              'Pipeline Hook': GitlabPipelineEvent,
              'Job Hook': GitlabJobEvent
              }
