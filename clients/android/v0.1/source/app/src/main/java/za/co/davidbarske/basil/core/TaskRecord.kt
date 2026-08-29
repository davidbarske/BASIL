package za.co.davidbarske.basil.core

import java.util.UUID

enum class TaskState(val label: String) {
    ACTIVE("Active"),
    WAITING("Waiting"),
    SCHEDULED("Scheduled"),
    BLOCKED("Blocked"),
    MONITOR("Monitor"),
    DONE("Done")
}

data class TaskRecord(
    val id: String,
    val description: String,
    val state: TaskState,
    val project: String,
    val nextAction: String,
    val deadline: String?,
    val notes: String,
    val createdAt: Long,
    val updatedAt: Long,
    val completedAt: Long?
) {
    init {
        require(id.isNotBlank()) { "Task id cannot be blank." }
        require(description.isNotBlank()) { "Task description cannot be blank." }
    }

    fun withCompletion(done: Boolean, now: Long = System.currentTimeMillis()): TaskRecord =
        if (done) {
            copy(state = TaskState.DONE, completedAt = completedAt ?: now, updatedAt = now)
        } else {
            copy(state = TaskState.ACTIVE, completedAt = null, updatedAt = now)
        }

    companion object {
        fun create(
            description: String,
            state: TaskState = TaskState.ACTIVE,
            project: String = "",
            nextAction: String = "",
            deadline: String? = null,
            notes: String = "",
            now: Long = System.currentTimeMillis()
        ): TaskRecord {
            val cleanDescription = description.trim()
            require(cleanDescription.isNotBlank()) { "Task description cannot be blank." }

            return TaskRecord(
                id = UUID.randomUUID().toString(),
                description = cleanDescription,
                state = state,
                project = project.trim(),
                nextAction = nextAction.trim(),
                deadline = deadline?.trim()?.takeIf { it.isNotBlank() },
                notes = notes.trim(),
                createdAt = now,
                updatedAt = now,
                completedAt = if (state == TaskState.DONE) now else null
            )
        }
    }
}
