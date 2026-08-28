# PROJECT BASIL — Meeting Processing

**Canonical Operator Workflow, System Boundary and Automation Plan**  
**Version:** 0.4  
**Date:** 25 August 2026  
**Status:** CURRENT WORKING AUTHORITY — use for routine meeting processing until replaced by v1.0.

## Repository provenance

This Markdown representation was migrated on 28 August 2026 from the current native Google Doc `BASIL Meeting Processing - Canonical Operator Workflow v0.4 - 2026-08-25` (Drive ID `1w5cnV_bBCgM4rgRPwHSl8fKRHkaWMUal5oQt7wbOzc4`). It preserves the source meaning and sequence while converting Google Docs table layout into Markdown. It does not promote later experimental work into the workflow.

## Controlling purpose

Consolidates the actual operator process, the two empirical ARC meeting runs, the current diarisation engine and BASIL evidence/intelligence boundaries into one place.

## User-facing target

Record the meeting, place it in Drive, run the standard transcription and local speaker-preparation steps, then give BASIL the meeting folder. Those local steps should progressively collapse into one launcher and eventually disappear behind automation.

## Operating principle

Preserve the source. Recover words and speaker activity. Reconcile uncertainty. Consolidate evidence. Derive intelligence. Promote valid actions. Retain learning.

## 1. Routine operator workflow: the version to remember

For an ordinary meeting, the human process should be six actions. Everything else belongs beneath the system boundary, not in the user's memory.

| Step | Action | What it means |
| --- | --- | --- |
| 1 | RECORD | Record the meeting on the phone. Preserve the original M4A/MP4 unchanged. |
| 2 | UPLOAD | Place the recording in its Google Drive meeting folder. |
| 3 | TRANSCRIBE | Open the Google Colab notebook currently used for transcription, `Copy of Whisper_YouTube` / `YouTube videos transcribed with OpenAI's Whisper`, point it at the meeting folder and run the notebook. The native JSON, TSV, SRT, VTT and TXT outputs are evidence and stay unchanged. |
| 4 | PREPARE SPEAKER EVIDENCE | Run the current local diarisation process using `diarise_meetings_v2.py` / pyannote Community-1. Use the known exact speaker count when genuinely known. The script should use the persistent local model cache and should not require rediscovering scripts or downloading models again. |
| 5 | PROCESS WITH BASIL | Give BASIL the Google Drive meeting folder and instruct: `Process this meeting using BASIL Meeting Intelligence.` BASIL discovers and reuses the recording, transcript and diarisation evidence, adds missing acoustic/linguistic evidence, reconciles speakers, asks only high-value calibration questions and finalises the interaction evidence. |
| 6 | RECEIVE / EXTEND | Receive the canonical transcript and Meeting Intelligence Report. Request the optional behavioural/interaction/power-dynamics or longitudinal analysis only where useful. BASIL promotes genuine actions and follow-ups separately. |

If this document works as intended, there should be no reason to reconstruct diarisation from old chats again. The local quick-reference remains available for fault handling, but it is subordinate to this operator workflow.

## 2. The actual process in use today

The current workflow has already become a functioning interaction-evidence pipeline. The confusion comes from the fact that its stages have been operated through different interfaces and remembered as separate jobs.

