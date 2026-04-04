# Endpoint Query Examples

This file contains sample HTTP queries and Swagger request bodies for the Support Ops environment endpoints.

Base URL:

```text
http://localhost:7860
```

Note:

- In PowerShell, prefer `curl.exe` instead of `curl`.
- Valid task IDs: `easy_password_reset`, `medium_duplicate_charge`, `hard_mixed_queue`

## 1. Health Check

```bash
curl.exe http://localhost:7860/health
```

Swagger request body:

```json
No body
```

Expected response:

```json
{"status":"ok"}
```

## 2. OpenAPI Schema

```bash
curl.exe http://localhost:7860/openapi.json
```

Swagger request body:

```json
No body
```

## 3. Reset Environment

Reset with default task:

```bash
curl.exe -X POST http://localhost:7860/reset ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

Swagger request body:

```json
{}
```

Reset with easy task:

```bash
curl.exe -X POST http://localhost:7860/reset ^
  -H "Content-Type: application/json" ^
  -d "{\"task_id\":\"easy_password_reset\"}"
```

Swagger request body:

```json
{
  "task_id": "easy_password_reset"
}
```

Reset with medium task:

```bash
curl.exe -X POST http://localhost:7860/reset ^
  -H "Content-Type: application/json" ^
  -d "{\"task_id\":\"medium_duplicate_charge\"}"
```

Swagger request body:

```json
{
  "task_id": "medium_duplicate_charge"
}
```

Reset with hard task:

```bash
curl.exe -X POST http://localhost:7860/reset ^
  -H "Content-Type: application/json" ^
  -d "{\"task_id\":\"hard_mixed_queue\"}"
```

Swagger request body:

```json
{
  "task_id": "hard_mixed_queue"
}
```

## 4. Get Current State

```bash
curl.exe http://localhost:7860/state
```

Swagger request body:

```json
No body
```

## 5. Step Endpoint Queries

### List tickets

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"list_tickets\"}"
```

Swagger request body:

```json
{
  "action_type": "list_tickets"
}
```

### Open a ticket

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"open_ticket\",\"ticket_id\":\"T-100\"}"
```

Swagger request body:

```json
{
  "action_type": "open_ticket",
  "ticket_id": "T-100"
}
```

### Classify a ticket

Valid categories:

- `account_access`
- `billing`
- `bug_report`
- `security`
- `shipping`

Valid priorities:

- `low`
- `normal`
- `high`
- `urgent`

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"classify_ticket\",\"ticket_id\":\"T-100\",\"category\":\"account_access\",\"priority\":\"normal\"}"
```

Swagger request body:

```json
{
  "action_type": "classify_ticket",
  "ticket_id": "T-100",
  "category": "account_access",
  "priority": "normal"
}
```

### Assign a ticket

Valid teams:

- `general_support`
- `identity_support`
- `billing_ops`
- `engineering`
- `security_response`

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"assign_ticket\",\"ticket_id\":\"T-100\",\"team\":\"identity_support\"}"
```

Swagger request body:

```json
{
  "action_type": "assign_ticket",
  "ticket_id": "T-100",
  "team": "identity_support"
}
```

### Reply to a ticket

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"reply_ticket\",\"ticket_id\":\"T-100\",\"message\":\"I have sent you a fresh password reset link so you can log in to your account again.\"}"
```

Swagger request body:

```json
{
  "action_type": "reply_ticket",
  "ticket_id": "T-100",
  "message": "I have sent you a fresh password reset link so you can log in to your account again."
}
```

### Update ticket status

Valid statuses:

- `open`
- `pending_customer`
- `escalated`
- `resolved`

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"set_status\",\"ticket_id\":\"T-100\",\"status\":\"resolved\"}"
```

Swagger request body:

```json
{
  "action_type": "set_status",
  "ticket_id": "T-100",
  "status": "resolved"
}
```

### Submit task

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"submit_task\",\"message\":\"done\"}"
```

Swagger request body:

```json
{
  "action_type": "submit_task",
  "message": "done"
}
```

### No-op

```bash
curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"noop\"}"
```

Swagger request body:

```json
{
  "action_type": "noop"
}
```

## 6. Full Easy Task Example

```bash
curl.exe -X POST http://localhost:7860/reset ^
  -H "Content-Type: application/json" ^
  -d "{\"task_id\":\"easy_password_reset\"}"

curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"open_ticket\",\"ticket_id\":\"T-100\"}"

curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"classify_ticket\",\"ticket_id\":\"T-100\",\"category\":\"account_access\",\"priority\":\"normal\"}"

curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"assign_ticket\",\"ticket_id\":\"T-100\",\"team\":\"identity_support\"}"

curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"reply_ticket\",\"ticket_id\":\"T-100\",\"message\":\"I have sent a fresh password reset link so you can log in to your account again.\"}"

curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"set_status\",\"ticket_id\":\"T-100\",\"status\":\"resolved\"}"

curl.exe -X POST http://localhost:7860/step ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"submit_task\",\"message\":\"done\"}"
```

## 7. Sample Ticket IDs by Task

- `easy_password_reset`: `T-100`
- `medium_duplicate_charge`: `T-200`, `T-201`
- `hard_mixed_queue`: `T-300`, `T-301`, `T-302`
