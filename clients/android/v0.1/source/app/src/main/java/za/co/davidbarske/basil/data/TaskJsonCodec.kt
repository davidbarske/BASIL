package za.co.davidbarske.basil.data

import org.json.JSONArray
import org.json.JSONObject
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.core.TaskState

class LegacyReconciliationRequired(val taskIds: List<String>, val originalPayload: String) :
    IllegalArgumentException("Legacy DONE tasks lack completion evidence; original payload retained: " + taskIds.joinToString())

object TaskJsonCodec {
    const val FORMAT = "BASIL_SYBIL_TASKS"
    const val SCHEMA_VERSION = 1
    private val fields = setOf("task_id", "title", "state", "importance", "urgency",
        "owner", "deadline", "dependency_ids", "source_refs", "completion_evidence")
    private val clientFields = setOf("project", "nextAction", "notes", "createdAt", "updatedAt", "completedAt")

    fun encode(tasks: List<TaskRecord>): String {
        require(tasks.map { it.id }.distinct().size == tasks.size) { "Duplicate task IDs." }
        val array = JSONArray()
        val metadata = JSONObject()
        tasks.forEach { original ->
            val task = original.copy()
            array.put(JSONObject().put("task_id", task.id).put("title", task.description)
                .put("state", task.state.name).putNullable("importance", task.importance)
                .putNullable("urgency", task.urgency).putNullable("owner", task.owner)
                .putNullable("deadline", task.deadline)
                .put("dependency_ids", JSONArray(task.dependencyIds))
                .put("source_refs", JSONArray(task.sourceRefs))
                .put("completion_evidence", JSONArray(task.completionEvidence)))
            if (task.hasClientMetadata ||
                listOf(task.project, task.nextAction, task.notes).any { it.isNotEmpty() } ||
                listOf(task.createdAt, task.updatedAt, task.completedAt).any { it != null }) {
                metadata.put(task.id, JSONObject().put("project", task.project)
                    .put("nextAction", task.nextAction).put("notes", task.notes)
                    .putNullable("createdAt", task.createdAt).putNullable("updatedAt", task.updatedAt)
                    .putNullable("completedAt", task.completedAt))
            }
        }
        val root = JSONObject().put("format", FORMAT).put("schema_version", SCHEMA_VERSION).put("tasks", array)
        if (metadata.length() > 0) root.put("android_v01", metadata)
        return root.toString(2)
    }

    fun decode(text: String): List<TaskRecord> {
        val root = JSONObject(text)
        val legacy = root.text("format") == "BASIL_TASK_EXPORT"
        if (legacy) {
            root.keysOnly(setOf("format", "schemaVersion", "exportedAt", "tasks"))
            require(root.integer("schemaVersion") == 1L) { "Unsupported legacy version." }
        } else {
            root.keysOnly(setOf("format", "schema_version", "tasks", "android_v01"))
            require(root.text("format") == FORMAT && root.integer("schema_version") == 1L) {
                "Unsupported SYBIL format/version."
            }
        }
        val array = root.getJSONArray("tasks")
        if (legacy) {
            val incomplete = (0 until array.length()).map { array.getJSONObject(it) }.filter {
                it.text("state") == "DONE" && (!it.has("completionEvidence") || it.strings("completionEvidence").isEmpty())
            }.map { it.text("id") }
            if (incomplete.isNotEmpty()) throw LegacyReconciliationRequired(incomplete, text)
        }
        val metadata = if (!legacy && root.has("android_v01")) root.getJSONObject("android_v01") else JSONObject()
        val tasks = (0 until array.length()).map {
            val obj = array.getJSONObject(it)
            if (legacy) migrate(obj) else canonical(obj, metadata)
        }
        require(tasks.map { it.id }.distinct().size == tasks.size) { "Duplicate task IDs." }
        require(metadata.keys().asSequence().all { id -> tasks.any { it.id == id } }) {
            "Client metadata refers to missing task."
        }
        return tasks
    }

    private fun canonical(obj: JSONObject, metadata: JSONObject): TaskRecord {
        obj.keysOnly(fields)
        require(fields.all { obj.has(it) }) { "Missing canonical task fields." }
        val id = obj.text("task_id")
        val client = if (metadata.has(id)) metadata.getJSONObject(id) else null
        client?.keysOnly(clientFields)
        require(client == null || clientFields.all { client.has(it) }) { "Missing client metadata fields." }
        return TaskRecord(
            id = id, description = obj.text("title"), state = TaskState.valueOf(obj.text("state")),
            importance = obj.score("importance"), urgency = obj.score("urgency"),
            owner = obj.nullableText("owner"), deadline = obj.nullableText("deadline"),
            dependencyIds = obj.strings("dependency_ids"), sourceRefs = obj.strings("source_refs"),
            completionEvidence = obj.strings("completion_evidence"),
            project = client?.text("project") ?: "", nextAction = client?.text("nextAction") ?: "",
            notes = client?.text("notes") ?: "", createdAt = client?.nullableInteger("createdAt"),
            updatedAt = client?.nullableInteger("updatedAt"), completedAt = client?.nullableInteger("completedAt"),
            hasClientMetadata = client != null
        )
    }

    private fun migrate(obj: JSONObject): TaskRecord {
        obj.keysOnly(clientFields + setOf("id", "description", "state", "deadline", "completionEvidence"))
        return TaskRecord(
            id = obj.text("id"), description = obj.text("description"), state = TaskState.valueOf(obj.text("state")),
            deadline = obj.nullableText("deadline")?.takeIf { it.isNotBlank() },
            completionEvidence = if (obj.has("completionEvidence")) obj.strings("completionEvidence") else emptyList(),
            project = obj.optionalText("project"), nextAction = obj.optionalText("nextAction"),
            notes = obj.optionalText("notes"), createdAt = obj.nullableInteger("createdAt"),
            updatedAt = obj.nullableInteger("updatedAt"), completedAt = obj.nullableInteger("completedAt"),
            hasClientMetadata = true
        )
    }

    private fun JSONObject.putNullable(key: String, value: Any?) = put(key, value ?: JSONObject.NULL)
    private fun JSONObject.keysOnly(allowed: Set<String>) {
        require(keys().asSequence().all { it in allowed }) { "Unknown fields; original data must be retained." }
    }
    private fun JSONObject.text(key: String): String {
        val value = get(key)
        require(value is String) { "$key must be text." }
        return value
    }
    private fun JSONObject.optionalText(key: String) = if (has(key)) text(key) else ""
    private fun JSONObject.nullableText(key: String) = if (!has(key) || isNull(key)) null else text(key)
    private fun JSONObject.integer(key: String): Long {
        val value = get(key)
        require(value is Int || value is Long) { "$key must be an integer." }
        return (value as Number).toLong()
    }
    private fun JSONObject.nullableInteger(key: String) = if (!has(key) || isNull(key)) null else integer(key)
    private fun JSONObject.score(key: String): Int? {
        val value = nullableInteger(key) ?: return null
        require(value in 1..10) { "$key must be 1..10 or unknown." }
        return value.toInt()
    }
    private fun JSONObject.strings(key: String): List<String> {
        val array = getJSONArray(key)
        return (0 until array.length()).map {
            val value = array.get(it)
            require(value is String) { "$key must contain text references." }
            value
        }
    }
}
