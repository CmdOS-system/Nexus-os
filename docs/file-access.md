# Nexus Agent R1 file access

Nexus Agent must not receive unrestricted access to a user's home directory.

R1 introduces an application-level one-shot file grant. A trusted UI/portal layer obtains a file selected by the user and gives FileGrantStore the resulting absolute path. The model receives only an opaque token, not authority to choose a new path.

The grant is consumed on first read, accepts regular files only, is limited to UTF-8 text and enforces a maximum size of 1 MB.

This is not yet the desktop portal implementation. Production integration should use the desktop document/file chooser portal or an equivalent user-mediated mechanism, and the application-level grant remains a second authorization boundary.

Symlink/race hardening and descriptor-based reads are required before treating this prototype as production-safe.
