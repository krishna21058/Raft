from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LogReplicationRequest(_message.Message):
    __slots__ = ("node_id", "last_log_index", "last_log_term")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_LOG_INDEX_FIELD_NUMBER: _ClassVar[int]
    LAST_LOG_TERM_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    last_log_index: int
    last_log_term: int
    def __init__(self, node_id: _Optional[int] = ..., last_log_index: _Optional[int] = ..., last_log_term: _Optional[int] = ...) -> None: ...

class LogReplicationResponse(_message.Message):
    __slots__ = ("log_entries",)
    LOG_ENTRIES_FIELD_NUMBER: _ClassVar[int]
    log_entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    def __init__(self, log_entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ...) -> None: ...

class LogEntry(_message.Message):
    __slots__ = ("index", "term", "key", "operation", "value")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    index: int
    term: int
    key: str
    operation: str
    value: str
    def __init__(self, index: _Optional[int] = ..., term: _Optional[int] = ..., key: _Optional[str] = ..., operation: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class AppendEntriesRequest(_message.Message):
    __slots__ = ("term", "leader_id", "prev_log_index", "prev_log_term", "entries", "leader_commit", "lease_duration")
    TERM_FIELD_NUMBER: _ClassVar[int]
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    PREV_LOG_INDEX_FIELD_NUMBER: _ClassVar[int]
    PREV_LOG_TERM_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    LEADER_COMMIT_FIELD_NUMBER: _ClassVar[int]
    LEASE_DURATION_FIELD_NUMBER: _ClassVar[int]
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    leader_commit: int
    lease_duration: int
    def __init__(self, term: _Optional[int] = ..., leader_id: _Optional[int] = ..., prev_log_index: _Optional[int] = ..., prev_log_term: _Optional[int] = ..., entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ..., leader_commit: _Optional[int] = ..., lease_duration: _Optional[int] = ...) -> None: ...

class AppendEntriesResponse(_message.Message):
    __slots__ = ("currTerm", "success")
    CURRTERM_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    currTerm: int
    success: str
    def __init__(self, currTerm: _Optional[int] = ..., success: _Optional[str] = ...) -> None: ...

class RequestVoteRequest(_message.Message):
    __slots__ = ("term", "candidate_id", "last_log_index", "last_log_term")
    TERM_FIELD_NUMBER: _ClassVar[int]
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_LOG_INDEX_FIELD_NUMBER: _ClassVar[int]
    LAST_LOG_TERM_FIELD_NUMBER: _ClassVar[int]
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int
    def __init__(self, term: _Optional[int] = ..., candidate_id: _Optional[int] = ..., last_log_index: _Optional[int] = ..., last_log_term: _Optional[int] = ...) -> None: ...

class RequestVoteResponse(_message.Message):
    __slots__ = ("term", "vote_granted", "lease_duration")
    TERM_FIELD_NUMBER: _ClassVar[int]
    VOTE_GRANTED_FIELD_NUMBER: _ClassVar[int]
    LEASE_DURATION_FIELD_NUMBER: _ClassVar[int]
    term: int
    vote_granted: bool
    lease_duration: int
    def __init__(self, term: _Optional[int] = ..., vote_granted: bool = ..., lease_duration: _Optional[int] = ...) -> None: ...

class ServeClientArgs(_message.Message):
    __slots__ = ("Request",)
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    Request: str
    def __init__(self, Request: _Optional[str] = ...) -> None: ...

class ServeClientReply(_message.Message):
    __slots__ = ("Data", "LeaderID", "Success")
    DATA_FIELD_NUMBER: _ClassVar[int]
    LEADERID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    Data: str
    LeaderID: int
    Success: str
    def __init__(self, Data: _Optional[str] = ..., LeaderID: _Optional[int] = ..., Success: _Optional[str] = ...) -> None: ...

class RecoverRequest(_message.Message):
    __slots__ = ("NodeId",)
    NODEID_FIELD_NUMBER: _ClassVar[int]
    NodeId: int
    def __init__(self, NodeId: _Optional[int] = ...) -> None: ...

class RecoverReply(_message.Message):
    __slots__ = ("commitLength", "term", "NodeId")
    COMMITLENGTH_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    commitLength: int
    term: int
    NodeId: int
    def __init__(self, commitLength: _Optional[int] = ..., term: _Optional[int] = ..., NodeId: _Optional[int] = ...) -> None: ...
