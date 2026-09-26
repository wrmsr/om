# flake8: noqa: E501
# ruff: noqa: N801 S105
# fmt: off
# @om-generated
import typing as _ta  # noqa

from omcore import dataclasses as _dc  # noqa

from ... import base as _base  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


AbortDate = _ta.NewType('AbortDate', _base.Timestamp)

AbortRuleId = _ta.NewType('AbortRuleId', str)

AcceptRanges = _ta.NewType('AcceptRanges', str)

AccountId = _ta.NewType('AccountId', str)


class AnnotationDirective(_base.Enum):
    COPY = 'COPY'
    EXCLUDE = 'EXCLUDE'


class ArchiveStatus(_base.Enum):
    ARCHIVE_ACCESS = 'ARCHIVE_ACCESS'
    DEEP_ARCHIVE_ACCESS = 'DEEP_ARCHIVE_ACCESS'


Body = _ta.NewType('Body', bytes)


@_dc.dataclass(frozen=True, kw_only=True)
class BucketAlreadyExists(
    _base.Shape,
    shape_name='BucketAlreadyExists',
):
    pass


@_dc.dataclass(frozen=True, kw_only=True)
class BucketAlreadyOwnedByYou(
    _base.Shape,
    shape_name='BucketAlreadyOwnedByYou',
):
    pass


class BucketCannedACL(_base.Enum):
    PRIVATE = 'private'
    PUBLIC_READ = 'public-read'
    PUBLIC_READ_WRITE = 'public-read-write'
    AUTHENTICATED_READ = 'authenticated-read'


BucketKeyEnabled = _ta.NewType('BucketKeyEnabled', bool)


class BucketLocationConstraint(_base.Enum):
    AF_SOUTH_1 = 'af-south-1'
    AP_EAST_1 = 'ap-east-1'
    AP_EAST_2 = 'ap-east-2'
    AP_NORTHEAST_1 = 'ap-northeast-1'
    AP_NORTHEAST_2 = 'ap-northeast-2'
    AP_NORTHEAST_3 = 'ap-northeast-3'
    AP_SOUTH_1 = 'ap-south-1'
    AP_SOUTH_2 = 'ap-south-2'
    AP_SOUTHEAST_1 = 'ap-southeast-1'
    AP_SOUTHEAST_2 = 'ap-southeast-2'
    AP_SOUTHEAST_3 = 'ap-southeast-3'
    AP_SOUTHEAST_4 = 'ap-southeast-4'
    AP_SOUTHEAST_5 = 'ap-southeast-5'
    AP_SOUTHEAST_6 = 'ap-southeast-6'
    AP_SOUTHEAST_7 = 'ap-southeast-7'
    CA_CENTRAL_1 = 'ca-central-1'
    CA_WEST_1 = 'ca-west-1'
    CN_NORTH_1 = 'cn-north-1'
    CN_NORTHWEST_1 = 'cn-northwest-1'
    E_U = 'EU'
    EU_CENTRAL_1 = 'eu-central-1'
    EU_CENTRAL_2 = 'eu-central-2'
    EU_NORTH_1 = 'eu-north-1'
    EU_SOUTH_1 = 'eu-south-1'
    EU_SOUTH_2 = 'eu-south-2'
    EU_WEST_1 = 'eu-west-1'
    EU_WEST_2 = 'eu-west-2'
    EU_WEST_3 = 'eu-west-3'
    IL_CENTRAL_1 = 'il-central-1'
    ME_CENTRAL_1 = 'me-central-1'
    ME_SOUTH_1 = 'me-south-1'
    MX_CENTRAL_1 = 'mx-central-1'
    SA_EAST_1 = 'sa-east-1'
    US_EAST_2 = 'us-east-2'
    US_GOV_EAST_1 = 'us-gov-east-1'
    US_GOV_WEST_1 = 'us-gov-west-1'
    US_WEST_1 = 'us-west-1'
    US_WEST_2 = 'us-west-2'


BucketName = _ta.NewType('BucketName', str)


class BucketNamespace(_base.Enum):
    ACCOUNT_REGIONAL = 'account-regional'
    GLOBAL = 'global'


BucketRegion = _ta.NewType('BucketRegion', str)


class BucketType(_base.Enum):
    DIRECTORY = 'Directory'


BypassGovernanceRetention = _ta.NewType('BypassGovernanceRetention', bool)

CacheControl = _ta.NewType('CacheControl', str)


class ChecksumAlgorithm(_base.Enum):
    CRC32 = 'CRC32'
    CRC32C = 'CRC32C'
    SHA1 = 'SHA1'
    SHA256 = 'SHA256'
    CRC64NVME = 'CRC64NVME'
    SHA512 = 'SHA512'
    MD5 = 'MD5'
    XXHASH64 = 'XXHASH64'
    XXHASH3 = 'XXHASH3'
    XXHASH128 = 'XXHASH128'


ChecksumCRC32 = _ta.NewType('ChecksumCRC32', str)

ChecksumCRC32C = _ta.NewType('ChecksumCRC32C', str)

ChecksumCRC64NVME = _ta.NewType('ChecksumCRC64NVME', str)

ChecksumMD5 = _ta.NewType('ChecksumMD5', str)


class ChecksumMode(_base.Enum):
    ENABLED = 'ENABLED'


ChecksumSHA1 = _ta.NewType('ChecksumSHA1', str)

ChecksumSHA256 = _ta.NewType('ChecksumSHA256', str)

ChecksumSHA512 = _ta.NewType('ChecksumSHA512', str)


class ChecksumType(_base.Enum):
    COMPOSITE = 'COMPOSITE'
    FULL_OBJECT = 'FULL_OBJECT'


ChecksumXXHASH128 = _ta.NewType('ChecksumXXHASH128', str)

ChecksumXXHASH3 = _ta.NewType('ChecksumXXHASH3', str)

ChecksumXXHASH64 = _ta.NewType('ChecksumXXHASH64', str)

Code = _ta.NewType('Code', str)

ContentDisposition = _ta.NewType('ContentDisposition', str)

ContentEncoding = _ta.NewType('ContentEncoding', str)

ContentLanguage = _ta.NewType('ContentLanguage', str)

ContentLength = _ta.NewType('ContentLength', int)

ContentMD5 = _ta.NewType('ContentMD5', str)

ContentRange = _ta.NewType('ContentRange', str)

ContentType = _ta.NewType('ContentType', str)

CopySource = _ta.NewType('CopySource', str)

CopySourceIfMatch = _ta.NewType('CopySourceIfMatch', str)

CopySourceIfModifiedSince = _ta.NewType('CopySourceIfModifiedSince', _base.Timestamp)

CopySourceIfNoneMatch = _ta.NewType('CopySourceIfNoneMatch', str)

CopySourceIfUnmodifiedSince = _ta.NewType('CopySourceIfUnmodifiedSince', _base.Timestamp)

CopySourceSSECustomerAlgorithm = _ta.NewType('CopySourceSSECustomerAlgorithm', str)

CopySourceSSECustomerKey = _ta.NewType('CopySourceSSECustomerKey', str)

CopySourceSSECustomerKeyMD5 = _ta.NewType('CopySourceSSECustomerKeyMD5', str)

CopySourceVersionId = _ta.NewType('CopySourceVersionId', str)

CreationDate = _ta.NewType('CreationDate', _base.Timestamp)


class DataRedundancy(_base.Enum):
    SINGLE_AVAILABILITY_ZONE = 'SingleAvailabilityZone'
    SINGLE_LOCAL_ZONE = 'SingleLocalZone'


DeleteMarker = _ta.NewType('DeleteMarker', bool)

DeleteMarkerVersionId = _ta.NewType('DeleteMarkerVersionId', str)

Delimiter = _ta.NewType('Delimiter', str)

DisplayName = _ta.NewType('DisplayName', str)

ETag = _ta.NewType('ETag', str)


class EncodingType(_base.Enum):
    URL = 'url'


@_dc.dataclass(frozen=True, kw_only=True)
class EncryptionTypeMismatch(
    _base.Shape,
    shape_name='EncryptionTypeMismatch',
):
    pass


Expiration = _ta.NewType('Expiration', str)

Expires = _ta.NewType('Expires', _base.Timestamp)

FetchOwner = _ta.NewType('FetchOwner', bool)

GrantFullControl = _ta.NewType('GrantFullControl', str)

GrantRead = _ta.NewType('GrantRead', str)

GrantReadACP = _ta.NewType('GrantReadACP', str)

GrantWrite = _ta.NewType('GrantWrite', str)

GrantWriteACP = _ta.NewType('GrantWriteACP', str)

ID = _ta.NewType('ID', str)

IfMatch = _ta.NewType('IfMatch', str)

IfMatchInitiatedTime = _ta.NewType('IfMatchInitiatedTime', _base.Timestamp)

IfMatchLastModifiedTime = _ta.NewType('IfMatchLastModifiedTime', _base.Timestamp)

IfMatchSize = _ta.NewType('IfMatchSize', int)

IfModifiedSince = _ta.NewType('IfModifiedSince', _base.Timestamp)

IfNoneMatch = _ta.NewType('IfNoneMatch', str)

IfUnmodifiedSince = _ta.NewType('IfUnmodifiedSince', _base.Timestamp)

Initiated = _ta.NewType('Initiated', _base.Timestamp)


class IntelligentTieringAccessTier(_base.Enum):
    ARCHIVE_ACCESS = 'ARCHIVE_ACCESS'
    DEEP_ARCHIVE_ACCESS = 'DEEP_ARCHIVE_ACCESS'


@_dc.dataclass(frozen=True, kw_only=True)
class InvalidRequest(
    _base.Shape,
    shape_name='InvalidRequest',
):
    pass


@_dc.dataclass(frozen=True, kw_only=True)
class InvalidWriteOffset(
    _base.Shape,
    shape_name='InvalidWriteOffset',
):
    pass


IsRestoreInProgress = _ta.NewType('IsRestoreInProgress', bool)

IsTruncated = _ta.NewType('IsTruncated', bool)

KeyCount = _ta.NewType('KeyCount', int)

KeyMarker = _ta.NewType('KeyMarker', str)

LastModified = _ta.NewType('LastModified', _base.Timestamp)

LastModifiedTime = _ta.NewType('LastModifiedTime', _base.Timestamp)

Location = _ta.NewType('Location', str)

LocationNameAsString = _ta.NewType('LocationNameAsString', str)


class LocationType(_base.Enum):
    AVAILABILITY_ZONE = 'AvailabilityZone'
    LOCAL_ZONE = 'LocalZone'


MFA = _ta.NewType('MFA', str)

MaxBuckets = _ta.NewType('MaxBuckets', int)

MaxKeys = _ta.NewType('MaxKeys', int)

