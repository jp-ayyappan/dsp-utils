# Virtru DSP gRPC API Postman Collection

Comprehensive Postman collection for interacting with Virtru Data Security Platform gRPC endpoints.

## Services Included

### 1. Tagging PDP Service (v2)
Content analysis and tag generation service.

**Endpoints:**
- `Tag` - Process content items to produce tags
- `TagPerContentItem` - Get tags per individual content item
- `TagStream` - Stream content for tagging (not in REST format)
- `ProcessTags` - Process existing tags

**Features:**
- Content extraction from multiple formats (text, binary, URLs)
- Data attribute tag generation
- Assertion generation (STANAG 4774, custom formats)
- Encrypted search token generation
- Provenance tracking

### 2. Policy Artifact Service (v1)
Policy import/export and artifact management.

**Endpoints:**
- `CreateImportArtifacts` - Import policy (YAML or OCI format)
- `CreateExportArtifacts` - Export policy (YAML or OCI format)
- `CreateTrustedArtifactProvider` - Register trusted providers

**Features:**
- Unbundled YAML format support
- OCI artifact bundle support
- Signature verification
- Trusted provider management
- Namespace isolation

### 3. NanoTDF Rewrap Service (v1)
Key management for NanoTDF format.

**Endpoints:**
- `Rewrap` - Rewrap NanoTDF headers to get KAS-wrapped keys

**Features:**
- Batch rewrap operations
- X25519 key agreement
- Per-item status tracking
- Signed Request Token (SRT) authentication

## Setup Instructions

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

### 2. Configure Environment Variables

The collection uses these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | gRPC server address (**include protocol**) | `http://localhost:8080` or `https://ohalo.platform.partner.dsp-prod-green.virtru.com:443` |
| `auth_token` | Bearer token for authentication | Your OAuth token |
| `use_tls` | Whether to use TLS | `true` for production, `false` for local |

**⚠️ Important:** The `base_url` must include the protocol (`http://` or `https://`). Without it, Postman will default to `http://` which will cause connection errors on TLS endpoints.

**Set Variables:**
1. Click on the collection
2. Go to "Variables" tab
3. Set "Current Value" for each variable

### 3. Authentication

The collection uses Bearer token authentication by default.

**Get an OAuth Token:**
```bash
# Using your runGRPCUI.sh script
cd ~/dev/personal/dsp-utils/grpcui
./runGRPCUI.sh local-dsp.virtru.com --insecure -a 8443 -p 8080

# The script fetches a token - you can extract it for Postman use
```

**Or use the Keycloak admin tool:**
```bash
cd ~/dev/personal/dsp-utils/keycloak
source venv/bin/activate

# Get token programmatically (you'll need to add a get-token command)
```

## Usage Examples

### Example 1: Tag Text Content

**Request:** Tagging PDP Service → Tag Content Items

```json
{
  "items": [
    {
      "desc": {
        "type": "text.plain",
        "id": "doc-1",
        "name": "sample.txt"
      },
      "text": "This is a SECRET document about Project Alpha."
    }
  ],
  "options": {
    "mode": "TAG_EXTRACT_AND_PROCESS"
  }
}
```

**Response:**
```json
{
  "tags": [
    {
      "metadata": {
        "id": "tag-1",
        "provenance": { ... }
      },
      "data_attribute": {
        "fqn": "https://example.com/attr/Classification/Secret"
      }
    }
  ],
  "events": []
}
```

### Example 2: Export Policy

**Request:** Policy Artifact Service → Export Policy (Unbundled)

```json
{
  "namespace": "https://example.com/attr",
  "no_bundle": true,
  "with_obligations": true
}
```

**Response:**
```json
{
  "policy_unbundled": {
    "policy": "<base64-encoded-yaml>"
  }
}
```

Decode the base64 to get human-readable YAML policy.

### Example 3: Process Existing Tags

**Request:** Tagging PDP Service → Process Tags

