import attrs.validators
from attrs import define, field

__all__ = ['Commit', 'Repo']

@define
class Commit:
    hash: str = field(validator=attrs.validators.instance_of(str))
    date: str = field(validator=attrs.validators.instance_of(str))
    author: str = field(validator=attrs.validators.instance_of(str))
    email: str = field(validator=attrs.validators.instance_of(str))
    diff_link: str = field(validator=attrs.validators.instance_of(str))
    repo_url: str = field(validator=attrs.validators.instance_of(str))

@define
class Branch:
    name: str = field(validator=attrs.validators.instance_of(str))
    repo: str = field(validator=attrs.validators.instance_of(str))
    url: str = field(validator=attrs.validators.instance_of(str))
    update_ts: str = field(validator=attrs.validators.instance_of(str))

@define
class Repo:
    name: str = field(validator=attrs.validators.instance_of(str))
    workspace: str = field(validator=attrs.validators.instance_of(str))
    url: str = field(validator=attrs.validators.instance_of(str))
    update_ts: str = field(validator=attrs.validators.instance_of(str))

@define
class RepoBranchLink:
    repo_name: str = field(validator=attrs.validators.instance_of(str))
    branch_name: str = field(validator=attrs.validators.instance_of(str))

@define
class BranchCommitLink:
    branch_name: str = field(validator=attrs.validators.instance_of(str))
    commit_hash: str = field(validator=attrs.validators.instance_of(str))