MaxUploads = _ta.NewType('MaxUploads', int)

Message = _ta.NewType('Message', str)


class MetadataDirective(_base.Enum):
    COPY = 'COPY'
    REPLACE = 'REPLACE'


MetadataKey = _ta.NewType('MetadataKey', str)

MetadataValue = _ta.NewType('MetadataValue', str)

MissingMeta = _ta.NewType('MissingMeta', int)

MpuObjectSize = _ta.NewType('MpuObjectSize', int)

MultipartUploadId = _ta.NewType('MultipartUploadId', str)

NextKeyMarker = _ta.NewType('NextKeyMarker', str)

NextToken = _ta.NewType('NextToken', str)

NextUploadIdMarker = _ta.NewType('NextUploadIdMarker', str)


@_dc.dataclass(frozen=True, kw_only=True)
class NoSuchBucket(
    _base.Shape,
    shape_name='NoSuchBucket',
):
    pass


@_dc.dataclass(frozen=True, kw_only=True)
class NoSuchKey(
    _base.Shape,
    shape_name='NoSuchKey',
):
    pass


@_dc.dataclass(frozen=True, kw_only=True)
class NoSuchUpload(
    _base.Shape,
    shape_name='NoSuchUpload',
):
    pass


class ObjectCannedACL(_base.Enum):
    PRIVATE = 'private'
    PUBLIC_READ = 'public-read'
    PUBLIC_READ_WRITE = 'public-read-write'
    AUTHENTICATED_READ = 'authenticated-read'
    AWS_EXEC_READ = 'aws-exec-read'
    BUCKET_OWNER_READ = 'bucket-owner-read'
    BUCKET_OWNER_FULL_CONTROL = 'bucket-owner-full-control'


ObjectKey = _ta.NewType('ObjectKey', str)

ObjectLockEnabledForBucket = _ta.NewType('ObjectLockEnabledForBucket', bool)


class ObjectLockEventHold(_base.Enum):
    ON = 'ON'
    OFF = 'OFF'


ObjectLockEventHoldDurationDays = _ta.NewType('ObjectLockEventHoldDurationDays', int)

ObjectLockEventHoldDurationYears = _ta.NewType('ObjectLockEventHoldDurationYears', int)


class ObjectLockLegalHoldStatus(_base.Enum):
    ON = 'ON'
    OFF = 'OFF'


class ObjectLockMode(_base.Enum):
    GOVERNANCE = 'GOVERNANCE'
    COMPLIANCE = 'COMPLIANCE'


ObjectLockRetainUntilDate = _ta.NewType('ObjectLockRetainUntilDate', _base.Timestamp)


@_dc.dataclass(frozen=True, kw_only=True)
class ObjectNotInActiveTierError(
    _base.Shape,
    shape_name='ObjectNotInActiveTierError',
):
    pass


class ObjectOwnership(_base.Enum):
    BUCKET_OWNER_PREFERRED = 'BucketOwnerPreferred'
    OBJECT_WRITER = 'ObjectWriter'
    BUCKET_OWNER_ENFORCED = 'BucketOwnerEnforced'


class ObjectStorageClass(_base.Enum):
    STANDARD = 'STANDARD'
    REDUCED_REDUNDANCY = 'REDUCED_REDUNDANCY'
    GLACIER = 'GLACIER'
    STANDARD_IA = 'STANDARD_IA'
    ONEZONE_IA = 'ONEZONE_IA'
    INTELLIGENT_TIERING = 'INTELLIGENT_TIERING'
    DEEP_ARCHIVE = 'DEEP_ARCHIVE'
    OUTPOSTS = 'OUTPOSTS'
    GLACIER_IR = 'GLACIER_IR'
    SNOW = 'SNOW'
    EXPRESS_ONEZONE = 'EXPRESS_ONEZONE'
    FSX_OPENZFS = 'FSX_OPENZFS'
    FSX_ONTAP = 'FSX_ONTAP'
    AWS_BACKUP_WARM = 'AWS_BACKUP_WARM'
    AWS_BACKUP_LOW_COST_WARM = 'AWS_BACKUP_LOW_COST_WARM'


ObjectVersionId = _ta.NewType('ObjectVersionId', str)


class OptionalObjectAttributes(_base.Enum):
    RESTORE_STATUS = 'RestoreStatus'


PartNumber = _ta.NewType('PartNumber', int)

PartsCount = _ta.NewType('PartsCount', int)

Prefix = _ta.NewType('Prefix', str)

Quiet = _ta.NewType('Quiet', bool)

Range = _ta.NewType('Range', str)


class ReplicationStatus(_base.Enum):
    COMPLETE = 'COMPLETE'
    PENDING = 'PENDING'
    FAILED = 'FAILED'
    REPLICA = 'REPLICA'
    COMPLETED = 'COMPLETED'


class RequestCharged(_base.Enum):
    REQUESTER = 'requester'


class RequestPayer(_base.Enum):
    REQUESTER = 'requester'


ResponseCacheControl = _ta.NewType('ResponseCacheControl', str)

ResponseContentDisposition = _ta.NewType('ResponseContentDisposition', str)

ResponseContentEncoding = _ta.NewType('ResponseContentEncoding', str)

ResponseContentLanguage = _ta.NewType('ResponseContentLanguage', str)

ResponseContentType = _ta.NewType('ResponseContentType', str)

ResponseExpires = _ta.NewType('ResponseExpires', _base.Timestamp)

Restore = _ta.NewType('Restore', str)

RestoreExpiryDate = _ta.NewType('RestoreExpiryDate', _base.Timestamp)

S3RegionalOrS3ExpressBucketArnString = _ta.NewType('S3RegionalOrS3ExpressBucketArnString', str)

SSECustomerAlgorithm = _ta.NewType('SSECustomerAlgorithm', str)

SSECustomerKey = _ta.NewType('SSECustomerKey', str)

SSECustomerKeyMD5 = _ta.NewType('SSECustomerKeyMD5', str)

SSEKMSEncryptionContext = _ta.NewType('SSEKMSEncryptionContext', str)

SSEKMSKeyId = _ta.NewType('SSEKMSKeyId', str)


class ServerSideEncryption(_base.Enum):
    AES256 = 'AES256'
    AWS_FSX = 'aws:fsx'
    AWS_BACKUP = 'aws:backup'
    AWS_KMS = 'aws:kms'
    AWS_KMS_DSSE = 'aws:kms:dsse'


Size = _ta.NewType('Size', int)

StartAfter = _ta.NewType('StartAfter', str)


class StorageClass(_base.Enum):
    STANDARD = 'STANDARD'
    REDUCED_REDUNDANCY = 'REDUCED_REDUNDANCY'
    STANDARD_IA = 'STANDARD_IA'
    ONEZONE_IA = 'ONEZONE_IA'
    INTELLIGENT_TIERING = 'INTELLIGENT_TIERING'
    GLACIER = 'GLACIER'
    DEEP_ARCHIVE = 'DEEP_ARCHIVE'
    OUTPOSTS = 'OUTPOSTS'
    GLACIER_IR = 'GLACIER_IR'
    SNOW = 'SNOW'
    EXPRESS_ONEZONE = 'EXPRESS_ONEZONE'
    FSX_OPENZFS = 'FSX_OPENZFS'
    FSX_ONTAP = 'FSX_ONTAP'
    AWS_BACKUP_WARM = 'AWS_BACKUP_WARM'
    AWS_BACKUP_LOW_COST_WARM = 'AWS_BACKUP_LOW_COST_WARM'


TagCount = _ta.NewType('TagCount', int)


class TaggingDirective(_base.Enum):
    COPY = 'COPY'
    REPLACE = 'REPLACE'


TaggingHeader = _ta.NewType('TaggingHeader', str)

Token = _ta.NewType('Token', str)


@_dc.dataclass(frozen=True, kw_only=True)
class TooManyParts(
    _base.Shape,
    shape_name='TooManyParts',
):
    pass


UploadIdMarker = _ta.NewType('UploadIdMarker', str)

WebsiteRedirectLocation = _ta.NewType('WebsiteRedirectLocation', str)

WriteOffsetBytes = _ta.NewType('WriteOffsetBytes', int)


@_dc.dataclass(frozen=True, kw_only=True)
class AbortMultipartUploadOutput(
    _base.Shape,
    shape_name='AbortMultipartUploadOutput',
):
    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class AbortMultipartUploadRequest(
    _base.Shape,
    shape_name='AbortMultipartUploadRequest',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    upload_id: MultipartUploadId = _dc.field(metadata=_base.field_metadata(
        member_name='UploadId',
        serialization_name='uploadId',
        location='querystring',
        shape_name='MultipartUploadId',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    if_match_initiated_time: IfMatchInitiatedTime | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatchInitiatedTime',
        serialization_name='x-amz-if-match-initiated-time',
        location='header',
        timestamp_format='rfc822',
        shape_name='IfMatchInitiatedTime',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class Bucket(
    _base.Shape,
    shape_name='Bucket',
):
    name: BucketName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Name',
        shape_name='BucketName',
    ))

    creation_date: CreationDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CreationDate',
        shape_name='CreationDate',
    ))

    bucket_region: BucketRegion | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketRegion',
        shape_name='BucketRegion',
    ))

    bucket_arn: S3RegionalOrS3ExpressBucketArnString | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketArn',
        shape_name='S3RegionalOrS3ExpressBucketArnString',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class BucketInfo(
    _base.Shape,
    shape_name='BucketInfo',
):
    data_redundancy: DataRedundancy | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DataRedundancy',
        shape_name='DataRedundancy',
    ))

    type: BucketType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Type',
        shape_name='BucketType',
    ))


ChecksumAlgorithmList: _ta.TypeAlias = _ta.Sequence[ChecksumAlgorithm]