```json
{
  "tags": [
    {
      "metadata": { "id": "tag-1" },
      "data_attribute": {
        "fqn": "https://example.com/attr/Classification/Secret"
      }
    }
  ],
  "options": {
    "mode": "PROCESS",
    "assertion_options": [
      {
        "assertion_type": "stanag_4774"
      }
    ]
  }
}
```

Generates STANAG 4774 assertions from data attributes.

## Common Workflows

### Workflow 1: Content Classification Pipeline

1. **Tag Content**
   - Use `Tag Content Items` with your document
   - Set mode to `TAG_EXTRACT_AND_PROCESS`

2. **Review Tags**
   - Examine returned tags and provenance
   - Check for any processing events/errors

3. **Generate Assertions**
   - Use `Process Tags` with the returned tags
   - Request specific assertion types (STANAG, etc.)

### Workflow 2: Policy Management

1. **Export Current Policy**
   - Use `Export Policy (Unbundled)`
   - Decode base64 and review YAML

2. **Modify Policy**
   - Edit the YAML (add attributes, values, mappings)
   - Base64 encode the modified YAML

3. **Import Updated Policy**
   - Use `Import Policy (Unbundled)`
   - Verify import success

### Workflow 3: NanoTDF Decryption

1. **Prepare Signed Request Token**
   - Create JWT with `requestBody` claim
   - Include client public key and NanoTDF headers

2. **Rewrap Keys**
   - Call `Rewrap NanoTDF Headers`
   - Receive KAS-wrapped keys

3. **Decrypt Content**
   - Use session public key for key agreement
   - Unwrap keys and decrypt NanoTDF payload

## Testing Tips

### Local Development

**Start DSP services:**
```bash
# Assuming you're using docker-compose
cd /path/to/dsp
docker-compose up -d

# Or individual services
./tagging-pdp-service --port 8080
```

**Configure Postman:**
- Set `base_url` to `localhost:8080`
- Set `use_tls` to `false`
- Leave `auth_token` empty for local testing (if auth is disabled)

### Testing with runGRPCUI.sh

The `runGRPCUI.sh` script handles authentication automatically. Use it to:
1. Verify gRPC services are accessible
2. Explore service methods interactively
3. Get sample requests/responses

```bash
cd ~/dev/personal/dsp-utils/grpcui
./runGRPCUI.sh local-dsp.virtru.com --insecure -a 8443 -p 8080
```

## Troubleshooting

### Socket Hang Up

**Problem:** `Error: socket hang up`

**Solutions:**
- **Most common:** Missing protocol in `base_url` - add `https://` or `http://` prefix
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
- Check token hasn't expired
- Ensure user has required permissions

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
- Set `use_tls` to `false` for local dev
- For production, import CA certificate
- Check server certificate validity

## Proto Files

The collection is based on these proto definitions:

```
data-security-platform/
├── sdk/tagging/pdp/v2/tagging.proto
├── sdk/policyimportexport/v1/policy_import_export.proto
└── sdk/kas/nanotdf/v1/nanotdf_rewrap.proto
```

**To regenerate or modify:**
1. Update proto files in DSP repository
2. Regenerate collection (or update manually)
3. Test all endpoints

## Additional Resources

- **DSP Documentation:** [Internal link]
- **gRPC Documentation:** https://grpc.io/docs/
- **Postman gRPC Support:** https://learning.postman.com/docs/sending-requests/grpc/grpc-request-interface/
- **Proto3 Language Guide:** https://protobuf.dev/programming-guides/proto3/

## Contributing

To add new endpoints or update existing ones:

1. Identify the proto file and service definition
2. Add request to appropriate folder in collection
3. Include example request body
4. Document expected response
5. Update this README with usage examples

## Version History

- **v1.0** (2026-02-09) - Initial collection
  - Tagging PDP Service (v2)
  - Policy Artifact Service (v1)
  - NanoTDF Rewrap Service (v1)
  - Health checks
