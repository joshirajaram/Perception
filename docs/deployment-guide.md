# Deployment guidance

Each contribution owns its deployment instructions; there is no universal deploy
command in this scaffold.

Document required resources and permissions, configurable inputs, costs, expected
changes, execution steps, verification, and cleanup. Use placeholders rather than
real tenants, subscriptions, secrets, or customer identifiers.

For Azure-deployable contributions, include reviewed deployment artifacts such as
`azuredeploy.json`. Add a deployment link only after its public artifact location
is finalized and the deployment has been tested. Scripts, dashboards, and plugins
may instead require setup or import instructions.

Prefer an authorized test environment for initial validation. Do not run live
deployments automatically from external pull requests.