@_dc.dataclass(frozen=True, kw_only=True)
class CommonPrefix(
    _base.Shape,
    shape_name='CommonPrefix',
):
    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        shape_name='Prefix',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CompleteMultipartUploadOutput(
    _base.Shape,
    shape_name='CompleteMultipartUploadOutput',
):
    location: Location | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Location',
        shape_name='Location',
    ))

    bucket: BucketName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Bucket',
        shape_name='BucketName',
    ))

    key: ObjectKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    expiration: Expiration | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expiration',
        serialization_name='x-amz-expiration',
        location='header',
        shape_name='Expiration',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        shape_name='ETag',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        shape_name='ChecksumXXHASH128',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        shape_name='ChecksumType',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='x-amz-version-id',
        location='header',
        shape_name='ObjectVersionId',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CompletedPart(
    _base.Shape,
    shape_name='CompletedPart',
):
    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        shape_name='ETag',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        shape_name='ChecksumXXHASH128',
    ))

    part_number: PartNumber | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='PartNumber',
        shape_name='PartNumber',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CopyObjectResult(
    _base.Shape,
    shape_name='CopyObjectResult',
):
    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        shape_name='ETag',
    ))

    last_modified: LastModified | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='LastModified',
        shape_name='LastModified',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        shape_name='ChecksumType',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        shape_name='ChecksumXXHASH128',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CreateBucketOutput(
    _base.Shape,
    shape_name='CreateBucketOutput',
):
    location: Location | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Location',
        serialization_name='Location',
        location='header',
        shape_name='Location',
    ))

    bucket_arn: S3RegionalOrS3ExpressBucketArnString | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketArn',
        serialization_name='x-amz-bucket-arn',
        location='header',
        shape_name='S3RegionalOrS3ExpressBucketArnString',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CreateMultipartUploadOutput(
    _base.Shape,
    shape_name='CreateMultipartUploadOutput',
):
    abort_date: AbortDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='AbortDate',
        serialization_name='x-amz-abort-date',
        location='header',
        shape_name='AbortDate',
    ))

    abort_rule_id: AbortRuleId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='AbortRuleId',
        serialization_name='x-amz-abort-rule-id',
        location='header',
        shape_name='AbortRuleId',
    ))

    bucket: BucketName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        shape_name='BucketName',
    ))

    key: ObjectKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    upload_id: MultipartUploadId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='UploadId',
        shape_name='MultipartUploadId',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    sse_kms_encryption_context: SSEKMSEncryptionContext | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSEncryptionContext',
        serialization_name='x-amz-server-side-encryption-context',
        location='header',
        shape_name='SSEKMSEncryptionContext',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        serialization_name='x-amz-checksum-algorithm',
        location='header',
        shape_name='ChecksumAlgorithm',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        serialization_name='x-amz-checksum-type',
        location='header',
        shape_name='ChecksumType',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class DeleteBucketRequest(
    _base.Shape,
    shape_name='DeleteBucketRequest',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class DeleteObjectOutput(
    _base.Shape,
    shape_name='DeleteObjectOutput',
):
    delete_marker: DeleteMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DeleteMarker',
        serialization_name='x-amz-delete-marker',
        location='header',
        shape_name='DeleteMarker',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='x-amz-version-id',
        location='header',
        shape_name='ObjectVersionId',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class DeleteObjectRequest(
    _base.Shape,
    shape_name='DeleteObjectRequest',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    mfa: MFA | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MFA',
        serialization_name='x-amz-mfa',
        location='header',
        shape_name='MFA',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='versionId',
        location='querystring',
        shape_name='ObjectVersionId',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    bypass_governance_retention: BypassGovernanceRetention | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BypassGovernanceRetention',
        serialization_name='x-amz-bypass-governance-retention',
        location='header',
        shape_name='BypassGovernanceRetention',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    if_match: IfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatch',
        serialization_name='If-Match',
        location='header',
        shape_name='IfMatch',
    ))

    if_match_last_modified_time: IfMatchLastModifiedTime | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatchLastModifiedTime',
        serialization_name='x-amz-if-match-last-modified-time',
        location='header',
        timestamp_format='rfc822',
        shape_name='IfMatchLastModifiedTime',
    ))

    if_match_size: IfMatchSize | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatchSize',
        serialization_name='x-amz-if-match-size',
        location='header',
        shape_name='IfMatchSize',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class DeletedObject(
    _base.Shape,
    shape_name='DeletedObject',
):
    key: ObjectKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        shape_name='ObjectVersionId',
    ))

    delete_marker: DeleteMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DeleteMarker',
        shape_name='DeleteMarker',
    ))

    delete_marker_version_id: DeleteMarkerVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DeleteMarkerVersionId',
        shape_name='DeleteMarkerVersionId',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class Error(
    _base.Shape,
    shape_name='Error',
):
    key: ObjectKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        shape_name='ObjectVersionId',
    ))

    code: Code | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Code',
        shape_name='Code',
    ))

    message: Message | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Message',
        shape_name='Message',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class GetObjectRequest(
    _base.Shape,
    shape_name='GetObjectRequest',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    if_match: IfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatch',
        serialization_name='If-Match',
        location='header',
        shape_name='IfMatch',
    ))

    if_modified_since: IfModifiedSince | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfModifiedSince',
        serialization_name='If-Modified-Since',
        location='header',
        shape_name='IfModifiedSince',
    ))

    if_none_match: IfNoneMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfNoneMatch',
        serialization_name='If-None-Match',
        location='header',
        shape_name='IfNoneMatch',
    ))

    if_unmodified_since: IfUnmodifiedSince | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfUnmodifiedSince',
        serialization_name='If-Unmodified-Since',
        location='header',
        shape_name='IfUnmodifiedSince',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    range: Range | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Range',
        serialization_name='Range',
        location='header',
        shape_name='Range',
    ))

    response_cache_control: ResponseCacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseCacheControl',
        serialization_name='response-cache-control',
        location='querystring',
        shape_name='ResponseCacheControl',
    ))

    response_content_disposition: ResponseContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentDisposition',
        serialization_name='response-content-disposition',
        location='querystring',
        shape_name='ResponseContentDisposition',
    ))

    response_content_encoding: ResponseContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentEncoding',
        serialization_name='response-content-encoding',
        location='querystring',
        shape_name='ResponseContentEncoding',
    ))

    response_content_language: ResponseContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentLanguage',
        serialization_name='response-content-language',
        location='querystring',
        shape_name='ResponseContentLanguage',
    ))

    response_content_type: ResponseContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentType',
        serialization_name='response-content-type',
        location='querystring',
        shape_name='ResponseContentType',
    ))

    response_expires: ResponseExpires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseExpires',
        serialization_name='response-expires',
        location='querystring',
        timestamp_format='rfc822',
        shape_name='ResponseExpires',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='versionId',
        location='querystring',
        shape_name='ObjectVersionId',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    part_number: PartNumber | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='PartNumber',
        serialization_name='partNumber',
        location='querystring',
        shape_name='PartNumber',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    checksum_mode: ChecksumMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMode',
        serialization_name='x-amz-checksum-mode',
        location='header',
        shape_name='ChecksumMode',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class HeadObjectRequest(
    _base.Shape,
    shape_name='HeadObjectRequest',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    if_match: IfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatch',
        serialization_name='If-Match',
        location='header',
        shape_name='IfMatch',
    ))

    if_modified_since: IfModifiedSince | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfModifiedSince',
        serialization_name='If-Modified-Since',
        location='header',
        shape_name='IfModifiedSince',
    ))

    if_none_match: IfNoneMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfNoneMatch',
        serialization_name='If-None-Match',
        location='header',
        shape_name='IfNoneMatch',
    ))

    if_unmodified_since: IfUnmodifiedSince | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfUnmodifiedSince',
        serialization_name='If-Unmodified-Since',
        location='header',
        shape_name='IfUnmodifiedSince',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    range: Range | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Range',
        serialization_name='Range',
        location='header',
        shape_name='Range',
    ))

    response_cache_control: ResponseCacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseCacheControl',
        serialization_name='response-cache-control',
        location='querystring',
        shape_name='ResponseCacheControl',
    ))

    response_content_disposition: ResponseContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentDisposition',
        serialization_name='response-content-disposition',
        location='querystring',
        shape_name='ResponseContentDisposition',
    ))

    response_content_encoding: ResponseContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentEncoding',
        serialization_name='response-content-encoding',
        location='querystring',
        shape_name='ResponseContentEncoding',
    ))

    response_content_language: ResponseContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentLanguage',
        serialization_name='response-content-language',
        location='querystring',
        shape_name='ResponseContentLanguage',
    ))

    response_content_type: ResponseContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseContentType',
        serialization_name='response-content-type',
        location='querystring',
        shape_name='ResponseContentType',
    ))

    response_expires: ResponseExpires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ResponseExpires',
        serialization_name='response-expires',
        location='querystring',
        timestamp_format='rfc822',
        shape_name='ResponseExpires',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='versionId',
        location='querystring',
        shape_name='ObjectVersionId',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    part_number: PartNumber | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='PartNumber',
        serialization_name='partNumber',
        location='querystring',
        shape_name='PartNumber',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    checksum_mode: ChecksumMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMode',
        serialization_name='x-amz-checksum-mode',
        location='header',
        shape_name='ChecksumMode',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class Initiator(
    _base.Shape,
    shape_name='Initiator',
):
    i_d: ID | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ID',
        shape_name='ID',
    ))

    display_name: DisplayName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DisplayName',
        shape_name='DisplayName',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class InvalidObjectState(
    _base.Shape,
    shape_name='InvalidObjectState',
):
    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        shape_name='StorageClass',
    ))

    access_tier: IntelligentTieringAccessTier | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='AccessTier',
        shape_name='IntelligentTieringAccessTier',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class ListBucketsRequest(
    _base.Shape,
    shape_name='ListBucketsRequest',
):
    max_buckets: MaxBuckets | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MaxBuckets',
        serialization_name='max-buckets',
        location='querystring',
        shape_name='MaxBuckets',
    ))

    continuation_token: Token | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContinuationToken',
        serialization_name='continuation-token',
        location='querystring',
        shape_name='Token',
    ))

    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        serialization_name='prefix',
        location='querystring',
        shape_name='Prefix',
    ))

    bucket_region: BucketRegion | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketRegion',
        serialization_name='bucket-region',
        location='querystring',
        shape_name='BucketRegion',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class ListMultipartUploadsRequest(
    _base.Shape,
    shape_name='ListMultipartUploadsRequest',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    delimiter: Delimiter | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Delimiter',
        serialization_name='delimiter',
        location='querystring',
        shape_name='Delimiter',
    ))

    encoding_type: EncodingType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='EncodingType',
        serialization_name='encoding-type',
        location='querystring',
        shape_name='EncodingType',
    ))

    key_marker: KeyMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='KeyMarker',
        serialization_name='key-marker',
        location='querystring',
        shape_name='KeyMarker',
    ))

    max_uploads: MaxUploads | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MaxUploads',
        serialization_name='max-uploads',
        location='querystring',
        shape_name='MaxUploads',
    ))

    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        serialization_name='prefix',
        location='querystring',
        shape_name='Prefix',
    ))

    upload_id_marker: UploadIdMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='UploadIdMarker',
        serialization_name='upload-id-marker',
        location='querystring',
        shape_name='UploadIdMarker',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class LocationInfo(
    _base.Shape,
    shape_name='LocationInfo',
):
    type: LocationType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Type',
        shape_name='LocationType',
    ))

    name: LocationNameAsString | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Name',
        shape_name='LocationNameAsString',
    ))


Metadata: _ta.TypeAlias = _ta.Mapping[MetadataKey, MetadataValue]


