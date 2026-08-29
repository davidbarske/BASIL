package za.co.davidbarske.basil.data

import android.content.Context
import za.co.davidbarske.basil.core.TaskRecord
import java.io.File
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.StandardCopyOption

class JsonTaskRepository(context: Context) : TaskRepository {
    private val dataFile = File(context.filesDir, "basil_tasks_v01.json")

    @Synchronized
    override fun loadAll(): List<TaskRecord> {
        if (!dataFile.exists()) return emptyList()
        return TaskJsonCodec.decode(dataFile.readText(Charsets.UTF_8))
    }

    @Synchronized
    override fun replaceAll(tasks: List<TaskRecord>) {
        writeAtomically(TaskJsonCodec.encode(tasks))
    }

    @Synchronized
    override fun upsert(task: TaskRecord) {
        val tasks = loadAll().toMutableList()
        val index = tasks.indexOfFirst { it.id == task.id }
        if (index >= 0) tasks[index] = task else tasks.add(task)
        writeAtomically(TaskJsonCodec.encode(tasks))
    }

    @Synchronized
    override fun delete(taskId: String) {
        val tasks = loadAll().filterNot { it.id == taskId }
        writeAtomically(TaskJsonCodec.encode(tasks))
    }

    private fun writeAtomically(text: String) {
        dataFile.parentFile?.mkdirs()
        val temp = File(dataFile.parentFile, "${dataFile.name}.tmp")
        temp.writeText(text, Charsets.UTF_8)

        try {
            Files.move(
                temp.toPath(),
                dataFile.toPath(),
                StandardCopyOption.REPLACE_EXISTING,
                StandardCopyOption.ATOMIC_MOVE
            )
        } catch (_: AtomicMoveNotSupportedException) {
            Files.move(temp.toPath(), dataFile.toPath(), StandardCopyOption.REPLACE_EXISTING)
        }
    }
}