| Stage | Layer | Current practice | System owner |
| --- | --- | --- | --- |
| 0 | Source recording | Phone recording, normally M4A. Uploaded to Google Drive. Original remains authoritative evidence. | MANUEL / evidence intake |
| 1 | Native transcription | Google Colab Whisper notebook produces timestamped transcript artefacts. JSON/TSV/SRT/VTT/TXT are retained unchanged. | MANUEL / transcription processor |
| 2 | Full diarisation | Local Python + pyannote Community-1 identifies anonymous speaker activity, regular/exclusive timelines, overlap and embeddings/QC where available. | MANUEL / speaker processor |
| 3 | BASIL lightweight + acoustic evidence | BASIL independently extracts acoustic, linguistic, timing and lightweight attribution evidence. This is a comparator/evidence layer, not automatic ground truth. | MANUEL / Interaction Evidence Ingest |
| 4 | Reconciliation | Transcript timing, full diarisation, BASIL evidence, voice similarity and context are aligned on one recording clock. Ambiguity remains visible. | MANUEL / merge-review layer |
| 5 | Human calibration | Zero to three high-value questions only where a short human answer materially improves attribution certainty. | MANUEL / evidence closure |
| 6 | Interaction evidence | Accepted machine evidence, provenance, corrections and processing state are consolidated into `<recording>--INTERACTION_DATA.sqlite`. | MANUEL / canonical evidence substrate |
| 7 | Canonical transcript | One presentation-ready human transcript: Turn \| Elapsed Time \| Wall-clock Time \| Speaker \| Transcript. Word and PDF versions are canonical human derivatives. | MANUEL → BRIAN handoff |
| 8 | Meeting Intelligence | Comprehensive reconstruction of what happened, what mattered, positions, decisions, commitments, risks, opportunities, quotations, follow-up and action evidence. | BRIAN / Meeting Intelligence |
| 9 | Optional deep intelligence | Behavioural, communication, interaction, power-dynamics, participant profiling or longitudinal analysis. Not automatically part of every meeting. | BRIAN / specialist analytical stack |
| 10 | BASIL action state + learning | Promote real commitments/follow-ups into BASIL task state and retain meeting-specific, participant/project and method learning with provenance. | BASIL operating / learning layer |

## 3. What is canonical and what is not

| Artefact | Status | Rule |
| --- | --- | --- |
| Original recording | CANONICAL SOURCE | Never replace it with a WAV or cleaned derivative. |
| Native Whisper/Colab JSON/TSV/SRT/VTT/TXT | CANONICAL MACHINE SOURCE | Preserve unchanged. Corrections are separate derivatives. |
| Raw Community-1 diarisation outputs | CANONICAL PROCESSOR EVIDENCE | Anonymous clusters are evidence, not identities. |
| BASIL lightweight attribution/acoustic layer | INDEPENDENT COMPARATOR / SUPPORTING EVIDENCE | Useful for calibration and anomaly discovery. Do not silently overwrite full diarisation. |
| `INTERACTION_DATA.sqlite` | CANONICAL CONSOLIDATED MACHINE EVIDENCE | The single structured evidence substrate used by downstream analysis. |
| Canonical master transcript DOCX/PDF | CANONICAL HUMAN TRANSCRIPT | Current reconciled attribution only. Internal method-comparison commentary stays out. |
| Meeting Intelligence Report | CANONICAL HUMAN INTELLIGENCE OUTPUT | Generated from finalised evidence. It is not the behavioural profile. |
| Behavioural / power / longitudinal reports | OPTIONAL ANALYTICAL DERIVATIVES | Run only when the decision value justifies them. |
| 16 kHz WAV, scratch extracts, debug files | WORKING DERIVATIVES | Reproducible. Retain only where recovery/evidence value justifies it. |

## 4. Why the current workflow feels harder than it actually is

| Friction | Root cause |
| --- | --- |
| Multiple interfaces | The same meeting moves through phone, Drive, Colab, Windows PowerShell/Python and ChatGPT. Each stage is individually workable but the user is acting as the orchestrator. |
| Transcription invocation is not frozen | The Colab notebook works in practice, but the canonical model, parameters, cell sequence, retry logic and output contract are still under-documented. |
| Diarisation has historical script residue | Older strict/repair scripts still exist in memory and folders. `diarise_meetings_v2.py` is the current operational engine, but the old process remains easy to rediscover accidentally. |
| Authentication/model confusion | Earlier pyannote operation depended on Hugging Face access and transient environment variables. The model assets are now available locally and should be treated as a persistent BASIL technical asset. |
| Evidence and analysis blur together | Acoustic analysis, lightweight attribution, full diarisation, Meeting Intelligence and behavioural profiling have sometimes been discussed as if they are one operation. They are different layers. |
| No single run manifest at the operator level | The system produces provenance internally, but the operator still has to remember which stages have run before telling BASIL what to do next. |
| Chat answers become accidental procedure | When the workflow is forgotten, another chat reconstructs it from fragments. Small differences in explanation then look like changes to the process. |

## 5. Frozen working folder structure

Use one meeting folder. Do not scatter transcription, diarisation and BASIL outputs across unrelated locations.

