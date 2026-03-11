# Resource Config

## Basic Structure

```json
{
  "<resource-id>": {
    <specification>
  }
}
```

## Example

```json
{
  "usr-local-linker": {
    "lib": ["lib/foo"],
    "bin": ["bin/foo"],
    "etc": ["etc/foo"]
  }
}
```

## Key Concepts

- **Resource ID**: Unique identifier (e.g., `usr-local-linker`) for the system resource
- **Specification**: Configuration details for files/paths to manage

See available workers documentation for specific resource IDs and their specifications.