@_dc.dataclass(frozen=True, kw_only=True)
class ObjectIdentifier(
    _base.Shape,
    shape_name='ObjectIdentifier',
):
    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        shape_name='ObjectVersionId',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        shape_name='ETag',
    ))

    last_modified_time: LastModifiedTime | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='LastModifiedTime',
        timestamp_format='rfc822',
        shape_name='LastModifiedTime',
    ))

    size: Size | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Size',
        shape_name='Size',
    ))


OptionalObjectAttributesList: _ta.TypeAlias = _ta.Sequence[OptionalObjectAttributes]


@_dc.dataclass(frozen=True, kw_only=True)
class Owner(
    _base.Shape,
    shape_name='Owner',
):
    display_name: DisplayName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DisplayName',
        shape_name='DisplayName',
    ))

    i_d: ID | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ID',
        shape_name='ID',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class PutObjectOutput(
    _base.Shape,
    shape_name='PutObjectOutput',
):
    expiration: Expiration | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expiration',
        serialization_name='x-amz-expiration',
        location='header',
        shape_name='Expiration',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        serialization_name='ETag',
        location='header',
        shape_name='ETag',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        serialization_name='x-amz-checksum-type',
        location='header',
        shape_name='ChecksumType',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='x-amz-version-id',
        location='header',
        shape_name='ObjectVersionId',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    sse_kms_encryption_context: SSEKMSEncryptionContext | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSEncryptionContext',
        serialization_name='x-amz-server-side-encryption-context',
        location='header',
        shape_name='SSEKMSEncryptionContext',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    size: Size | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Size',
        serialization_name='x-amz-object-size',
        location='header',
        shape_name='Size',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class RestoreStatus(
    _base.Shape,
    shape_name='RestoreStatus',
):
    is_restore_in_progress: IsRestoreInProgress | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IsRestoreInProgress',
        shape_name='IsRestoreInProgress',
    ))

    restore_expiry_date: RestoreExpiryDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RestoreExpiryDate',
        shape_name='RestoreExpiryDate',
    ))


TagSet: _ta.TypeAlias = _ta.Sequence[_base.Tag]


@_dc.dataclass(frozen=True, kw_only=True)
class UploadPartOutput(
    _base.Shape,
    shape_name='UploadPartOutput',
):
    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        serialization_name='ETag',
        location='header',
        shape_name='ETag',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class UploadPartRequest(
    _base.Shape,
    shape_name='UploadPartRequest',
    payload_member='Body',
):
    body: Body | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Body',
        streaming=True,
        shape_name='Body',
    ))

    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    content_length: ContentLength | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLength',
        serialization_name='Content-Length',
        location='header',
        shape_name='ContentLength',
    ))

    content_md5: ContentMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentMD5',
        serialization_name='Content-MD5',
        location='header',
        shape_name='ContentMD5',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        serialization_name='x-amz-sdk-checksum-algorithm',
        location='header',
        shape_name='ChecksumAlgorithm',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    part_number: PartNumber = _dc.field(metadata=_base.field_metadata(
        member_name='PartNumber',
        serialization_name='partNumber',
        location='querystring',
        shape_name='PartNumber',
    ))

    upload_id: MultipartUploadId = _dc.field(metadata=_base.field_metadata(
        member_name='UploadId',
        serialization_name='uploadId',
        location='querystring',
        shape_name='MultipartUploadId',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))


Buckets: _ta.TypeAlias = _ta.Sequence[Bucket]

CommonPrefixList: _ta.TypeAlias = _ta.Sequence[CommonPrefix]

CompletedPartList: _ta.TypeAlias = _ta.Sequence[CompletedPart]


@_dc.dataclass(frozen=True, kw_only=True)
class CopyObjectOutput(
    _base.Shape,
    shape_name='CopyObjectOutput',
    payload_member='CopyObjectResult',
):
    copy_object_result: CopyObjectResult | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopyObjectResult',
        shape_name='CopyObjectResult',
    ))

    expiration: Expiration | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expiration',
        serialization_name='x-amz-expiration',
        location='header',
        shape_name='Expiration',
    ))

    copy_source_version_id: CopySourceVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceVersionId',
        serialization_name='x-amz-copy-source-version-id',
        location='header',
        shape_name='CopySourceVersionId',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='x-amz-version-id',
        location='header',
        shape_name='ObjectVersionId',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    sse_kms_encryption_context: SSEKMSEncryptionContext | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSEncryptionContext',
        serialization_name='x-amz-server-side-encryption-context',
        location='header',
        shape_name='SSEKMSEncryptionContext',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CopyObjectRequest(
    _base.Shape,
    shape_name='CopyObjectRequest',
):
    acl: ObjectCannedACL | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ACL',
        serialization_name='x-amz-acl',
        location='header',
        shape_name='ObjectCannedACL',
    ))

    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    cache_control: CacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CacheControl',
        serialization_name='Cache-Control',
        location='header',
        shape_name='CacheControl',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        serialization_name='x-amz-checksum-algorithm',
        location='header',
        shape_name='ChecksumAlgorithm',
    ))

    content_disposition: ContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentDisposition',
        serialization_name='Content-Disposition',
        location='header',
        shape_name='ContentDisposition',
    ))

    content_encoding: ContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentEncoding',
        serialization_name='Content-Encoding',
        location='header',
        shape_name='ContentEncoding',
    ))

    content_language: ContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLanguage',
        serialization_name='Content-Language',
        location='header',
        shape_name='ContentLanguage',
    ))

    content_type: ContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentType',
        serialization_name='Content-Type',
        location='header',
        shape_name='ContentType',
    ))

    copy_source: CopySource = _dc.field(metadata=_base.field_metadata(
        member_name='CopySource',
        serialization_name='x-amz-copy-source',
        location='header',
        shape_name='CopySource',
    ))

    copy_source_if_match: CopySourceIfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceIfMatch',
        serialization_name='x-amz-copy-source-if-match',
        location='header',
        shape_name='CopySourceIfMatch',
    ))

    copy_source_if_modified_since: CopySourceIfModifiedSince | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceIfModifiedSince',
        serialization_name='x-amz-copy-source-if-modified-since',
        location='header',
        shape_name='CopySourceIfModifiedSince',
    ))

    copy_source_if_none_match: CopySourceIfNoneMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceIfNoneMatch',
        serialization_name='x-amz-copy-source-if-none-match',
        location='header',
        shape_name='CopySourceIfNoneMatch',
    ))

    copy_source_if_unmodified_since: CopySourceIfUnmodifiedSince | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceIfUnmodifiedSince',
        serialization_name='x-amz-copy-source-if-unmodified-since',
        location='header',
        shape_name='CopySourceIfUnmodifiedSince',
    ))

    expires: Expires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expires',
        serialization_name='Expires',
        location='header',
        shape_name='Expires',
    ))

    grant_full_control: GrantFullControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantFullControl',
        serialization_name='x-amz-grant-full-control',
        location='header',
        shape_name='GrantFullControl',
    ))

    grant_read: GrantRead | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantRead',
        serialization_name='x-amz-grant-read',
        location='header',
        shape_name='GrantRead',
    ))

    grant_read_acp: GrantReadACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantReadACP',
        serialization_name='x-amz-grant-read-acp',
        location='header',
        shape_name='GrantReadACP',
    ))

    grant_write_acp: GrantWriteACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantWriteACP',
        serialization_name='x-amz-grant-write-acp',
        location='header',
        shape_name='GrantWriteACP',
    ))

    if_match: IfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatch',
        serialization_name='If-Match',
        location='header',
        shape_name='IfMatch',
    ))

    if_none_match: IfNoneMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfNoneMatch',
        serialization_name='If-None-Match',
        location='header',
        shape_name='IfNoneMatch',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    metadata: Metadata | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Metadata',
        serialization_name='x-amz-meta-',
        location='headers',
        value_type=_base.MapValueType(MetadataKey, MetadataValue),
        shape_name='Metadata',
    ))

    metadata_directive: MetadataDirective | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MetadataDirective',
        serialization_name='x-amz-metadata-directive',
        location='header',
        shape_name='MetadataDirective',
    ))

    tagging_directive: TaggingDirective | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='TaggingDirective',
        serialization_name='x-amz-tagging-directive',
        location='header',
        shape_name='TaggingDirective',
    ))

    annotation_directive: AnnotationDirective | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='AnnotationDirective',
        serialization_name='x-amz-object-annotation-directive',
        location='header',
        shape_name='AnnotationDirective',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        serialization_name='x-amz-storage-class',
        location='header',
        shape_name='StorageClass',
    ))

    website_redirect_location: WebsiteRedirectLocation | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='WebsiteRedirectLocation',
        serialization_name='x-amz-website-redirect-location',
        location='header',
        shape_name='WebsiteRedirectLocation',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    sse_kms_encryption_context: SSEKMSEncryptionContext | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSEncryptionContext',
        serialization_name='x-amz-server-side-encryption-context',
        location='header',
        shape_name='SSEKMSEncryptionContext',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    copy_source_sse_customer_algorithm: CopySourceSSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceSSECustomerAlgorithm',
        serialization_name='x-amz-copy-source-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='CopySourceSSECustomerAlgorithm',
    ))

    copy_source_sse_customer_key: CopySourceSSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceSSECustomerKey',
        serialization_name='x-amz-copy-source-server-side-encryption-customer-key',
        location='header',
        shape_name='CopySourceSSECustomerKey',
    ))

    copy_source_sse_customer_key_md5: CopySourceSSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CopySourceSSECustomerKeyMD5',
        serialization_name='x-amz-copy-source-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='CopySourceSSECustomerKeyMD5',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    tagging: TaggingHeader | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Tagging',
        serialization_name='x-amz-tagging',
        location='header',
        shape_name='TaggingHeader',
    ))

    object_lock_mode: ObjectLockMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockMode',
        serialization_name='x-amz-object-lock-mode',
        location='header',
        shape_name='ObjectLockMode',
    ))

    object_lock_retain_until_date: ObjectLockRetainUntilDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockRetainUntilDate',
        serialization_name='x-amz-object-lock-retain-until-date',
        location='header',
        timestamp_format='iso8601',
        shape_name='ObjectLockRetainUntilDate',
    ))

    object_lock_legal_hold_status: ObjectLockLegalHoldStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockLegalHoldStatus',
        serialization_name='x-amz-object-lock-legal-hold',
        location='header',
        shape_name='ObjectLockLegalHoldStatus',
    ))

    object_lock_event_hold: ObjectLockEventHold | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHold',
        serialization_name='x-amz-object-lock-event-hold',
        location='header',
        shape_name='ObjectLockEventHold',
    ))

    object_lock_event_hold_duration_days: ObjectLockEventHoldDurationDays | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationDays',
        serialization_name='x-amz-object-lock-event-hold-duration-days',
        location='header',
        shape_name='ObjectLockEventHoldDurationDays',
    ))

    object_lock_event_hold_duration_years: ObjectLockEventHoldDurationYears | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationYears',
        serialization_name='x-amz-object-lock-event-hold-duration-years',
        location='header',
        shape_name='ObjectLockEventHoldDurationYears',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    expected_source_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedSourceBucketOwner',
        serialization_name='x-amz-source-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CreateBucketConfiguration(
    _base.Shape,
    shape_name='CreateBucketConfiguration',
):
    location_constraint: BucketLocationConstraint | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='LocationConstraint',
        shape_name='BucketLocationConstraint',
    ))

    location: LocationInfo | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Location',
        shape_name='LocationInfo',
    ))

    bucket: BucketInfo | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Bucket',
        shape_name='BucketInfo',
    ))

    tags: TagSet | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Tags',
        list_member_name='Tag',
        value_type=_base.ListValueType(_base.Tag),
        shape_name='TagSet',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CreateMultipartUploadRequest(
    _base.Shape,
    shape_name='CreateMultipartUploadRequest',
):
    acl: ObjectCannedACL | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ACL',
        serialization_name='x-amz-acl',
        location='header',
        shape_name='ObjectCannedACL',
    ))

    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    cache_control: CacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CacheControl',
        serialization_name='Cache-Control',
        location='header',
        shape_name='CacheControl',
    ))

    content_disposition: ContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentDisposition',
        serialization_name='Content-Disposition',
        location='header',
        shape_name='ContentDisposition',
    ))

    content_encoding: ContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentEncoding',
        serialization_name='Content-Encoding',
        location='header',
        shape_name='ContentEncoding',
    ))

    content_language: ContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLanguage',
        serialization_name='Content-Language',
        location='header',
        shape_name='ContentLanguage',
    ))

    content_type: ContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentType',
        serialization_name='Content-Type',
        location='header',
        shape_name='ContentType',
    ))

    expires: Expires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expires',
        serialization_name='Expires',
        location='header',
        shape_name='Expires',
    ))

    grant_full_control: GrantFullControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantFullControl',
        serialization_name='x-amz-grant-full-control',
        location='header',
        shape_name='GrantFullControl',
    ))

    grant_read: GrantRead | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantRead',
        serialization_name='x-amz-grant-read',
        location='header',
        shape_name='GrantRead',
    ))

    grant_read_acp: GrantReadACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantReadACP',
        serialization_name='x-amz-grant-read-acp',
        location='header',
        shape_name='GrantReadACP',
    ))

    grant_write_acp: GrantWriteACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantWriteACP',
        serialization_name='x-amz-grant-write-acp',
        location='header',
        shape_name='GrantWriteACP',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    metadata: Metadata | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Metadata',
        serialization_name='x-amz-meta-',
        location='headers',
        value_type=_base.MapValueType(MetadataKey, MetadataValue),
        shape_name='Metadata',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        serialization_name='x-amz-storage-class',
        location='header',
        shape_name='StorageClass',
    ))

    website_redirect_location: WebsiteRedirectLocation | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='WebsiteRedirectLocation',
        serialization_name='x-amz-website-redirect-location',
        location='header',
        shape_name='WebsiteRedirectLocation',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    sse_kms_encryption_context: SSEKMSEncryptionContext | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSEncryptionContext',
        serialization_name='x-amz-server-side-encryption-context',
        location='header',
        shape_name='SSEKMSEncryptionContext',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    tagging: TaggingHeader | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Tagging',
        serialization_name='x-amz-tagging',
        location='header',
        shape_name='TaggingHeader',
    ))

    object_lock_mode: ObjectLockMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockMode',
        serialization_name='x-amz-object-lock-mode',
        location='header',
        shape_name='ObjectLockMode',
    ))

    object_lock_retain_until_date: ObjectLockRetainUntilDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockRetainUntilDate',
        serialization_name='x-amz-object-lock-retain-until-date',
        location='header',
        timestamp_format='iso8601',
        shape_name='ObjectLockRetainUntilDate',
    ))

    object_lock_legal_hold_status: ObjectLockLegalHoldStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockLegalHoldStatus',
        serialization_name='x-amz-object-lock-legal-hold',
        location='header',
        shape_name='ObjectLockLegalHoldStatus',
    ))

    object_lock_event_hold: ObjectLockEventHold | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHold',
        serialization_name='x-amz-object-lock-event-hold',
        location='header',
        shape_name='ObjectLockEventHold',
    ))

    object_lock_event_hold_duration_days: ObjectLockEventHoldDurationDays | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationDays',
        serialization_name='x-amz-object-lock-event-hold-duration-days',
        location='header',
        shape_name='ObjectLockEventHoldDurationDays',
    ))

    object_lock_event_hold_duration_years: ObjectLockEventHoldDurationYears | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationYears',
        serialization_name='x-amz-object-lock-event-hold-duration-years',
        location='header',
        shape_name='ObjectLockEventHoldDurationYears',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        serialization_name='x-amz-checksum-algorithm',
        location='header',
        shape_name='ChecksumAlgorithm',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        serialization_name='x-amz-checksum-type',
        location='header',
        shape_name='ChecksumType',
    ))


