package za.co.davidbarske.basil.data

import java.util.Collections
import org.json.JSONArray
import org.json.JSONObject
import za.co.davidbarske.basil.core.TaskRecord

/** Source recovery is outside canonical TaskRecord/state. Bytes are preserved exactly. */
class LocalSourceProblem(
    original: ByteArray, taskIds: List<String>, val legacyReconciliation: Boolean, val message: String
) {
    private val source = original.copyOf()
    val taskIds: List<String> = Collections.unmodifiableList(ArrayList(taskIds))
    fun exportBytes(): ByteArray = source.copyOf()
}

data class LocalSnapshot(val tasks: List<TaskRecord>, val sourceProblem: LocalSourceProblem? = null)

class CanonicalImportConflict(
    local: List<TaskRecord>, incoming: List<TaskRecord>, val originalPayload: String
) : IllegalArgumentException("Canonical import conflicts require reconciliation: " + incoming.joinToString { it.id }) {
    val localTasks: List<TaskRecord> = Collections.unmodifiableList(ArrayList(local))
    val incomingTasks: List<TaskRecord> = Collections.unmodifiableList(ArrayList(incoming))
    val taskIds: List<String> = Collections.unmodifiableList(incomingTasks.map { it.id })
}

/** Small local application policies, not a synchronization protocol. */
object LocalRegister {
    fun inspect(bytes: ByteArray): LocalSnapshot {
        try {
            val text = bytes.decodeToString(throwOnInvalidSequence = true)
            try {
                return LocalSnapshot(TaskJsonCodec.decode(text))
            } catch (error: LegacyReconciliationRequired) {
                val root = JSONObject(text)
                val all = root.getJSONArray("tasks")
                val ids = (0 until all.length()).map {
                    val id = all.getJSONObject(it).get("id")
                    require(id is String && id.isNotBlank()) { "Invalid legacy task ID." }
                    id
                }
                require(ids.distinct().size == ids.size) { "Duplicate legacy task IDs." }
                val visible = JSONArray()
                (0 until all.length()).forEach {
                    if (ids[it] !in error.taskIds) visible.put(all.getJSONObject(it))
                }
                // Only the strictly decoded subset is exposed as operational task state.
                root.put("tasks", visible)
                val tasks = TaskJsonCodec.decode(root.toString())
                return LocalSnapshot(tasks, LocalSourceProblem(bytes, error.taskIds, true,
                    "Historical source requires reconciliation: " + error.taskIds.joinToString() +
                        ". Showing validated tasks read-only; export the original or recover with an evidence-backed file."))
            }
        } catch (error: Exception) {
            // Malformed/unrelated source stays recoverable, but is never canonicalized.
            return LocalSnapshot(emptyList(), LocalSourceProblem(bytes, emptyList(), false,
                "Local source is invalid: " + (error.message ?: "Unable to decode") +
                    ". Original data is available for export; writes are blocked."))
        }
    }

    fun merge(existing: List<TaskRecord>, imported: List<TaskRecord>, originalPayload: String): List<TaskRecord> {
        TaskJsonCodec.encode(existing) // Validate IDs and records at this public boundary.
        TaskJsonCodec.encode(imported)
        val local = existing.associateBy { it.id }
        val conflicts = imported.filter { candidate ->
            local[candidate.id]?.let { !it.sameCanonicalContent(candidate) } ?: false
        }
        if (conflicts.isNotEmpty()) {
            throw CanonicalImportConflict(conflicts.map { local.getValue(it.id) }, conflicts, originalPayload)
        }
        // Identical canonical IDs retain local client metadata, regardless of timestamp.
        return existing + imported.filter { it.id !in local }
    }

    fun reconcileLegacy(original: String, supplied: List<TaskRecord>): List<TaskRecord> {
        val problem = try {
            TaskJsonCodec.decode(original)
            throw IllegalArgumentException("No historical completion reconciliation is required.")
        } catch (error: LegacyReconciliationRequired) {
            error
        }
        TaskJsonCodec.encode(supplied)
        val byId = supplied.associateBy { it.id }
        val root = JSONObject(original)
        val tasks = root.getJSONArray("tasks")
        val ids = (0 until tasks.length()).map { tasks.getJSONObject(it).getString("id") }
        require(ids.distinct().size == ids.size && byId.keys == ids.toSet()) {
            "Recovery must retain every original task ID exactly once."
        }
        (0 until tasks.length()).forEach {
            val old = tasks.getJSONObject(it)
            if (old.getString("id") in problem.taskIds) {
                old.put("completionEvidence", JSONArray(byId.getValue(old.getString("id")).completionEvidence))
            }
        }
        // Inject only explicitly supplied references, then perform full canonical validation.
        val expected = TaskJsonCodec.decode(root.toString())
        require(expected.all { it.sameCanonicalContent(byId.getValue(it.id)) }) {
            "Recovery may supply completion evidence; other original canonical facts must remain unchanged."
        }
        // Preserve original client metadata even if the recovery file omitted it.
        return expected
    }
}