```text
<MEETING_NAME>__YYYY-MM-DD/
  00_SOURCE/
      original_audio_or_video.*
  01_TRANSCRIPTION_NATIVE/
      *.json  *.tsv  *.srt  *.vtt  *.txt
  02_DIARISATION/
      source_manifest.json
      run_status.json
      diarisation_regular.*
      diarisation_exclusive.*
      speaker_embeddings.npz
      diarisation_analysis.json
      artifact_manifest.json
  03_INTERACTION_EVIDENCE/
      <recording>--INTERACTION_DATA.sqlite
  04_REVIEW/
      ambiguity_queue.*
      speaker_mapping.*
      adjudication_record.*
  05_CANONICAL_TRANSCRIPT/
      <meeting>--MASTER_TRANSCRIPT.docx
      <meeting>--MASTER_TRANSCRIPT.pdf
  06_MEETING_INTELLIGENCE/
      <meeting>--MEETING_INTELLIGENCE_REPORT.docx
      [optional behavioural / longitudinal reports]
  07_BASIL_HANDOFF/
      action_extract / promoted actions / project-state updates
  99_ARCHIVE/
      superseded derivatives retained only for evidence or recovery
```

## 6. Immediate simplification: what should change now

Do not attempt a grand rebuild before reducing the recurring operator friction. The near-term design should remove memory-dependent steps first.

| Change | Operating rule |
| --- | --- |
| A. Treat this document as the current procedure | Stop reconstructing the workflow from old chats. Old chats and scripts are historical evidence unless explicitly promoted here. |
| B. Freeze `diarise_meetings_v2.py` as the current local runner | The V2 Community-1 runner already adds progress, QC, resumability, regular/exclusive outputs, embeddings where exposed and provenance. Older strict/repair scripts become fallback/legacy only. |
| C. Persist the pyannote model cache | The Community-1/segmentation/embedding assets should live in one known BASIL model-cache location. Routine runs should not depend on a new model download or rediscovery of authentication steps. |
| D. Make the local diarisation command deterministic | The user should provide only the recording/folder and known speaker count. A wrapper can locate the audio, create the 16 kHz derivative if needed, invoke V2, validate outputs and write status. |
| E. Freeze the Colab transcription contract | Capture the exact current notebook, Whisper model and parameter values as a controlled configuration. Until that is done, do not invent or silently change them. |
| F. Make BASIL folder-aware | The BASIL instruction should be folder-level, not file-by-file: inspect the folder, reuse valid evidence, process only what is missing, finalise and report exceptions. |
| G. Keep optional analysis optional | Canonical transcript + Meeting Intelligence are routine. Behavioural/power/longitudinal work is a downstream decision, not a mandatory burden on every meeting. |

## 7. Target user experience

| Maturity | User experience |
| --- | --- |
| CURRENT STABLE — FOUR INTERVENTIONS | 1. Upload to Drive. 2. Run the standard Colab transcription notebook. 3. Run one local V2 diarisation/meeting-prep command. 4. Tell BASIL to process the meeting folder. |
| NEXT — THREE INTERVENTIONS | 1. Upload recording. 2. Run one local meeting-prep launcher that handles transcription where available, diarisation, validation and writes a `READY_FOR_BASIL` manifest. 3. Tell BASIL to process the folder. |
| END STATE — ONE INTERVENTION | Drop the recording into the meeting folder. A local/cloud worker detects it, performs transcription and diarisation, writes the evidence bundle and BASIL completes evidence ingest, canonical transcript, Meeting Intelligence and action handoff. |

## 8. Recommended automation architecture

| Component | Where it runs | Function |
| --- | --- | --- |
| 1. Folder intake / manifest | Small local script or launcher | Ask for/select meeting folder and optional speaker count. Detect source recording and existing STT/diarisation outputs. Write one machine-readable run manifest. |
| 2. Transcription adapter | Existing Colab first; replace only if justified | Short term: keep the working Colab route. Medium term: either local faster-whisper/Whisper if hardware is adequate or a persistent cloud transcription worker. Do not automate around an undocumented notebook configuration. |
| 3. Diarisation worker | Local Windows Python | Use persistent Community-1 model assets. Avoid per-run token/model rediscovery. Use the current V2 runner or a simplified wrapper around the same evidence-preserving functions. |
| 4. Evidence validator | Local script + BASIL preflight | Confirm required native STT files, diarisation coverage, source hashes and speaker count assumptions before downstream analysis. |
| 5. BASIL evidence ingest | ChatGPT/BASIL | Read Drive folder, reuse evidence, perform acoustic/linguistic processing in checkpointed blocks, reconcile speakers and build/update SQLite. |
| 6. Human micro-loop | Chat | Ask zero to three attribution questions only where expected information value is high. |
| 7. Output generator | BASIL | Produce canonical transcript DOCX/PDF, Meeting Intelligence Report and action extract. Optional deep analysis remains separate. |
| 8. Learning / archive | BASIL + Drive | Retain validated participant/project learning and method improvements with provenance. Archive superseded outputs rather than silently overwriting sources. |

