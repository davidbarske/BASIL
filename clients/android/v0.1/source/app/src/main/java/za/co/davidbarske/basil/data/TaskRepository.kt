package za.co.davidbarske.basil.data

import za.co.davidbarske.basil.core.TaskRecord

interface TaskRepository {
    fun loadAll(): List<TaskRecord>
    fun readSnapshot(): LocalSnapshot
    fun replaceAll(tasks: List<TaskRecord>)
    fun upsert(task: TaskRecord)
    fun importJson(text: String)
    fun reconcileLocal(text: String)
    /** Client-local removal only; absence conveys no canonical deletion authority. */
    fun delete(taskId: String)
}