DeletedObjects: _ta.TypeAlias = _ta.Sequence[DeletedObject]

Errors: _ta.TypeAlias = _ta.Sequence[Error]


@_dc.dataclass(frozen=True, kw_only=True)
class GetObjectOutput(
    _base.Shape,
    shape_name='GetObjectOutput',
    payload_member='Body',
):
    body: Body | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Body',
        streaming=True,
        shape_name='Body',
    ))

    delete_marker: DeleteMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DeleteMarker',
        serialization_name='x-amz-delete-marker',
        location='header',
        shape_name='DeleteMarker',
    ))

    accept_ranges: AcceptRanges | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='AcceptRanges',
        serialization_name='accept-ranges',
        location='header',
        shape_name='AcceptRanges',
    ))

    expiration: Expiration | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expiration',
        serialization_name='x-amz-expiration',
        location='header',
        shape_name='Expiration',
    ))

    restore: Restore | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Restore',
        serialization_name='x-amz-restore',
        location='header',
        shape_name='Restore',
    ))

    last_modified: LastModified | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='LastModified',
        serialization_name='Last-Modified',
        location='header',
        shape_name='LastModified',
    ))

    content_length: ContentLength | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLength',
        serialization_name='Content-Length',
        location='header',
        shape_name='ContentLength',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        serialization_name='ETag',
        location='header',
        shape_name='ETag',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        serialization_name='x-amz-checksum-type',
        location='header',
        shape_name='ChecksumType',
    ))

    missing_meta: MissingMeta | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MissingMeta',
        serialization_name='x-amz-missing-meta',
        location='header',
        shape_name='MissingMeta',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='x-amz-version-id',
        location='header',
        shape_name='ObjectVersionId',
    ))

    cache_control: CacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CacheControl',
        serialization_name='Cache-Control',
        location='header',
        shape_name='CacheControl',
    ))

    content_disposition: ContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentDisposition',
        serialization_name='Content-Disposition',
        location='header',
        shape_name='ContentDisposition',
    ))

    content_encoding: ContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentEncoding',
        serialization_name='Content-Encoding',
        location='header',
        shape_name='ContentEncoding',
    ))

    content_language: ContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLanguage',
        serialization_name='Content-Language',
        location='header',
        shape_name='ContentLanguage',
    ))

    content_range: ContentRange | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentRange',
        serialization_name='Content-Range',
        location='header',
        shape_name='ContentRange',
    ))

    content_type: ContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentType',
        serialization_name='Content-Type',
        location='header',
        shape_name='ContentType',
    ))

    expires: Expires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expires',
        serialization_name='Expires',
        location='header',
        shape_name='Expires',
    ))

    website_redirect_location: WebsiteRedirectLocation | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='WebsiteRedirectLocation',
        serialization_name='x-amz-website-redirect-location',
        location='header',
        shape_name='WebsiteRedirectLocation',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    metadata: Metadata | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Metadata',
        serialization_name='x-amz-meta-',
        location='headers',
        value_type=_base.MapValueType(MetadataKey, MetadataValue),
        shape_name='Metadata',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        serialization_name='x-amz-storage-class',
        location='header',
        shape_name='StorageClass',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))

    replication_status: ReplicationStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ReplicationStatus',
        serialization_name='x-amz-replication-status',
        location='header',
        shape_name='ReplicationStatus',
    ))

    parts_count: PartsCount | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='PartsCount',
        serialization_name='x-amz-mp-parts-count',
        location='header',
        shape_name='PartsCount',
    ))

    tag_count: TagCount | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='TagCount',
        serialization_name='x-amz-tagging-count',
        location='header',
        shape_name='TagCount',
    ))

    object_lock_mode: ObjectLockMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockMode',
        serialization_name='x-amz-object-lock-mode',
        location='header',
        shape_name='ObjectLockMode',
    ))

    object_lock_retain_until_date: ObjectLockRetainUntilDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockRetainUntilDate',
        serialization_name='x-amz-object-lock-retain-until-date',
        location='header',
        timestamp_format='iso8601',
        shape_name='ObjectLockRetainUntilDate',
    ))

    object_lock_legal_hold_status: ObjectLockLegalHoldStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockLegalHoldStatus',
        serialization_name='x-amz-object-lock-legal-hold',
        location='header',
        shape_name='ObjectLockLegalHoldStatus',
    ))

    object_lock_event_hold: ObjectLockEventHold | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHold',
        serialization_name='x-amz-object-lock-event-hold',
        location='header',
        shape_name='ObjectLockEventHold',
    ))

    object_lock_event_hold_duration_days: ObjectLockEventHoldDurationDays | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationDays',
        serialization_name='x-amz-object-lock-event-hold-duration-days',
        location='header',
        shape_name='ObjectLockEventHoldDurationDays',
    ))

    object_lock_event_hold_duration_years: ObjectLockEventHoldDurationYears | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationYears',
        serialization_name='x-amz-object-lock-event-hold-duration-years',
        location='header',
        shape_name='ObjectLockEventHoldDurationYears',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class HeadObjectOutput(
    _base.Shape,
    shape_name='HeadObjectOutput',
):
    delete_marker: DeleteMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='DeleteMarker',
        serialization_name='x-amz-delete-marker',
        location='header',
        shape_name='DeleteMarker',
    ))

    accept_ranges: AcceptRanges | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='AcceptRanges',
        serialization_name='accept-ranges',
        location='header',
        shape_name='AcceptRanges',
    ))

    expiration: Expiration | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expiration',
        serialization_name='x-amz-expiration',
        location='header',
        shape_name='Expiration',
    ))

    restore: Restore | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Restore',
        serialization_name='x-amz-restore',
        location='header',
        shape_name='Restore',
    ))

    archive_status: ArchiveStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ArchiveStatus',
        serialization_name='x-amz-archive-status',
        location='header',
        shape_name='ArchiveStatus',
    ))

    last_modified: LastModified | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='LastModified',
        serialization_name='Last-Modified',
        location='header',
        shape_name='LastModified',
    ))

    content_length: ContentLength | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLength',
        serialization_name='Content-Length',
        location='header',
        shape_name='ContentLength',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        serialization_name='x-amz-checksum-type',
        location='header',
        shape_name='ChecksumType',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        serialization_name='ETag',
        location='header',
        shape_name='ETag',
    ))

    missing_meta: MissingMeta | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MissingMeta',
        serialization_name='x-amz-missing-meta',
        location='header',
        shape_name='MissingMeta',
    ))

    version_id: ObjectVersionId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='VersionId',
        serialization_name='x-amz-version-id',
        location='header',
        shape_name='ObjectVersionId',
    ))

    cache_control: CacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CacheControl',
        serialization_name='Cache-Control',
        location='header',
        shape_name='CacheControl',
    ))

    content_disposition: ContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentDisposition',
        serialization_name='Content-Disposition',
        location='header',
        shape_name='ContentDisposition',
    ))

    content_encoding: ContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentEncoding',
        serialization_name='Content-Encoding',
        location='header',
        shape_name='ContentEncoding',
    ))

    content_language: ContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLanguage',
        serialization_name='Content-Language',
        location='header',
        shape_name='ContentLanguage',
    ))

    content_type: ContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentType',
        serialization_name='Content-Type',
        location='header',
        shape_name='ContentType',
    ))

    content_range: ContentRange | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentRange',
        serialization_name='Content-Range',
        location='header',
        shape_name='ContentRange',
    ))

    expires: Expires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expires',
        serialization_name='Expires',
        location='header',
        shape_name='Expires',
    ))

    website_redirect_location: WebsiteRedirectLocation | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='WebsiteRedirectLocation',
        serialization_name='x-amz-website-redirect-location',
        location='header',
        shape_name='WebsiteRedirectLocation',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    metadata: Metadata | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Metadata',
        serialization_name='x-amz-meta-',
        location='headers',
        value_type=_base.MapValueType(MetadataKey, MetadataValue),
        shape_name='Metadata',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        serialization_name='x-amz-storage-class',
        location='header',
        shape_name='StorageClass',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))

    replication_status: ReplicationStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ReplicationStatus',
        serialization_name='x-amz-replication-status',
        location='header',
        shape_name='ReplicationStatus',
    ))

    parts_count: PartsCount | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='PartsCount',
        serialization_name='x-amz-mp-parts-count',
        location='header',
        shape_name='PartsCount',
    ))

    tag_count: TagCount | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='TagCount',
        serialization_name='x-amz-tagging-count',
        location='header',
        shape_name='TagCount',
    ))

    object_lock_mode: ObjectLockMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockMode',
        serialization_name='x-amz-object-lock-mode',
        location='header',
        shape_name='ObjectLockMode',
    ))

    object_lock_retain_until_date: ObjectLockRetainUntilDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockRetainUntilDate',
        serialization_name='x-amz-object-lock-retain-until-date',
        location='header',
        timestamp_format='iso8601',
        shape_name='ObjectLockRetainUntilDate',
    ))

    object_lock_legal_hold_status: ObjectLockLegalHoldStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockLegalHoldStatus',
        serialization_name='x-amz-object-lock-legal-hold',
        location='header',
        shape_name='ObjectLockLegalHoldStatus',
    ))

    object_lock_event_hold: ObjectLockEventHold | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHold',
        serialization_name='x-amz-object-lock-event-hold',
        location='header',
        shape_name='ObjectLockEventHold',
    ))

    object_lock_event_hold_duration_days: ObjectLockEventHoldDurationDays | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationDays',
        serialization_name='x-amz-object-lock-event-hold-duration-days',
        location='header',
        shape_name='ObjectLockEventHoldDurationDays',
    ))

    object_lock_event_hold_duration_years: ObjectLockEventHoldDurationYears | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationYears',
        serialization_name='x-amz-object-lock-event-hold-duration-years',
        location='header',
        shape_name='ObjectLockEventHoldDurationYears',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class ListObjectsV2Request(
    _base.Shape,
    shape_name='ListObjectsV2Request',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    delimiter: Delimiter | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Delimiter',
        serialization_name='delimiter',
        location='querystring',
        shape_name='Delimiter',
    ))

    encoding_type: EncodingType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='EncodingType',
        serialization_name='encoding-type',
        location='querystring',
        shape_name='EncodingType',
    ))

    max_keys: MaxKeys | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MaxKeys',
        serialization_name='max-keys',
        location='querystring',
        shape_name='MaxKeys',
    ))

    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        serialization_name='prefix',
        location='querystring',
        shape_name='Prefix',
    ))

    continuation_token: Token | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContinuationToken',
        serialization_name='continuation-token',
        location='querystring',
        shape_name='Token',
    ))

    fetch_owner: FetchOwner | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='FetchOwner',
        serialization_name='fetch-owner',
        location='querystring',
        shape_name='FetchOwner',
    ))

    start_after: StartAfter | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StartAfter',
        serialization_name='start-after',
        location='querystring',
        shape_name='StartAfter',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    optional_object_attributes: OptionalObjectAttributesList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='OptionalObjectAttributes',
        serialization_name='x-amz-optional-object-attributes',
        location='header',
        value_type=_base.ListValueType(OptionalObjectAttributes),
        shape_name='OptionalObjectAttributesList',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class MultipartUpload(
    _base.Shape,
    shape_name='MultipartUpload',
):
    upload_id: MultipartUploadId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='UploadId',
        shape_name='MultipartUploadId',
    ))

    key: ObjectKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    initiated: Initiated | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Initiated',
        shape_name='Initiated',
    ))

    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        shape_name='StorageClass',
    ))

    owner: Owner | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Owner',
        shape_name='Owner',
    ))

    initiator: Initiator | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Initiator',
        shape_name='Initiator',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        shape_name='ChecksumAlgorithm',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        shape_name='ChecksumType',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class Object(
    _base.Shape,
    shape_name='Object',
):
    key: ObjectKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Key',
        shape_name='ObjectKey',
    ))

    last_modified: LastModified | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='LastModified',
        shape_name='LastModified',
    ))

    etag: ETag | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ETag',
        shape_name='ETag',
    ))

    checksum_algorithm: ChecksumAlgorithmList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        xml_flattened=True,
        value_type=_base.ListValueType(ChecksumAlgorithm),
        shape_name='ChecksumAlgorithmList',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        shape_name='ChecksumType',
    ))

    size: Size | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Size',
        shape_name='Size',
    ))

    storage_class: ObjectStorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        shape_name='ObjectStorageClass',
    ))

    owner: Owner | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Owner',
        shape_name='Owner',
    ))

    restore_status: RestoreStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RestoreStatus',
        shape_name='RestoreStatus',
    ))


