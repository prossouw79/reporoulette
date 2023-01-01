import attrs.validators
from attrs import define, field
from sqlite_integrated import DatabaseEntry

__all__ = ['Commit', 'Branch', 'Repo', 'RepoBranchLink', 'BranchCommitLink']


@define
class Commit:
    hash: str = field(validator=attrs.validators.instance_of(str))
    message: str = field(validator=attrs.validators.instance_of(str))
    summary: str = field(validator=attrs.validators.instance_of(str))
    date: str = field(validator=attrs.validators.instance_of(str))
    author: str = field(validator=attrs.validators.instance_of(str))
    email: str = field(validator=attrs.validators.instance_of(str))
    diff_link: str = field(validator=attrs.validators.instance_of(str))
    repo_url: str = field(validator=attrs.validators.instance_of(str))

    @classmethod
    def from_db_entry(cls, db_entry: DatabaseEntry):
        return cls(
            hash=db_entry.get('hash'),
            message=db_entry.get('message'),
            summary=db_entry.get('summary'),
            date=db_entry.get('date'),
            author=db_entry.get('author'),
            email=db_entry.get('email'),
            diff_link=db_entry.get('diff_link'),
            repo_url=db_entry.get('repo_url')
        )


@define
class Branch:
    name: str = field(validator=attrs.validators.instance_of(str))
    repo: str = field(validator=attrs.validators.instance_of(str))
    url: str = field(validator=attrs.validators.instance_of(str))
    update_ts: str = field(validator=attrs.validators.instance_of(str))

    @classmethod
    def from_db_entry(cls, db_entry: DatabaseEntry):
        return cls(
            name=db_entry.get('name'),
            repo=db_entry.get('repo'),
            url=db_entry.get('url'),
            update_ts=db_entry.get('update_ts')
        )


@define
class Repo:
    name: str = field(validator=attrs.validators.instance_of(str))
    workspace: str = field(validator=attrs.validators.instance_of(str))
    main_branch: str = field(validator=attrs.validators.instance_of(str))
    main_branch_url: str = field(validator=attrs.validators.instance_of(str))
    repo_url: str = field(validator=attrs.validators.instance_of(str))
    update_ts: str = field(validator=attrs.validators.instance_of(str))

    @classmethod
    def from_db_entry(cls, db_entry: DatabaseEntry):
        return cls(
            name=db_entry.get('name'),
            workspace=db_entry.get('workspace'),
            main_branch=db_entry.get('main_branch'),
            main_branch_url=db_entry.get('main_branch_url'),
            repo_url=db_entry.get('repo_url'),
            update_ts=db_entry.get('update_ts')
        )


@define
class RepoBranchLink:
    repo_name: str = field(validator=attrs.validators.instance_of(str))
    branch_name: str = field(validator=attrs.validators.instance_of(str))

    @classmethod
    def from_db_entry(cls, db_entry: DatabaseEntry):
        return cls(
            repo_name=db_entry.get('repo_name'),
            branch_name=db_entry.get('branch_name')
        )


@define
class BranchCommitLink:
    branch_name: str = field(validator=attrs.validators.instance_of(str))
    commit_hash: str = field(validator=attrs.validators.instance_of(str))

    @classmethod
    def from_db_entry(cls, db_entry: DatabaseEntry):
        return cls(
            branch_name=db_entry.get('branch_name'),
            commit_hash=db_entry.get('commit_hash')
        )