## 9. Processing profiles and speaker-processing limits

The recent pyannote test changes how BASIL should execute diarisation inside constrained ChatGPT compute. The pretrained models work, but long monolithic pipeline calls are inefficient. The method should therefore be adaptive and checkpointed.

| Profile | When | Speaker / evidence method | Default? |
| --- | --- | --- | --- |
| STANDARD | Routine meetings, usually known participants | Transcript-aligned speaker attribution using native STT timestamps, pretrained speaker embeddings and targeted pyannote segmentation around uncertain boundaries. Acoustic and linguistic evidence retained. | Default |
| ENHANCED | Unknown/multiple participants, more overlap, attribution-sensitive work | Checkpointed 8–10 minute speaker-processing blocks, regular/exclusive diarisation, systematic embeddings, global speaker reconciliation and targeted human calibration. | Select when speaker structure matters |
| FORENSIC | Legal/evidentially sensitive or unusually difficult recordings | Enhanced processing plus competing methods, denser acoustic evidence, targeted high-resolution reprocessing and intensive anomaly review. | Only when evidential value justifies cost |

For long meetings, processing duration is not a hard architectural limit. The work should be divided into checkpointed blocks and committed progressively to SQLite rather than depending on one long-lived tool invocation.

## 10. Routine output contract

| Class | Required content |
| --- | --- |
| Always preserve | Original recording; native STT bundle; raw diarisation evidence; processing provenance. |
| Always finalise | `INTERACTION_DATA.sqlite`; canonical master transcript DOCX + PDF; Meeting Intelligence Report. |
| Always surface | Run status; what was processed/reused; key results; exceptions/unresolved items; where the run sits in BASIL; immediate next step. |
| Only when useful | Behavioural profile; power-dynamics analysis; participant strategic profile; longitudinal memo; competing-method forensic bundle. |
| When multiple downloadable outputs are created in chat | Also provide one compact chat-specific ZIP containing the new outputs. |

## 11. Remaining decisions before v1.0

| Decision | What must be settled |
| --- | --- |
| Transcription configuration | Capture the exact current Colab notebook version, Whisper model and parameter values used for routine meetings. This is now the largest unresolved production detail. |
| Local wrapper | Create one Windows launcher/PowerShell script that finds the audio, uses the persistent model cache, runs V2 with the supplied speaker count, validates expected outputs and produces a `READY_FOR_BASIL` manifest. |
| Model-cache location | Choose one durable BASIL technical-assets folder and consolidate the pyannote model dependencies there. |
| Retention policy | Decide which raw processor bundles remain permanent after successful SQLite ingest. During calibration, keep them. Routine retention can later be reduced. |
| Speaker identity threshold | Freeze the evidence threshold for promoting an anonymous cluster to a named person. Retain mixed/unresolved states where the threshold is not met. |
| One-command transcription | Only after the current Colab configuration is captured should we decide whether to keep Colab, automate it or replace it with local/cloud transcription. |

## 12. Current diarisation quick command

The current operational engine is `diarise_meetings_v2.py` using `pyannote/speaker-diarization-community-1`. For a meeting with a known exact speaker count:

```bash
python diarise_meetings_v2.py "Meeting 02.m4a" --num-speakers 2
```

For an unknown speaker count, use a justified min/max range or automatic estimation. Do not hard-code a guessed exact count. The older `run_diarization_strict.py` and `repair_diarization_outputs.py` remain legacy/fallback references, not the routine path.

## 13. Authority and source basis

This version updates the 24 August 2026 Working Process Baseline v0.3 rather than creating a competing process. It incorporates the actual operator workflow described on 25 August 2026 and the pyannote runtime/model findings established during the Meeting 02 rerun discussion.
