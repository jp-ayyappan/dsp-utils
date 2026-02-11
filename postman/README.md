# Virtru DSP gRPC API Postman Collection

Comprehensive Postman collection for interacting with Virtru Data Security Platform gRPC endpoints via gRPC-gateway.

## Quick Start

### 1. Import Collection

**Option A: Import via Postman UI**
1. Open Postman
2. Click "Import" button
3. Select `DSP-gRPC-APIs.postman_collection.json`
4. Click "Import"

**Option B: Import via URL**
```bash
# If you've pushed to GitHub
# Collections → Import → Link → Paste GitHub raw URL
```

### 2. Configure Variables

Click on the collection → **Variables** tab and set these values:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `base_url` | gRPC server address (**include protocol**) | `https://ohalo.platform.partner.dsp-prod-green.virtru.com:443` | ✅ Yes |
| `keycloak_url` | Keycloak base URL | `https://keycloak-ohalo.dsp-prod-green.virtru.com` | ✅ Yes |
| `keycloak_realm` | Keycloak realm name | `dsp-ohalo` | ✅ Yes |
| `keycloak_client_id` | OAuth public client ID | `dsp-outlook-auth` | ✅ Yes |
| `keycloak_username` | Your username | `your-username` | ✅ Yes |
| `keycloak_password` | Your password | `your-password` | ✅ Yes |
| `auth_token` | Access token (auto-populated) | *Auto-set by "Get Access Token"* | ⚙️ Auto |
| `refresh_token` | Refresh token (auto-populated) | *Auto-set by "Get Access Token"* | ⚙️ Auto |
| `token_expires_at` | Token expiry timestamp (auto-populated) | *Auto-set by "Get Access Token"* | ⚙️ Auto |

**⚠️ Important:**
- The `base_url` **must include the protocol** (`http://` or `https://`). Without it, Postman defaults to `http://` which causes connection errors.
- Only set the first 6 variables manually. The auth tokens auto-populate when you authenticate.

### 3. Authenticate

1. Navigate to **Authentication** folder in the collection
2. Run **"Get Access Token (Password Grant)"**
3. Verify the response populates: `auth_token`, `refresh_token`, `token_expires_at`

**That's it!** All subsequent requests will automatically:
- Use your `auth_token` for authentication
- Refresh the token when it expires (via pre-request script)
- No manual token management needed

### 4. Make Your First Request

Try **Policy Service → Namespaces → List Namespaces** to verify everything works!

## Usage Examples

### Example 1: List Policy Namespaces

**Request:** Policy Service → Namespaces → List Namespaces

```json
{
  "state": "ACTIVE"
}
```

**Response:**
```json
{
  "namespaces": [
    {
      "id": "namespace-uuid",
      "name": "https://example.com/attr",
      "fqn": "https://example.com/attr"
    }
  ]
}
```

### Example 2: Create an Attribute

**Request:** Policy Service → Attributes → Create Attribute

```json
{
  "namespace_id": "namespace-uuid",
  "name": "Classification",
  "rule": "HIERARCHY",
  "values": ["Unclassified", "Confidential", "Secret", "TopSecret"]
}
```

### Example 3: Get Authorization Decisions

**Request:** Authorization Service → Get Decisions

```json
{
  "decision_requests": [
    {
      "actions": [{"standard": "STANDARD_ACTION_TRANSMIT"}],
      "entity_chains": [{
        "entities": [{
          "id": "e1",
          "entity_type": {"name": "ResourceAttributeEntity"},
          "attribute": "https://example.com/attr/Classification/Secret"
        }]
      }],
      "subject_sets": [{
        "subject_attributes": [{
          "attribute": "https://example.com/attr/Clearance/Secret"
        }]
      }]
    }
  ]
}
```

## Common Workflows

### Workflow 1: Policy Setup

1. **Create Namespace** → Policy Service → Namespaces → Create Namespace
2. **Create Attribute** → Policy Service → Attributes → Create Attribute
3. **Create Values** → Policy Service → Attributes → Create Attribute Value
4. **List Everything** → Verify your policy structure

### Workflow 2: Content Classification

1. **Tag Content** → Tagging PDP Service → Tag Content Items
2. **Review Tags** → Check returned data attributes
3. **Process Tags** → Generate assertions (STANAG 4774, etc.)

### Workflow 3: Authorization Testing

1. **Setup Policy** → Create attributes and values
2. **Create Subject Mappings** → Map users to attributes
3. **Test Decisions** → Authorization Service → Get Decisions

## Troubleshooting

### Socket Hang Up

**Problem:** `Error: socket hang up`

**Solutions:**
- **Most common:** Missing protocol in `base_url`
  - ❌ Wrong: `ohalo.platform.partner.dsp-prod-green.virtru.com:443`
  - ✅ Correct: `https://ohalo.platform.partner.dsp-prod-green.virtru.com:443`
- Verify you have a valid `auth_token` (run "Get Access Token" first)
- Check if gRPC-gateway is enabled on your DSP instance

### Connection Refused

**Problem:** `connect ECONNREFUSED`

**Solutions:**
- Verify gRPC server is running
- Check `base_url` matches server address
- Ensure firewall allows connections

### Authentication Failed

**Problem:** `UNAUTHENTICATED` or `PERMISSION_DENIED`