ObjectIdentifierList: _ta.TypeAlias = _ta.Sequence[ObjectIdentifier]


@_dc.dataclass(frozen=True, kw_only=True)
class PutObjectRequest(
    _base.Shape,
    shape_name='PutObjectRequest',
    payload_member='Body',
):
    acl: ObjectCannedACL | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ACL',
        serialization_name='x-amz-acl',
        location='header',
        shape_name='ObjectCannedACL',
    ))

    body: Body | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Body',
        streaming=True,
        shape_name='Body',
    ))

    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    cache_control: CacheControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CacheControl',
        serialization_name='Cache-Control',
        location='header',
        shape_name='CacheControl',
    ))

    content_disposition: ContentDisposition | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentDisposition',
        serialization_name='Content-Disposition',
        location='header',
        shape_name='ContentDisposition',
    ))

    content_encoding: ContentEncoding | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentEncoding',
        serialization_name='Content-Encoding',
        location='header',
        shape_name='ContentEncoding',
    ))

    content_language: ContentLanguage | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLanguage',
        serialization_name='Content-Language',
        location='header',
        shape_name='ContentLanguage',
    ))

    content_length: ContentLength | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentLength',
        serialization_name='Content-Length',
        location='header',
        shape_name='ContentLength',
    ))

    content_md5: ContentMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentMD5',
        serialization_name='Content-MD5',
        location='header',
        shape_name='ContentMD5',
    ))

    content_type: ContentType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContentType',
        serialization_name='Content-Type',
        location='header',
        shape_name='ContentType',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        serialization_name='x-amz-sdk-checksum-algorithm',
        location='header',
        shape_name='ChecksumAlgorithm',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    expires: Expires | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Expires',
        serialization_name='Expires',
        location='header',
        shape_name='Expires',
    ))

    if_match: IfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatch',
        serialization_name='If-Match',
        location='header',
        shape_name='IfMatch',
    ))

    if_none_match: IfNoneMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfNoneMatch',
        serialization_name='If-None-Match',
        location='header',
        shape_name='IfNoneMatch',
    ))

    grant_full_control: GrantFullControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantFullControl',
        serialization_name='x-amz-grant-full-control',
        location='header',
        shape_name='GrantFullControl',
    ))

    grant_read: GrantRead | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantRead',
        serialization_name='x-amz-grant-read',
        location='header',
        shape_name='GrantRead',
    ))

    grant_read_acp: GrantReadACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantReadACP',
        serialization_name='x-amz-grant-read-acp',
        location='header',
        shape_name='GrantReadACP',
    ))

    grant_write_acp: GrantWriteACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantWriteACP',
        serialization_name='x-amz-grant-write-acp',
        location='header',
        shape_name='GrantWriteACP',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    write_offset_bytes: WriteOffsetBytes | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='WriteOffsetBytes',
        serialization_name='x-amz-write-offset-bytes',
        location='header',
        shape_name='WriteOffsetBytes',
    ))

    metadata: Metadata | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Metadata',
        serialization_name='x-amz-meta-',
        location='headers',
        value_type=_base.MapValueType(MetadataKey, MetadataValue),
        shape_name='Metadata',
    ))

    server_side_encryption: ServerSideEncryption | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ServerSideEncryption',
        serialization_name='x-amz-server-side-encryption',
        location='header',
        shape_name='ServerSideEncryption',
    ))

    storage_class: StorageClass | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StorageClass',
        serialization_name='x-amz-storage-class',
        location='header',
        shape_name='StorageClass',
    ))

    website_redirect_location: WebsiteRedirectLocation | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='WebsiteRedirectLocation',
        serialization_name='x-amz-website-redirect-location',
        location='header',
        shape_name='WebsiteRedirectLocation',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))

    sse_kms_key_id: SSEKMSKeyId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSKeyId',
        serialization_name='x-amz-server-side-encryption-aws-kms-key-id',
        location='header',
        shape_name='SSEKMSKeyId',
    ))

    sse_kms_encryption_context: SSEKMSEncryptionContext | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSEKMSEncryptionContext',
        serialization_name='x-amz-server-side-encryption-context',
        location='header',
        shape_name='SSEKMSEncryptionContext',
    ))

    bucket_key_enabled: BucketKeyEnabled | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketKeyEnabled',
        serialization_name='x-amz-server-side-encryption-bucket-key-enabled',
        location='header',
        shape_name='BucketKeyEnabled',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    tagging: TaggingHeader | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Tagging',
        serialization_name='x-amz-tagging',
        location='header',
        shape_name='TaggingHeader',
    ))

    object_lock_mode: ObjectLockMode | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockMode',
        serialization_name='x-amz-object-lock-mode',
        location='header',
        shape_name='ObjectLockMode',
    ))

    object_lock_retain_until_date: ObjectLockRetainUntilDate | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockRetainUntilDate',
        serialization_name='x-amz-object-lock-retain-until-date',
        location='header',
        timestamp_format='iso8601',
        shape_name='ObjectLockRetainUntilDate',
    ))

    object_lock_legal_hold_status: ObjectLockLegalHoldStatus | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockLegalHoldStatus',
        serialization_name='x-amz-object-lock-legal-hold',
        location='header',
        shape_name='ObjectLockLegalHoldStatus',
    ))

    object_lock_event_hold: ObjectLockEventHold | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHold',
        serialization_name='x-amz-object-lock-event-hold',
        location='header',
        shape_name='ObjectLockEventHold',
    ))

    object_lock_event_hold_duration_days: ObjectLockEventHoldDurationDays | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationDays',
        serialization_name='x-amz-object-lock-event-hold-duration-days',
        location='header',
        shape_name='ObjectLockEventHoldDurationDays',
    ))

    object_lock_event_hold_duration_years: ObjectLockEventHoldDurationYears | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEventHoldDurationYears',
        serialization_name='x-amz-object-lock-event-hold-duration-years',
        location='header',
        shape_name='ObjectLockEventHoldDurationYears',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CompletedMultipartUpload(
    _base.Shape,
    shape_name='CompletedMultipartUpload',
):
    parts: CompletedPartList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Parts',
        serialization_name='Part',
        xml_flattened=True,
        value_type=_base.ListValueType(CompletedPart),
        shape_name='CompletedPartList',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class CreateBucketRequest(
    _base.Shape,
    shape_name='CreateBucketRequest',
    payload_member='CreateBucketConfiguration',
):
    acl: BucketCannedACL | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ACL',
        serialization_name='x-amz-acl',
        location='header',
        shape_name='BucketCannedACL',
    ))

    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    create_bucket_configuration: CreateBucketConfiguration | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CreateBucketConfiguration',
        serialization_name='CreateBucketConfiguration',
        xml_namespace='http://s3.amazonaws.com/doc/2006-03-01/',
        shape_name='CreateBucketConfiguration',
    ))

    grant_full_control: GrantFullControl | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantFullControl',
        serialization_name='x-amz-grant-full-control',
        location='header',
        shape_name='GrantFullControl',
    ))

    grant_read: GrantRead | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantRead',
        serialization_name='x-amz-grant-read',
        location='header',
        shape_name='GrantRead',
    ))

    grant_read_acp: GrantReadACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantReadACP',
        serialization_name='x-amz-grant-read-acp',
        location='header',
        shape_name='GrantReadACP',
    ))

    grant_write: GrantWrite | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantWrite',
        serialization_name='x-amz-grant-write',
        location='header',
        shape_name='GrantWrite',
    ))

    grant_write_acp: GrantWriteACP | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='GrantWriteACP',
        serialization_name='x-amz-grant-write-acp',
        location='header',
        shape_name='GrantWriteACP',
    ))

    object_lock_enabled_for_bucket: ObjectLockEnabledForBucket | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectLockEnabledForBucket',
        serialization_name='x-amz-bucket-object-lock-enabled',
        location='header',
        shape_name='ObjectLockEnabledForBucket',
    ))

    object_ownership: ObjectOwnership | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ObjectOwnership',
        serialization_name='x-amz-object-ownership',
        location='header',
        shape_name='ObjectOwnership',
    ))

    bucket_namespace: BucketNamespace | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BucketNamespace',
        serialization_name='x-amz-bucket-namespace',
        location='header',
        shape_name='BucketNamespace',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class Delete(
    _base.Shape,
    shape_name='Delete',
):
    objects: ObjectIdentifierList = _dc.field(metadata=_base.field_metadata(
        member_name='Objects',
        serialization_name='Object',
        xml_flattened=True,
        value_type=_base.ListValueType(ObjectIdentifier),
        shape_name='ObjectIdentifierList',
    ))

    quiet: Quiet | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Quiet',
        shape_name='Quiet',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class DeleteObjectsOutput(
    _base.Shape,
    shape_name='DeleteObjectsOutput',
):
    deleted: DeletedObjects | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Deleted',
        xml_flattened=True,
        value_type=_base.ListValueType(DeletedObject),
        shape_name='DeletedObjects',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))

    errors: Errors | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Errors',
        serialization_name='Error',
        xml_flattened=True,
        value_type=_base.ListValueType(Error),
        shape_name='Errors',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class ListBucketsOutput(
    _base.Shape,
    shape_name='ListBucketsOutput',
):
    buckets: Buckets | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Buckets',
        list_member_name='Bucket',
        value_type=_base.ListValueType(Bucket),
        shape_name='Buckets',
    ))

    owner: Owner | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Owner',
        shape_name='Owner',
    ))

    continuation_token: NextToken | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContinuationToken',
        shape_name='NextToken',
    ))

    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        shape_name='Prefix',
    ))


