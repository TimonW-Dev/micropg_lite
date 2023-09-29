# micropg_lite changelog
Time format: DD.MM.YYYY
## micropg_lite-V1.0.0 (6.6.2023)
First version of micropg_lite.

### micropg_lite-V1.1.0 (29.9.2023)
- `CHANGELOG.md` added
- `VERSION` file removed

## micropg_lite-V2.0.0 (29.9.2023)
micropg_lite-V2.0.0 uses way less RAM and enables the users to use more of their own code.

**Changes**:
- Removed a lot of unused variables
- Removed specific errormessages for more efficency
- `LICENSE` file updated (own MIT-Lincense added)
- `README.md` changes
- Removed the `getServerData.py`
    - Removed "self.tz_name" variable (was unused)
    - Removed "self.server_version" variable (it didn't have any function)
    - Added random generation for "client_nonce"
- `memory-test.py` script added for testing in the examples/ directory
- `docker-containers-setup.sh` script added in the examples/ directory
- Code formatting

Thanks to [Betafloof](https://github.com/BetaFloof) for the support ([Pull request](https://github.com/TimonW-Dev/micropg_lite/pull/1))