"""Globus OAuth tools.
ProxyStore provides the `proxystore-globus-auth` CLI tool to give consent
to the ProxyStore Globus Application.
```bash
# basic authentication
proxystore-globus-auth
# delete old tokens
proxystore-globus-auth --delete
# give consent for specific collections
proxystore-globus-auth --collections COLLECTION_UUID COLLECTION_UUID ...
# specify additional scopes
proxystore-globus-auth --scopes SCOPE SCOPE ...
```
Based on [Parsl's implementation](https://github.com/Parsl/parsl/blob/1.2.0/parsl/data_provider/globus.py)
and the [Globus examples](https://github.com/globus/native-app-examples/blob/064569e103f7d328f3d6c4b1242234011c81dffb/example_copy_paste_refresh_token.py).
"""  # noqa: E501
from __future__ import annotations

import argparse
import functools
import json
import os
from typing import Any
from typing import Iterable
from typing import Sequence

import globus_sdk

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore

# Registered Globus Client ID for Ocelot
_APPLICATION_ID = '1ed32e7d-3eef-4fc1-a151-4671326f59d4'
# https://docs.globus.org/globus-connect-server/migrating-to-v5.4/application-migration/#activation_is_replaced_by_consent  # noqa: E501
_COLLECTION_CONSENT = (
    '*https://auth.globus.org/scopes/{COLLECTION}/data_access'
)
_REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
_TOKENS_FILE = 'globus-tokens.json'


home_dir_ = "~"

class GlobusAuthFileError(Exception):
    """Exception raised if the Globus Auth token file cannot be read."""

    pass


def load_tokens_from_file(filepath: str) -> dict[str, dict[str, Any]]:
    """Load a set of saved tokens."""
    with open(filepath) as f:
        tokens = json.load(f)

    return tokens


def save_tokens_to_file(
    filepath: str,
    tokens: globus_sdk.OAuthTokenResponse,
) -> None:
    """Save a set of tokens for later use."""
    with open(filepath, 'w') as f:
        json.dump(tokens.by_resource_server, f, indent=4)


def authenticate(
    client_id: str,
    requested_scopes: Iterable[str] | None = None,
) -> globus_sdk.OAuthTokenResponse:
    """Perform Native App auth flow."""
    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    print("requested scopes: ", requested_scopes)
    client.oauth2_start_flow(
        refresh_tokens=True,
        requested_scopes=requested_scopes,
    )

    url = client.oauth2_get_authorize_url()
    print(f'Please visit the following url to authenticate:\n{url}')

    auth_code = input('Enter the auth code: ').strip()
    return client.oauth2_exchange_code_for_tokens(auth_code)

def authenticate_gui(
    w: QDialog,
    client_id:str,
    requested_scopes: Iterable[str] | None = None,
    session_domains: Iterable[str] | None = None
) -> globus_sdk.OAuthTokenResponse:
    """Perform Native App auth flow."""
    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    print("requested scopes: ", requested_scopes)
    client.oauth2_start_flow(
        refresh_tokens=True,
        requested_scopes=requested_scopes,
    )

    url = client.oauth2_get_authorize_url(session_required_single_domain=session_domains)
    print(f'Please visit the following url to authenticate:\n{url}')
    auth_code, ok = QInputDialog.getText(w, "Globus Authenticate", f'Please paste the authenticate code in')
    if ok:
        print("Got authenticate code, proceed to exchange code for tokens")
    
    # auth_code = input('Enter the auth code: ').strip()
    return client.oauth2_exchange_code_for_tokens(auth_code)


def get_authorizer(
    client_id: str,
    tokens_file: str,
) -> globus_sdk.RefreshTokenAuthorizer:
    """Get an authorizer for the Globus SDK.
    Raises:
        GlobusAuthFileError: If `tokens_file` cannot be parsed.
    """
    try:
        tokens = load_tokens_from_file(tokens_file)
    except OSError as e:
        raise GlobusAuthFileError(
            f'Error loading tokens from {tokens_file}: {e}.',
        ) from e

    transfer_tokens = tokens['transfer.api.globus.org']
    auth_client = globus_sdk.NativeAppAuthClient(client_id=client_id)

    return globus_sdk.RefreshTokenAuthorizer(
        transfer_tokens['refresh_token'],
        auth_client,
        access_token=transfer_tokens['access_token'],
        expires_at=transfer_tokens['expires_at_seconds'],
        on_refresh=functools.partial(save_tokens_to_file, tokens_file),
    )