**Solutions:**
- Verify `auth_token` is set and valid
- Check token hasn't expired (should auto-refresh)
- Ensure user has required permissions in Keycloak
- Try running "Get Access Token" again

### Invalid Request

**Problem:** `INVALID_ARGUMENT` errors

**Solutions:**
- Check request body matches proto schema
- Ensure required fields are present
- Validate field types (string vs bytes)
- Use base64 encoding for binary data

### TLS/SSL Errors

**Problem:** Certificate validation errors

**Solutions:**
- For local dev: Set `base_url` to `http://localhost:8080`
- For production with self-signed certs: Disable SSL verification in Postman settings
- Check server certificate validity

## Services Included

**Total: 94 endpoints across 11 services** (HTTP/gRPC-gateway accessible)

### 1. Authentication (3 endpoints)
- Get Access Token (Password Grant, Client Credentials)
- Refresh Token

### 2. Policy Service (67 endpoints)

**Namespaces (11):** Create, List, Get, Update, Deactivate, AssignPublicKey, RemovePublicKey, AssignCertificate, RemoveCertificate, Assign/RemoveKAS (deprecated)

**Attributes (14):** Create, List, Get, Update, Deactivate, GetByFqns, AssignPublicKey (attribute/value), RemovePublicKey (attribute/value), Assign/RemoveKAS (deprecated)

**Attribute Values (8):** Create (with examples for Secret/TopSecret/Confidential), List, Get, Update, Deactivate

**Subject Mappings (8):** Match, Create (with/without new subjects), List, Get, Update, Delete, DeleteAllUnmapped

**Resource Mappings (10):** CreateGroup, ListGroups, GetGroup, UpdateGroup, DeleteGroup, Create, List, Get, Update, Delete

**Subject Condition Sets (5):** Create, List, Get, Update, Delete

**Key Access Servers (15):** Create (remote/local key), List, Get, Update, Delete, CreateKey, GetKey, ListKeys, UpdateKey, RotateKey, SetBaseKey, GetBaseKey, ListKeyMappings

### 3. KAS Service (3 endpoints)
- Rewrap
- PublicKey (POST)
- LegacyPublicKey

### 4. WellKnown Service (1 endpoint)
- GetWellKnownConfiguration

### 5. Authorization Service (4 endpoints)
- GetDecisions (single/multiple actions)
- GetDecisionsByToken
- GetEntitlements

### 6. Entity Resolution Service (2 endpoints)
- CreateEntityChainFromJwt
- ResolveEntities

### 7. Shared Service v1 (3 endpoints)
- GetMyEntitlements
- TransformToICTDF
- TransformToZTDF

### 8. Tagging PDP Service (4 endpoints)
- Tag Content Items
- Tag Per Content Item
- Process Tags
- TagStream (streaming RPC)

### 9. Policy Artifact Service (2 endpoints)
- Import Policy (Unbundled)
- Export Policy (Unbundled)

### 10. NanoTDF Rewrap Service (1 endpoint)
- Rewrap NanoTDF Headers

---

**Note:** Additional services are available via pure gRPC (grpcurl) but may not have HTTP/JSON endpoints. Run `/postman/test_http_support.sh` to test HTTP support for other services.

## Proto Files

The collection is based on these proto definitions:

**OpenTDF Platform:**
```
opentdf/platform/service/
├── policy/namespaces/namespaces.proto
├── policy/attributes/attributes.proto
├── policy/subjectmapping/subject_mapping.proto
├── policy/resourcemapping/resource_mapping.proto
├── policy/kasregistry/key_access_server_registry.proto
├── kas/kas.proto
├── authorization/authorization.proto
└── wellknownconfiguration/wellknown_configuration.proto
```

**DSP Services:**
```
data-security-platform/sdk/
├── tagging/pdp/v2/tagging.proto
├── policyimportexport/v1/policy_import_export.proto
└── kas/nanotdf/v1/nanotdf_rewrap.proto
```

## Additional Resources

### Related Tools

This repository includes other utilities for DSP infrastructure management:

- **[Keycloak Admin Tool](../keycloak/)** - CLI for managing Keycloak clients, users, and attributes
- **[gRPC UI Scripts](../grpcui/)** - Interactive gRPC UI for service exploration

### Documentation

- **gRPC Documentation:** https://grpc.io/docs/
- **Postman gRPC Support:** https://learning.postman.com/docs/sending-requests/grpc/grpc-request-interface/
- **Proto3 Language Guide:** https://protobuf.dev/programming-guides/proto3/
- **OpenTDF Platform:** https://github.com/opentdf/platform

## Contributing

To add new endpoints or update existing ones:

1. Identify the proto file and service definition
2. Add request to appropriate folder in collection
3. Include example request body with inline comments
4. Document expected response format
5. Update this README with usage examples

## Version History

- **v1.1** (2026-02-10) - Fixed gRPC-gateway URLs and documentation
  - Corrected all service paths to use gRPC-gateway format
  - Added complete variable documentation
  - Clarified authentication flow
  - Improved troubleshooting guide

- **v1.0** (2026-02-09) - Initial collection
  - OpenTDF Platform services (Policy, KAS, Authorization, WellKnown)
  - DSP services (Tagging PDP, Policy Artifact, NanoTDF Rewrap)
  - Keycloak OAuth with auto-refresh
