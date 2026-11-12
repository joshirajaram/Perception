# Authentication

Detailed customer sign-in instructions must be checked against the public API
documentation before the first runnable contribution is published.

Keep common endpoint and authentication instructions in shared docs. Each contribution should state only:

- Which API/authentication approach it uses, linking to the shared guide.
- Its required permissions and additional prerequisites.
- Any contribution-specific credential setup or cleanup.

Do not store access tokens or client secrets in source control. Use the identity
mechanism documented for the specific contribution, requesting only required access.
