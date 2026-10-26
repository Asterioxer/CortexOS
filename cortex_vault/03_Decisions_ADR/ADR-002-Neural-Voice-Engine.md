---
title: "ADR-002: Neural Voice Engine & Sub-10ms Barge-In"
type: "adr"
tags:
  - cortex/adr
  - cortex/voice
status: "accepted"
date: "2026-10-26"
---

# ADR-002: Neural Voice Engine & Sub-10ms Barge-In

## Context
Voice output previously suffered from audio echo (repetitive double speech) and overlapping voices when multiple messages or persona switches occurred concurrently.

## Decision
1. Implemented a client-side monotonic speech epoch mutex (`activeSpeechEpoch`) in JavaScript. Any new speech call increments the epoch and pauses preceding audio elements immediately.
2. Server-side single-flight lock in `CortexVoiceEngine` with Kokoro / Edge-TTS neural speech synthesis.
3. Sub-10ms instant barge-in killswitch button (`HALT`) allowing immediate operator override.

## Consequences
Clean, isolated baritone/companion voice output without echo or concurrent speaker overlap.
