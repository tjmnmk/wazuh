from enum import Enum
from pathlib import Path
from typing import List

from pydantic import Field, ValidationInfo, field_validator
from wazuh.core.common import WAZUH_INDEXER_CA_BUNDLE
from wazuh.core.config.models.base import ValidateFilePathMixin, WazuhConfigBaseModel
from wazuh.core.exception import WazuhError
from wazuh.core.utils import assign_wazuh_ownership


class SSLProtocol(str, Enum):
    """Enum representing supported SSL/TLS protocols."""

    tls = 'TLS'
    tls_v1 = 'TLSv1'
    tls_v1_1 = 'TLSv1.1'
    tls_v1_2 = 'TLSv1.2'
    auto = 'auto'


class SSLConfig(WazuhConfigBaseModel, ValidateFilePathMixin):
    """Configuration for SSL settings specific to the server.

    Parameters
    ----------
    key : str
        The path to the SSL key file.
    cert : str
        The path to the SSL certificate file.
    ca : str
        The path to the CA certificate file.
    keyfile_password : str
        The password for the SSL key file. Default is an empty string.
    """

    key: str
    cert: str
    ca: str
    keyfile_password: str = ''

    @field_validator('key', 'cert', 'ca')
    @classmethod
    def validate_ssl_files(cls, path: str, info: ValidationInfo) -> str:
        """Validate that the SSL files exist.

        Parameters
        ----------
        path : str
            Path to the SSL certificate/key.
        info : ValidationInfo
            Validation context information.

        Raises
        ------
        ValueError
            Invalid SSL file path.

        Returns
        -------
        str
            SSL certificate/key path.
        """
        cls._validate_file_path(path, info.field_name)
        return path


class IndexerSSLConfig(WazuhConfigBaseModel, ValidateFilePathMixin):
    """Configuration for SSL settings specific to the indexer.

    Parameters
    ----------
    use_ssl : bool
        Whether to use SSL for the indexer. Default is False.
    key : str
        The path to the SSL key file. Default is an empty string.
    certificate : str
        The path to the SSL certificate file. Default is an empty string.
    certificate_authorities : List[str]
        List of paths to the CA certificate file. Default is a list containing one empty string.
    verify_certificates : bool
        Whether to verify the server TLS certificates or not. Default is True.
    """

    use_ssl: bool = False
    key: str = ''
    certificate: str = ''
    certificate_authorities: List[str] = Field(default=[''], min_length=1, exclude=True)
    verify_certificates: bool = True
    certificate_authorities_bundle: Path = WAZUH_INDEXER_CA_BUNDLE

    @field_validator('key', 'certificate')
    @classmethod
    def validate_ssl_files(cls, path: str, info: ValidationInfo) -> str:
        """Validate that the SSL files exist.

        Parameters
        ----------
        path : str
            Path to the SSL certificate/key.
        info : ValidationInfo
            Validation context information.

        Raises
        ------
        ValueError
            Invalid SSL file path.

        Returns
        -------
        str
            SSL certificate/key path.
        """
        if info.data['use_ssl']:
            cls._validate_file_path(path, info.field_name)
        return path

    @field_validator('certificate_authorities')
    @classmethod
    def validate_ca_files(cls, paths: List[str], info: ValidationInfo) -> List[str]:
        """Validate that the SSL certificate authorities files exist and create a bundle file.

        Parameters
        ----------
        paths : List[str]
            Paths to the SSL certificate authorities.
        info : ValidationInfo
            Validation context information.

        Raises
        ------
        ValueError
            Invalid SSL file path.

        Returns
        -------
        List[str]
            SSL Certificate Authorities paths.
        """
        if info.data['use_ssl']:
            for path in paths:
                cls._validate_file_path(path, info.field_name)

            cls.create_ca_bundle(paths)

        return paths

    @classmethod
    def create_ca_bundle(cls, file_paths: List[str]):
        """Merge certificate authorities files into a single bundle file.

        Parameters
        ----------
        file_paths : List[str]
            CA files paths.

        Raises
        ------
        WazuhError(1006)
            File does not exist or permission error.
        """
        try:
            with open(WAZUH_INDEXER_CA_BUNDLE, 'w') as bundle_file:
                for file_path in file_paths:
                    with open(file_path, 'r') as file:
                        bundle_file.write(file.read())

            assign_wazuh_ownership(WAZUH_INDEXER_CA_BUNDLE)
        except IOError as e:
            raise WazuhError(1006, str(e))


class APISSLConfig(WazuhConfigBaseModel, ValidateFilePathMixin):
    """Configuration for API SSL settings.

    Parameters
    ----------
    key : str
        The path to the SSL key file.
    cert : str
        The path to the SSL certificate file.
    use_ca : bool
        Whether to use a CA certificate. Default is False.
    ca : str
        The path to the CA certificate file. Default is an empty string.
    ssl_protocol : Literal["TLS", "TLSv1", "TLSv1.1", "TLSv1.2", "auto"]
        The SSL protocol to use. Default is "auto".
    ssl_ciphers : str
        The SSL ciphers to use. Default is an empty string.
    """

    key: str
    cert: str
    use_ca: bool = False
    ca: str = ''
    ssl_protocol: SSLProtocol = SSLProtocol.auto
    ssl_ciphers: str = ''

    @field_validator('ca')
    @classmethod
    def validate_ca_file(cls, path: str, info: ValidationInfo) -> str:
        """Validate that the certificate authority file exists.

        Parameters
        ----------
        path : str
            Path to the SSL certificate authority file.
        info : ValidationInfo
            Validation context information.

        Raises
        ------
        ValueError
            Invalid SSL file path.

        Returns
        -------
        str
            SSL certificate authority file path.
        """
        if info.data['use_ca']:
            cls._validate_file_path(path, info.field_name)

        return path
