package za.co.davidbarske.basil.data

import org.json.JSONArray
import org.json.JSONObject
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.core.TaskState

object TaskJsonCodec {
    const val FORMAT = "BASIL_TASK_EXPORT"
    const val SCHEMA_VERSION = 1

    fun encode(tasks: List<TaskRecord>): String {
        val root = JSONObject()
            .put("format", FORMAT)
            .put("schemaVersion", SCHEMA_VERSION)
            .put("exportedAt", System.currentTimeMillis())

        val array = JSONArray()
        tasks.forEach { task ->
            array.put(
                JSONObject()
                    .put("id", task.id)
                    .put("description", task.description)
                    .put("state", task.state.name)
                    .put("project", task.project)
                    .put("nextAction", task.nextAction)
                    .put("deadline", task.deadline ?: JSONObject.NULL)
                    .put("notes", task.notes)
                    .put("createdAt", task.createdAt)
                    .put("updatedAt", task.updatedAt)
                    .put("completedAt", task.completedAt ?: JSONObject.NULL)
            )
        }

        root.put("tasks", array)
        return root.toString(2)
    }

    fun decode(text: String): List<TaskRecord> {
        val root = JSONObject(text)
        require(root.optString("format") == FORMAT) { "This is not a BASIL task export." }
        require(root.optInt("schemaVersion", -1) == SCHEMA_VERSION) {
            "Unsupported BASIL task schema version."
        }

        val array = root.getJSONArray("tasks")
        return buildList {
            for (index in 0 until array.length()) {
                val obj = array.getJSONObject(index)
                add(
                    TaskRecord(
                        id = obj.getString("id"),
                        description = obj.getString("description"),
                        state = TaskState.valueOf(obj.getString("state")),
                        project = obj.optString("project", ""),
                        nextAction = obj.optString("nextAction", ""),
                        deadline = obj.nullableString("deadline"),
                        notes = obj.optString("notes", ""),
                        createdAt = obj.getLong("createdAt"),
                        updatedAt = obj.getLong("updatedAt"),
                        completedAt = obj.nullableLong("completedAt")
                    )
                )
            }
        }
    }

    private fun JSONObject.nullableString(key: String): String? =
        if (!has(key) || isNull(key)) null else getString(key).takeIf { it.isNotBlank() }

    private fun JSONObject.nullableLong(key: String): Long? =
        if (!has(key) || isNull(key)) null else getLong(key)
}
