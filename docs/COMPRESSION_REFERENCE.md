# Compression Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## SmartContextCompressor (`lingflow/compression/smart_compressor.py`)

tiktoken-based intelligent context compression with:

1. **TokenEstimator** — Precise token counting via tiktoken (cl100k_base encoding), falls back to character estimation (ratio 0.25-0.28)
2. **MessageScorer** — Multi-dimensional scoring: role priority (system > user > assistant > tool), content importance (critical keywords), recency (exponential decay), length adjustment
3. **TieredCompressionStrategy** — Five tiers: KEEP_ALL, KEEP_IMPORTANT, COMPRESS, SUMMARIZE, DROP
4. **ConversationSummarizer** — Generates summaries preserving tasks, decisions, and errors

## Compression Modes

| Mode | Target Ratio | Message Compress Ratio |
|------|-------------|----------------------|
| normal | 50% | 70% |
| aggressive | 30% | 50% |
| emergency | 20% | 30% |

## Thresholds (default)

- **Warning**: 75% of max_tokens
- **Compress**: 85% of max_tokens
- **Critical**: 95% of max_tokens (emergency compression)

## Context Compression Notes

- Default max_tokens: 180,000
- System messages always preserved
- `requirements`, `constraints`, `critical_requirements` sections preserved
