# ClaimGuard sample texts

Use these **optionally** via the UI **Load sample** button, or paste/upload your own files.

- `source_report.txt` — retrieved context / earnings excerpt
- `generated_summary.txt` — answer with planted hallucinations
- `verification_pair.json` — `{ query, source_text, generated_text }` for API/`curl`

Custom input is the default: the Verify screen starts **empty**.

```bash
curl -s -X POST http://127.0.0.1:8002/api/verify \
  -H 'Content-Type: application/json' \
  -d @verification_pair.json
```