def _get_proxystore_scopes(
    collections: Iterable[str] | None = None,
    additional_scopes: Iterable[str] | None = None,
) -> list[str]:
    scopes = ['openid']

    transfer_scope = 'urn:globus:auth:scope:transfer.api.globus.org:all'
    if collections is not None:
        data_access = [
            _COLLECTION_CONSENT.format(COLLECTION=c) for c in collections
        ]
        transfer_scope = f'{transfer_scope}[{" ".join(data_access)}]'
    scopes.append(transfer_scope)
    print("scopes: ", scopes)
    if additional_scopes is not None:
        scopes.extend(additional_scopes)

    return scopes

def get_one_time_authorizer(
    client_id: str,
    collections: list[str],
) -> globus_sdk.AccessTokenAuthorizer:
    scopes = _get_proxystore_scopes(collections)
    tokens = authenticate(client_id=client_id, requested_scopes=scopes)
    transfer_tokens = tokens.by_resource_server["transfer.api.globus.org"]
    return globus_sdk.AccessTokenAuthorizer(transfer_tokens["access_token"])


def proxystore_authenticate(
    w: QDialog,
    client_id: str,
    proxystore_dir: str,
    token_file_name: str,
    collections: list[str] | None = None,
    additional_scopes: list[str] | None = None,
    session_domains : Iterable[str] | None = None
) -> None:
    """Perform auth flow for ProxyStore native app."""
    tokens_file = os.path.join(proxystore_dir, token_file_name)
    os.makedirs(proxystore_dir, exist_ok=True)

    scopes = _get_proxystore_scopes(collections, additional_scopes)

    tokens = authenticate_gui(
        w=w,
        client_id=client_id,
        requested_scopes=scopes,
        session_domains=session_domains
    )
    save_tokens_to_file(tokens_file, tokens)


def get_proxystore_authorizer(
    client_id: str,
    token_file_name: str,
    cwd_dir: str,
) -> globus_sdk.RefreshTokenAuthorizer:
    """Get an authorizer for the Globus native app."""
    tokens_file = os.path.join(cwd_dir, token_file_name)

    return get_authorizer(
        client_id=client_id,
        tokens_file=tokens_file,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Perform Globus authentication.
    This function is the entrypoint for the `proxystore-globus-auth` CLI tool.
    """
    parser = argparse.ArgumentParser(
        'ProxyStore Globus Auth Tool',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--collections',
        nargs='+',
        help='Collection UUIDs to request scopes for.',
    )
    parser.add_argument(
        '--scopes',
        nargs='+',
        help='Additional scopes to request.',
    )
    parser.add_argument(
        '--domains',
        nargs='+',
        help="The special session domains required for the authentication.",
    )

    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete existing authentication tokens.',
    )
    args = parser.parse_args(argv)

    if args.delete:
        tokens_file = os.path.join(home_dir_, _TOKENS_FILE)
        if os.path.exists(tokens_file):
            os.remove(tokens_file)
            print('Deleted tokens file.')
            return 0
        else:
            print('No tokens file found.')
            return 1

    try:
        get_proxystore_authorizer(_APPLICATION_ID, _TOKENS_FILE, home_dir_)
    except GlobusAuthFileError:
        print(
            'Performing authentication for the ProxyStore Globus Native app.',
        )
        proxystore_authenticate(
            collections=args.collections,
            additional_scopes=args.scopes,
            session_domains=args.domains)
        get_proxystore_authorizer(_APPLICATION_ID, _TOKENS_FILE, home_dir_)
        print('Globus authorization complete.')
        return 0
    else:
        print(
            'Globus authorization is already completed. To re-authenticate, '
            'delete your tokens (proxystore-globus-auth --delete) and try '
            'again.',
        )
        return 1


if __name__ == '__main__':
    raise SystemExit(main())