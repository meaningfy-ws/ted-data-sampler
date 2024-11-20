import hashlib
import json
import sys
import tempfile
from logging import Logger
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field

from ted_data_sampler.core.adapters.GitHubDownloader import GitHubDownloader
from ted_data_sampler.core.services.logger import setup_logger

FIELDS_PATH_NAME = "fields"
FIELDS_JSON_FILE_NAME = "fields.json"
NOTICE_TYPES_PATH_NAME = "notice-types"
EFORMS_SDK_GITHUB_LINK = "https://github.com/OP-TED/eForms-SDK"

import_logger: Logger = setup_logger([])


class EFormsFieldsRepeatableAttribute(BaseModel):
    value: bool
    severity: str


class EFormsField(BaseModel):
    id: str
    parent_node_id: str = Field(..., alias='parentNodeId')
    name: str
    xpath_absolute: str = Field(..., alias='xpathAbsolute')
    xpath_relative: str = Field(..., alias='xpathRelative')
    value_type: str = Field(..., alias='type')
    bt_id: Optional[str] = Field(default=None, alias='btId')
    legal_type: Optional[str] = Field(default=None, alias='legalType')
    repeatable: EFormsFieldsRepeatableAttribute

    def generate_hash_id(self, project_id: str = None) -> str:
        fields_to_hash = [project_id, self.id, self.xpath_absolute, self.xpath_relative, self.repeatable.value,
                          self.parent_node_id, self.name, self.bt_id, self.value_type,
                          self.legal_type]
        str_content = "_".join(map(str, fields_to_hash))
        return str(hashlib.sha1(str_content.encode("utf-8")).hexdigest())


class EFormsNode(BaseModel):
    id: str
    parent_id: Optional[str] = Field(default=None, alias='parentId')
    xpath_absolute: str = Field(..., alias='xpathAbsolute')
    xpath_relative: str = Field(..., alias='xpathRelative')
    repeatable: bool

    def generate_hash_id(self, project_id: str = None):
        fields_to_hash = [
            project_id, self.id, self.xpath_absolute, self.xpath_relative, self.repeatable, self.parent_id
        ]
        str_content = "_".join(map(str, fields_to_hash))
        return str(hashlib.sha1(str_content.encode("utf-8")).hexdigest())


class EFormsSDKFields(BaseModel):
    ubl_version: str = Field(..., alias='ublVersion')
    sdk_version: str = Field(..., alias='sdkVersion')
    xml_structure: List[EFormsNode] = Field(..., alias='xmlStructure')
    fields: List[EFormsField]


def extract_xpaths_from_eforms_fields(eforms_sdk_fields: EFormsSDKFields) -> List[str]:
    return [field.xpath_absolute for field in eforms_sdk_fields.fields]


def import_eforms_fields_from_folder(eforms_fields_folder_path: Path) -> EFormsSDKFields:
    notice_types_dir_path: Path = eforms_fields_folder_path / NOTICE_TYPES_PATH_NAME
    fields_dir_path: Path = eforms_fields_folder_path / FIELDS_PATH_NAME
    fields_json_path: Path = fields_dir_path / FIELDS_JSON_FILE_NAME

    with fields_json_path.open() as fields_json_file:
        eforms_fields_content = json.load(fields_json_file)
        eforms_sdk_fields: EFormsSDKFields = EFormsSDKFields(**eforms_fields_content)

    return eforms_sdk_fields


def import_eforms_fields_from_github_repository(
        github_repository_url: str,
        branch_or_tag_name: str,
) -> EFormsSDKFields:
    github_downloader = GitHubDownloader(github_repository_url=github_repository_url,
                                         branch_or_tag_name=branch_or_tag_name)

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_dir_path = Path(tmp_dir)
        github_downloader.download(result_dir_path=temp_dir_path,
                                   download_resources_filter=[FIELDS_PATH_NAME, NOTICE_TYPES_PATH_NAME])
        eforms_sdk_fields: EFormsSDKFields = import_eforms_fields_from_folder(
            eforms_fields_folder_path=temp_dir_path,
        )

    return eforms_sdk_fields


def extract_xpaths_by_sdk_version(sdk_version: str) -> List[str]:
    import_logger.info(
        f"Extracting XPaths form eForms SDK Fields from {EFORMS_SDK_GITHUB_LINK} with branch or tag name: {sdk_version}")
    eforms_sdk_fields: EFormsSDKFields = import_eforms_fields_from_github_repository(
        github_repository_url=EFORMS_SDK_GITHUB_LINK,
        branch_or_tag_name=sdk_version
    )

    xpaths: List[str] = extract_xpaths_from_eforms_fields(eforms_sdk_fields=eforms_sdk_fields)
    import_logger.info(f"Nr of extracted xpaths from SDK version {sdk_version}: {len(xpaths)}")
    return xpaths


def extract_xpaths_by_list_of_sdk_versions(sdk_versions: List[str]) -> List[str]:
    xpaths: List[str] = []
    import_logger.info(f"Extracting XPaths form {sdk_versions} SDK versions")
    for sdk_version in sdk_versions:
        extracted_xpaths = extract_xpaths_by_sdk_version(sdk_version)
        xpaths.extend(extracted_xpaths)
    import_logger.info(f"Total nr. of extracted xpaths from SDK versions {sdk_versions}: {len(xpaths)}")
    return xpaths


def extract_unique_xpaths_by_list_of_sdk_versions(sdk_versions: List[str]) -> List[str]:
    xpaths: List[str] = extract_xpaths_by_list_of_sdk_versions(sdk_versions=sdk_versions)
    unique_xpaths: List[str] = list(set(xpaths))
    import_logger.info(f"Total nr. of unique xpaths from SDK versions {sdk_versions}: {len(unique_xpaths)}")
    return unique_xpaths
