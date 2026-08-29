package za.co.davidbarske.basil.data

import za.co.davidbarske.basil.core.TaskRecord

interface TaskRepository {
    fun loadAll(): List<TaskRecord>
    fun replaceAll(tasks: List<TaskRecord>)
    fun upsert(task: TaskRecord)
    fun delete(taskId: String)
}