MultipartUploadList: _ta.TypeAlias = _ta.Sequence[MultipartUpload]

ObjectList: _ta.TypeAlias = _ta.Sequence[Object]


@_dc.dataclass(frozen=True, kw_only=True)
class CompleteMultipartUploadRequest(
    _base.Shape,
    shape_name='CompleteMultipartUploadRequest',
    payload_member='MultipartUpload',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    key: ObjectKey = _dc.field(metadata=_base.field_metadata(
        member_name='Key',
        serialization_name='Key',
        location='uri',
        shape_name='ObjectKey',
    ))

    multipart_upload: CompletedMultipartUpload | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MultipartUpload',
        serialization_name='CompleteMultipartUpload',
        xml_namespace='http://s3.amazonaws.com/doc/2006-03-01/',
        shape_name='CompletedMultipartUpload',
    ))

    upload_id: MultipartUploadId = _dc.field(metadata=_base.field_metadata(
        member_name='UploadId',
        serialization_name='uploadId',
        location='querystring',
        shape_name='MultipartUploadId',
    ))

    checksum_crc32: ChecksumCRC32 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32',
        serialization_name='x-amz-checksum-crc32',
        location='header',
        shape_name='ChecksumCRC32',
    ))

    checksum_crc32c: ChecksumCRC32C | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC32C',
        serialization_name='x-amz-checksum-crc32c',
        location='header',
        shape_name='ChecksumCRC32C',
    ))

    checksum_crc64nvme: ChecksumCRC64NVME | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumCRC64NVME',
        serialization_name='x-amz-checksum-crc64nvme',
        location='header',
        shape_name='ChecksumCRC64NVME',
    ))

    checksum_sha1: ChecksumSHA1 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA1',
        serialization_name='x-amz-checksum-sha1',
        location='header',
        shape_name='ChecksumSHA1',
    ))

    checksum_sha256: ChecksumSHA256 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA256',
        serialization_name='x-amz-checksum-sha256',
        location='header',
        shape_name='ChecksumSHA256',
    ))

    checksum_sha512: ChecksumSHA512 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumSHA512',
        serialization_name='x-amz-checksum-sha512',
        location='header',
        shape_name='ChecksumSHA512',
    ))

    checksum_md5: ChecksumMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumMD5',
        serialization_name='x-amz-checksum-md5',
        location='header',
        shape_name='ChecksumMD5',
    ))

    checksum_xxhash64: ChecksumXXHASH64 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH64',
        serialization_name='x-amz-checksum-xxhash64',
        location='header',
        shape_name='ChecksumXXHASH64',
    ))

    checksum_xxhash3: ChecksumXXHASH3 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH3',
        serialization_name='x-amz-checksum-xxhash3',
        location='header',
        shape_name='ChecksumXXHASH3',
    ))

    checksum_xxhash128: ChecksumXXHASH128 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumXXHASH128',
        serialization_name='x-amz-checksum-xxhash128',
        location='header',
        shape_name='ChecksumXXHASH128',
    ))

    checksum_type: ChecksumType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumType',
        serialization_name='x-amz-checksum-type',
        location='header',
        shape_name='ChecksumType',
    ))

    mpu_object_size: MpuObjectSize | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MpuObjectSize',
        serialization_name='x-amz-mp-object-size',
        location='header',
        shape_name='MpuObjectSize',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    if_match: IfMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfMatch',
        serialization_name='If-Match',
        location='header',
        shape_name='IfMatch',
    ))

    if_none_match: IfNoneMatch | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IfNoneMatch',
        serialization_name='If-None-Match',
        location='header',
        shape_name='IfNoneMatch',
    ))

    sse_customer_algorithm: SSECustomerAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerAlgorithm',
        serialization_name='x-amz-server-side-encryption-customer-algorithm',
        location='header',
        shape_name='SSECustomerAlgorithm',
    ))

    sse_customer_key: SSECustomerKey | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKey',
        serialization_name='x-amz-server-side-encryption-customer-key',
        location='header',
        shape_name='SSECustomerKey',
    ))

    sse_customer_key_md5: SSECustomerKeyMD5 | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='SSECustomerKeyMD5',
        serialization_name='x-amz-server-side-encryption-customer-key-MD5',
        location='header',
        shape_name='SSECustomerKeyMD5',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class DeleteObjectsRequest(
    _base.Shape,
    shape_name='DeleteObjectsRequest',
    payload_member='Delete',
):
    bucket: BucketName = _dc.field(metadata=_base.field_metadata(
        member_name='Bucket',
        serialization_name='Bucket',
        location='uri',
        shape_name='BucketName',
    ))

    delete: Delete = _dc.field(metadata=_base.field_metadata(
        member_name='Delete',
        serialization_name='Delete',
        xml_namespace='http://s3.amazonaws.com/doc/2006-03-01/',
        shape_name='Delete',
    ))

    mfa: MFA | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MFA',
        serialization_name='x-amz-mfa',
        location='header',
        shape_name='MFA',
    ))

    request_payer: RequestPayer | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestPayer',
        serialization_name='x-amz-request-payer',
        location='header',
        shape_name='RequestPayer',
    ))

    bypass_governance_retention: BypassGovernanceRetention | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='BypassGovernanceRetention',
        serialization_name='x-amz-bypass-governance-retention',
        location='header',
        shape_name='BypassGovernanceRetention',
    ))

    expected_bucket_owner: AccountId | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ExpectedBucketOwner',
        serialization_name='x-amz-expected-bucket-owner',
        location='header',
        shape_name='AccountId',
    ))

    checksum_algorithm: ChecksumAlgorithm | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ChecksumAlgorithm',
        serialization_name='x-amz-sdk-checksum-algorithm',
        location='header',
        shape_name='ChecksumAlgorithm',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class ListMultipartUploadsOutput(
    _base.Shape,
    shape_name='ListMultipartUploadsOutput',
):
    bucket: BucketName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Bucket',
        shape_name='BucketName',
    ))

    key_marker: KeyMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='KeyMarker',
        shape_name='KeyMarker',
    ))

    upload_id_marker: UploadIdMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='UploadIdMarker',
        shape_name='UploadIdMarker',
    ))

    next_key_marker: NextKeyMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='NextKeyMarker',
        shape_name='NextKeyMarker',
    ))

    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        shape_name='Prefix',
    ))

    delimiter: Delimiter | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Delimiter',
        shape_name='Delimiter',
    ))

    next_upload_id_marker: NextUploadIdMarker | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='NextUploadIdMarker',
        shape_name='NextUploadIdMarker',
    ))

    max_uploads: MaxUploads | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MaxUploads',
        shape_name='MaxUploads',
    ))

    is_truncated: IsTruncated | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IsTruncated',
        shape_name='IsTruncated',
    ))

    uploads: MultipartUploadList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Uploads',
        serialization_name='Upload',
        xml_flattened=True,
        value_type=_base.ListValueType(MultipartUpload),
        shape_name='MultipartUploadList',
    ))

    common_prefixes: CommonPrefixList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CommonPrefixes',
        xml_flattened=True,
        value_type=_base.ListValueType(CommonPrefix),
        shape_name='CommonPrefixList',
    ))

    encoding_type: EncodingType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='EncodingType',
        shape_name='EncodingType',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


