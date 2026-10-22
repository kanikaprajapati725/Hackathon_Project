# Remaining work (70%)

Milestones follow the build plan in the reference document. Module numbers (M1–M12) match its section 6.
Each item is implemented in `../careflow_ai_complete/`.

## Phase 1–2 leftovers
- [ ] Users table with PBKDF2 password hashes; role permissions (intake / nurse / doctor / admin), with data minimisation per role (`auth.py`)
- [ ] Background worker so slow stages (ASR/OCR) don't block requests; fail-safe routing when the pipeline errors (`services.py`)

## Phase 3: multimodal and multilingual (M2, M3, M4)
- [ ] Voice notes:
    - [ ] decode with ffmpeg; faster-whisper (CPU int8)
    - [ ] language hint + domain prompt; auto-detect retry
    - [ ] per-segment confidence; cached transcripts
- [ ] Reports:
    - [ ] PDF text layer (pypdf); RapidOCR with bounding boxes
    - [ ] image quality score
    - [ ] lab parser (value/unit/range/critical status) + report header (name/age/sex)
- [ ] Lexicon: Hindi (Devanagari), Tamil, Bengali patterns; Indic durations (done in engine, needs lexicon)
- [ ] Translation to an English pivot, with coverage-based confidence (lexicon gloss); optional SLM translation

## Phase 4: safety and trust (M7, M9, M12)
- [ ] Prompt-injection scanner (EN/HI/Hinglish/TA/BN) on all inputs; quarantine; cannot change priority
- [ ] Hidden-text detection in PDFs (text layer vs rendered OCR)
- [ ] Conflict checks:
    - [ ] history vs labs (e.g. "no diabetes" vs HbA1c 9.1)
    - [ ] duration mismatches across sources
    - [ ] report name/sex/age mismatch
- [ ] Quality flags: unreadable report, low OCR/ASR confidence, uncertain translation
- [ ] Missing-information checklists per complaint (OPQRST/SOCRATES style)
- [ ] Patient kiosk:
    - [ ] language choice; granular, versioned consent
    - [ ] voice recording + uploads
    - [ ] case code + access code
- [ ] Withdraw consent / erase data (files + records, audit tombstone); delete recordings when there is no "store voice" consent
- [ ] Hash-chained audit log with verification

## Phase 5: clinician UX and innovation (M10, M11)
- [ ] Follow-up questions ranked by impact, in the patient's language; closed loop (answers re-run the pipeline)
- [ ] Draft triage note (template + no-diagnosis filter); edit, diff vs AI draft, approve & sign (doctor only); override reasons
- [ ] Priority override: nurses raise only, doctors lower with a reason
- [ ] Flag review (acknowledge / resolve with comment)
- [ ] Evidence viewer: OCR box overlay on the image, audio cued to the segment, PDF line highlight
- [ ] Live P1/P2 alert banner + sound; waiting-time ageing in the queue
- [ ] FHIR R4 Bundle export; analytics (overrides, review time, flags)

## Phase 6: evaluate, benchmark, pitch
- [ ] Full evaluation script (priority, urgent recall, flag precision/recall, injection detection, latency)
- [ ] Optional SLM (<20B, OpenAI-compatible endpoint): quoted-signal extraction (catches CF-013), raise-only, hallucinated quotes rejected
- [ ] Tests: pipeline, API/RBAC, audit tampering, SLM guardrails
- [ ] README, demo script, backup demo video, deck
