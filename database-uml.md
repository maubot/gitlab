
## ERM

@startuml
class User {
user_name
}

class GitlabServer {
gitlab_server
api_token
}

class Alias {
user_name
gitlab_server
alias
}

User "1" - "m" GitlabServer
(User, GitlabServer) . Alias

@enduml

## Database layout

@startuml
class Tokens {
{static} user_name : str
{static} gitlab_server : text
api_token : text
}

class Alias {
{static} user_name : str
{static} gitlab_server : text
{static} alias : text
}
@enduml