@_dc.dataclass(frozen=True, kw_only=True)
class ListObjectsV2Output(
    _base.Shape,
    shape_name='ListObjectsV2Output',
):
    is_truncated: IsTruncated | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='IsTruncated',
        shape_name='IsTruncated',
    ))

    contents: ObjectList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Contents',
        xml_flattened=True,
        value_type=_base.ListValueType(Object),
        shape_name='ObjectList',
    ))

    name: BucketName | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Name',
        shape_name='BucketName',
    ))

    prefix: Prefix | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Prefix',
        shape_name='Prefix',
    ))

    delimiter: Delimiter | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='Delimiter',
        shape_name='Delimiter',
    ))

    max_keys: MaxKeys | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='MaxKeys',
        shape_name='MaxKeys',
    ))

    common_prefixes: CommonPrefixList | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='CommonPrefixes',
        xml_flattened=True,
        value_type=_base.ListValueType(CommonPrefix),
        shape_name='CommonPrefixList',
    ))

    encoding_type: EncodingType | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='EncodingType',
        shape_name='EncodingType',
    ))

    key_count: KeyCount | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='KeyCount',
        shape_name='KeyCount',
    ))

    continuation_token: Token | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='ContinuationToken',
        shape_name='Token',
    ))

    next_continuation_token: NextToken | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='NextContinuationToken',
        shape_name='NextToken',
    ))

    start_after: StartAfter | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='StartAfter',
        shape_name='StartAfter',
    ))

    request_charged: RequestCharged | None = _dc.field(default=None, metadata=_base.field_metadata(
        member_name='RequestCharged',
        serialization_name='x-amz-request-charged',
        location='header',
        shape_name='RequestCharged',
    ))


ALL_SHAPES: frozenset[type[_base.Shape]] = frozenset([
    AbortMultipartUploadOutput,
    AbortMultipartUploadRequest,
    Bucket,
    BucketAlreadyExists,
    BucketAlreadyOwnedByYou,
    BucketInfo,
    CommonPrefix,
    CompleteMultipartUploadOutput,
    CompleteMultipartUploadRequest,
    CompletedMultipartUpload,
    CompletedPart,
    CopyObjectOutput,
    CopyObjectRequest,
    CopyObjectResult,
    CreateBucketConfiguration,
    CreateBucketOutput,
    CreateBucketRequest,
    CreateMultipartUploadOutput,
    CreateMultipartUploadRequest,
    Delete,
    DeleteBucketRequest,
    DeleteObjectOutput,
    DeleteObjectRequest,
    DeleteObjectsOutput,
    DeleteObjectsRequest,
    DeletedObject,
    EncryptionTypeMismatch,
    Error,
    GetObjectOutput,
    GetObjectRequest,
    HeadObjectOutput,
    HeadObjectRequest,
    Initiator,
    InvalidObjectState,
    InvalidRequest,
    InvalidWriteOffset,
    ListBucketsOutput,
    ListBucketsRequest,
    ListMultipartUploadsOutput,
    ListMultipartUploadsRequest,
    ListObjectsV2Output,
    ListObjectsV2Request,
    LocationInfo,
    MultipartUpload,
    NoSuchBucket,
    NoSuchKey,
    NoSuchUpload,
    Object,
    ObjectIdentifier,
    ObjectNotInActiveTierError,
    Owner,
    PutObjectOutput,
    PutObjectRequest,
    RestoreStatus,
    TooManyParts,
    UploadPartOutput,
    UploadPartRequest,
])


##


ABORT_MULTIPART_UPLOAD = _base.Operation(
    name='AbortMultipartUpload',
    input=AbortMultipartUploadRequest,
    output=AbortMultipartUploadOutput,
    errors=[
        NoSuchUpload,
    ],
    http_method='DELETE',
    http_request_uri='/{Bucket}/{Key+}',
    http_response_code=204,
)

COMPLETE_MULTIPART_UPLOAD = _base.Operation(
    name='CompleteMultipartUpload',
    input=CompleteMultipartUploadRequest,
    output=CompleteMultipartUploadOutput,
    http_method='POST',
    http_request_uri='/{Bucket}/{Key+}',
)

COPY_OBJECT = _base.Operation(
    name='CopyObject',
    input=CopyObjectRequest,
    output=CopyObjectOutput,
    errors=[
        ObjectNotInActiveTierError,
    ],
    http_method='PUT',
    http_request_uri='/{Bucket}/{Key+}',
)

CREATE_BUCKET = _base.Operation(
    name='CreateBucket',
    input=CreateBucketRequest,
    output=CreateBucketOutput,
    errors=[
        BucketAlreadyExists,
        BucketAlreadyOwnedByYou,
    ],
    http_method='PUT',
    http_request_uri='/{Bucket}',
)

CREATE_MULTIPART_UPLOAD = _base.Operation(
    name='CreateMultipartUpload',
    input=CreateMultipartUploadRequest,
    output=CreateMultipartUploadOutput,
    http_method='POST',
    http_request_uri='/{Bucket}/{Key+}?uploads',
)

DELETE_BUCKET = _base.Operation(
    name='DeleteBucket',
    input=DeleteBucketRequest,
    http_method='DELETE',
    http_request_uri='/{Bucket}',
    http_response_code=204,
)

DELETE_OBJECT = _base.Operation(
    name='DeleteObject',
    input=DeleteObjectRequest,
    output=DeleteObjectOutput,
    http_method='DELETE',
    http_request_uri='/{Bucket}/{Key+}',
    http_response_code=204,
)

DELETE_OBJECTS = _base.Operation(
    name='DeleteObjects',
    input=DeleteObjectsRequest,
    output=DeleteObjectsOutput,
    http_method='POST',
    http_request_uri='/{Bucket}?delete',
)

GET_OBJECT = _base.Operation(
    name='GetObject',
    input=GetObjectRequest,
    output=GetObjectOutput,
    errors=[
        InvalidObjectState,
        NoSuchKey,
    ],
    http_method='GET',
    http_request_uri='/{Bucket}/{Key+}',
)

HEAD_OBJECT = _base.Operation(
    name='HeadObject',
    input=HeadObjectRequest,
    output=HeadObjectOutput,
    errors=[
        NoSuchKey,
    ],
    http_method='HEAD',
    http_request_uri='/{Bucket}/{Key+}',
)

LIST_BUCKETS = _base.Operation(
    name='ListBuckets',
    input=ListBucketsRequest,
    output=ListBucketsOutput,
    http_method='GET',
    http_request_uri='/',
)

LIST_MULTIPART_UPLOADS = _base.Operation(
    name='ListMultipartUploads',
    input=ListMultipartUploadsRequest,
    output=ListMultipartUploadsOutput,
    http_method='GET',
    http_request_uri='/{Bucket}?uploads',
)

LIST_OBJECTS_V2 = _base.Operation(
    name='ListObjectsV2',
    input=ListObjectsV2Request,
    output=ListObjectsV2Output,
    errors=[
        NoSuchBucket,
    ],
    http_method='GET',
    http_request_uri='/{Bucket}?list-type=2',
)

PUT_OBJECT = _base.Operation(
    name='PutObject',
    input=PutObjectRequest,
    output=PutObjectOutput,
    errors=[
        EncryptionTypeMismatch,
        InvalidRequest,
        InvalidWriteOffset,
        TooManyParts,
    ],
    http_method='PUT',
    http_request_uri='/{Bucket}/{Key+}',
)

UPLOAD_PART = _base.Operation(
    name='UploadPart',
    input=UploadPartRequest,
    output=UploadPartOutput,
    http_method='PUT',
    http_request_uri='/{Bucket}/{Key+}',
)


ALL_OPERATIONS: frozenset[_base.Operation] = frozenset([
    ABORT_MULTIPART_UPLOAD,
    COMPLETE_MULTIPART_UPLOAD,
    COPY_OBJECT,
    CREATE_BUCKET,
    CREATE_MULTIPART_UPLOAD,
    DELETE_BUCKET,
    DELETE_OBJECT,
    DELETE_OBJECTS,
    GET_OBJECT,
    HEAD_OBJECT,
    LIST_BUCKETS,
    LIST_MULTIPART_UPLOADS,
    LIST_OBJECTS_V2,
    PUT_OBJECT,
    UPLOAD_PART,
])
